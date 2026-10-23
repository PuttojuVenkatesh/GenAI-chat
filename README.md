# Gen AI Chat

A small Python and React chat application using the Groq chat-completions API.
The Python service detects a basic intent, includes recent conversation history,
and returns Markdown-formatted assistant responses. The React interface renders
assistant Markdown with `react-markdown`.

## Requirements

- Python 3.10 or newer
- Node.js and npm
- A Groq API key

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

Open two terminals in the project folder.

Terminal 1 — start the Python API:

```powershell
.\venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Terminal 2 — start the React development server:

```powershell
Set-Location .\frontend
npm run dev
```

Open the local URL printed by Vite (usually `http://localhost:5173`).

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
