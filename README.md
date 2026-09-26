# Personal AI Action Agent

A full-stack, AI-powered automation platform that connects to your tools (GitHub, LinkedIn, Gmail, Calendar, etc.) and executes actions on your behalf using natural language commands. 

Powered by **Google Gemini 2.0 Flash**.

## 🌟 Core Features

- **Multi-Platform Integration**: Supports OAuth connections to external platforms (currently configured for GitHub).
- **Conversational UI**: A sleek, premium dark-themed interface built with Next.js to chat with your agent.
- **Smart Tool Execution**: The AI translates natural language ("Create an issue about dark mode in repo X") into precise API calls.
- **Security-First Confirmations**: Sensitive actions (like creating Pull Requests) are flagged by the backend and intercepted by the UI, presenting a "Confirmation Card" that requires explicit user approval before execution.
- **Activity Log**: Complete audit trail of every API action performed by the agent.

---

## 🏗️ Architecture & Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with async SQLAlchemy and Alembic (for migrations, if added).
- **AI Engine**: Google GenAI SDK (`google-generativeai`) integrated with native Function Calling.
- **Auth**: JWT (JSON Web Tokens) with `passlib` for password hashing.
- **API Client**: `httpx` for fast, asynchronous HTTP requests to external APIs (GitHub).

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Styling**: Pure CSS Modules with a bespoke premium dark theme (glassmorphism, CSS micro-animations).
- **State**: React Context API for global auth state.
- **HTTP**: Centralized `ApiService` for token rotation and error handling.

---

## 📂 Project Structure

```text
Future_man_works/
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── main.py                  # FastAPI entry point & Tool Registration
│       ├── config.py                # Environment variables (Pydantic Settings)
│       ├── database/
│       │   ├── database.py          # PostgreSQL Engine
│       │   └── models.py            # User, PlatformConnection, Conversation, Message, Task, ToolExecution
│       ├── auth/
│       │   └── security.py          # JWT logic
│       ├── api/
│       │   ├── auth.py              # Register, Login, Me
│       │   ├── chat.py              # Agent interaction
│       │   ├── connections.py       # OAuth flows (GitHub)
│       │   └── tasks.py             # Activity log & Confirmations
│       ├── agent/
│       │   ├── agent.py             # Gemini integration & Function parsing
│       │   ├── executor.py          # Validation & DB logging for tools
│       │   └── permissions.py       # OAuth scope checking
│       └── tools/
│           ├── base.py              # BaseTool interface & RiskLevels
│           ├── registry.py          # Tool registry
│           └── github/              # 8 Implemented GitHub Actions
│               ├── client.py
│               ├── schemas.py
│               └── tools.py
│
└── frontend/
    ├── .env.local
    ├── package.json
    └── src/
        ├── services/
        │   └── api.js               # Centralized HTTP client
        ├── context/
        │   └── AuthContext.js       # Auth Provider
        └── app/
            ├── globals.css          # Design System
            ├── layout.js            
            ├── page.js              # Auth Redirector
            ├── login/               
            ├── register/            
            ├── dashboard/           # Connect Platforms & Quick Actions
            ├── chat/                # Agent UI & Confirmation Cards
            └── tasks/               # Activity History
```

---

## ⚙️ Setup & Installation

### 1. Database Setup
Ensure PostgreSQL is installed and running. Create a database for the project:
```sql
CREATE DATABASE personal_ai_agent;
```

### 2. Backend Environment Variables
Duplicate `backend/.env.example` to `backend/.env` and fill in:
```env
DATABASE_URL="postgresql+asyncpg://postgres:yourpassword@localhost:5432/personal_ai_agent"
SECRET_KEY="your-random-jwt-secret-key"

GEMINI_API_KEY="your-google-gemini-key"

GITHUB_CLIENT_ID="your-github-oauth-client-id"
GITHUB_CLIENT_SECRET="your-github-oauth-client-secret"
GITHUB_REDIRECT_URI="http://localhost:3000/connections/github/callback"
```
*(To get GitHub credentials, create a new OAuth App in your GitHub Developer Settings).*

### 3. Run Backend
Open a terminal in the `backend/` folder:
```bash
python -m venv .venv
.\.venv\Scripts\activate       # Windows
# source .venv/bin/activate    # Mac/Linux

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
*(On first startup, SQLAlchemy will automatically create all tables).*

### 4. Run Frontend
Open a new terminal in the `frontend/` folder. Ensure `.env.local` contains `NEXT_PUBLIC_API_URL=http://localhost:8000`.
```bash
npm install
npm run dev
```

### 5. Start Using!
1. Go to `http://localhost:3000`
2. Create an account.
3. Click "Connect" on the GitHub tile in the dashboard.
4. Authorize the app on GitHub.
5. Go to the Chat tab and try commands like:
   - *"Show my repositories"*
   - *"List issues in [owner]/[repo]"*
   - *"Create an issue in [owner]/[repo] about dark mode"*
