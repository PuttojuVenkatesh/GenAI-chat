import os
import unittest
from copy import deepcopy
from unittest.mock import patch
from uuid import UUID

import httpx
from fastapi.testclient import TestClient
from groq import APIError

import api


class InMemoryCollection:
    def __init__(self) -> None:
        self.documents: dict[str, dict] = {}

    def insert_one(self, document: dict) -> None:
        self.documents[document["_id"]] = deepcopy(document)

    def find_one(self, query: dict) -> dict | None:
        document = self.documents.get(query["_id"])
        return deepcopy(document) if document is not None else None

    def find(self, query: dict, projection: dict) -> list[dict]:
        documents = [
            deepcopy(document)
            for document in self.documents.values()
            if document["messages"]
        ]
        for document in documents:
            if projection.get("messages") == 0:
                document.pop("messages", None)
        return documents

    def update_one(self, query: dict, update: dict) -> None:
        document = self.documents[query["_id"]]
        document["messages"].extend(deepcopy(update["$push"]["messages"]["$each"]))
        document.update(update["$set"])


class ChatSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.collection = InMemoryCollection()
        self.chats = patch.object(api, "chats", self.collection)
        self.chats.start()
        self.addCleanup(self.chats.stop)
        self.client = TestClient(api.app)
        self.api_key = patch.dict(os.environ, {"GROQ_API_KEY": "test-key"})
        self.api_key.start()
        self.addCleanup(self.api_key.stop)

    def create_session(self) -> str:
        response = self.client.post("/sessions")
        self.assertEqual(response.status_code, 200)
        session_id = response.json()["session_id"]
        UUID(session_id)
        return session_id

    def test_follow_up_receives_stored_session_history(self) -> None:
        observed_history: list[list[dict[str, str]]] = []

        def respond(client, message, intent, history):
            observed_history.append(history)
            return f"Reply to: {message}"

        session_id = self.create_session()
        with patch("api.generate_response", side_effect=respond):
            first = self.client.post(
                "/chat",
                json={"session_id": session_id, "message": "Hello"},
            )
            second = self.client.post(
                "/chat",
                json={
                    "session_id": session_id,
                    "message": "Can you explain that?",
                },
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            observed_history,
            [
                [],
                [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Reply to: Hello"},
                ],
            ],
        )
        self.assertEqual(second.json()["session_id"], session_id)

    def test_chat_history_can_be_listed_and_reopened(self) -> None:
        session_id = self.create_session()
        with patch("api.generate_response", return_value="A saved reply"):
            response = self.client.post(
                "/chat",
                json={"session_id": session_id, "message": "Remember this chat"},
            )

        self.assertEqual(response.status_code, 200)
        sessions = self.client.get("/sessions")
        self.assertEqual(sessions.status_code, 200)
        self.assertEqual(sessions.json()[0]["session_id"], session_id)
        self.assertEqual(sessions.json()[0]["title"], "Remember this chat")

        reopened = self.client.get(f"/sessions/{session_id}")
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(
            reopened.json()["messages"],
            [
                {"role": "user", "content": "Remember this chat"},
                {"role": "assistant", "content": "A saved reply"},
            ],
        )

    def test_sessions_do_not_share_history(self) -> None:
        first_session = self.create_session()
        second_session = self.create_session()
        observed_history: list[list[dict[str, str]]] = []

        def respond(client, message, intent, history):
            observed_history.append(history)
            return "Reply"

        with patch("api.generate_response", side_effect=respond):
            self.client.post(
                "/chat",
                json={"session_id": first_session, "message": "First chat"},
            )
            response = self.client.post(
                "/chat",
                json={"session_id": second_session, "message": "Separate chat"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(observed_history, [[], []])

    def test_unknown_session_returns_not_found(self) -> None:
        response = self.client.post(
            "/chat",
            json={
                "session_id": "00000000-0000-0000-0000-000000000001",
                "message": "Hi",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("session not found", response.json()["detail"])

    def test_missing_api_key_returns_server_error(self) -> None:
        session_id = self.create_session()
        with patch.dict(os.environ):
            os.environ.pop("GROQ_API_KEY", None)
            response = self.client.post(
                "/chat",
                json={"session_id": session_id, "message": "Hi"},
            )

        self.assertEqual(response.status_code, 500)
        self.assertIn("GROQ_API_KEY", response.json()["detail"])

    def test_groq_error_returns_bad_gateway_without_storing_failed_turn(self) -> None:
        session_id = self.create_session()
        error = APIError(
            "Upstream failed",
            request=httpx.Request("POST", "https://api.groq.com"),
            body=None,
        )
        with patch("api.generate_response", side_effect=error):
            response = self.client.post(
                "/chat",
                json={"session_id": session_id, "message": "Hi"},
            )

        self.assertEqual(response.status_code, 502)
        self.assertIn("Groq API request failed", response.json()["detail"])
        self.assertEqual(
            self.collection.find_one({"_id": session_id})["messages"],
            [],
        )


if __name__ == "__main__":
    unittest.main()
