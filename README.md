# Gen AI Chat

A small Python and React chat application using the Groq chat-completions API.
The Python service assigns each chat a UUID, stores successful turns in
process-memory, detects a basic intent, and sends recent session history to
Groq. The React interface renders assistant Markdown with `react-markdown` and
starts a separate session for each new chat.

## Requirements

- Python 3.10 or newer
- Node.js and npm
- A Groq API key
- Git (optional, for syncing with GitHub)

## Setup

From the project folder, create and activate a Python virtual environment and
install the Python dependencies:

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and replace the placeholder with your Groq API key:

```text
GROQ_API_KEY=your_actual_key
```

Install the frontend dependencies:

```powershell
Set-Location .\frontend
npm install
```

## Run the web chat

The Python backend and React frontend must both be running. If only the
frontend is running, the app cannot create a chat session and the Send button
stays disabled. The Vite development server forwards `/api` requests to the
backend, so it works whether Vite chooses port 5173 or another available port.

Open two terminals in VS Code.

Terminal 1 — from the project folder, start the Python API:

```powershell
.\venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Leave Terminal 1 running. In Terminal 2, start the React development server:

```powershell
Set-Location .\frontend
npm run dev
```

Open the local URL printed by Vite (usually `http://localhost:5173`). Wait for
the header to show **Ready** before sending a message. If it shows **Offline**,
confirm Terminal 1 is running and select **Retry**.
Use **New Chat** to start a separate conversation. Each new session has its own
message history.

The in-memory session store is cleared whenever the Python API process stops or
restarts. It is intended for development and does not persist chats to disk.

## Run backend tests

From the project folder:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Run the terminal examples

From the project folder:

```powershell
.\venv\Scripts\python.exe .\task1.py
.\venv\Scripts\python.exe .\task4.py
```

Type `quit` to exit the interactive chat in `task4.py`.

## Notes

- `task4.py` contains a small keyword-based intent detector that can be replaced
  with the project's intended classifier when available.
- The API key stays in `.env`; `.gitignore` excludes `.env`, the virtual
  environment, installed frontend packages, and frontend build output.
