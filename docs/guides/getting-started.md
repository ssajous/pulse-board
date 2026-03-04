# Getting Started with Pulse Board

This tutorial walks you through setting up and running Pulse Board on your local machine. By the end, you will have the full application running -- backend, frontend, and database -- and you will have created a topic, voted on it, and seen real-time updates across browser tabs.

**Time to complete**: approximately 10 minutes.

## What You Will Build

Pulse Board is a real-time community engagement platform. Community members submit topics anonymously, vote them up or down, and watch scores update live across every connected browser. Topics that accumulate too many downvotes are automatically censured and removed from the board. Hosts can also run interactive polls during sessions, collecting responses in real-time and projecting results in a dedicated present mode.

In this tutorial, you will:

1. Install prerequisites and clone the repository
2. Start the entire stack with a single command
3. Verify the backend, frontend, and database are running
4. Create a topic, cast votes, and observe real-time updates
5. Create an event, join it from a second tab, run a poll, and use present mode

## Prerequisites

Install the following tools before you begin. If you already have them, confirm the required versions.

| Tool | Minimum Version | Install Guide |
|------|-----------------|---------------|
| **Python** | 3.13+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js** | 22 LTS | Install via [nvm](https://github.com/nvm-sh/nvm), then `nvm install 22` |
| **uv** | Latest | [docs.astral.sh/uv/getting-started/installation](https://docs.astral.sh/uv/getting-started/installation/) |
| **Docker** | Latest | [docs.docker.com/get-started/get-docker](https://docs.docker.com/get-started/get-docker/) |

Verify each tool is available:

```bash
python3 --version    # Should print Python 3.13.x or higher
node --version       # Should print v22.x.x
uv --version         # Should print uv 0.x.x
docker --version     # Should print Docker 2x.x.x or higher
```

## Step 1: Clone and Configure

Clone the repository and create your local environment file:

```bash
git clone <repo-url>
cd pulse-board
cp .env.example .env
```

The `.env` file contains sensible defaults for local development. You do not need to edit it to get started.

## Step 2: Install Dependencies

Install both Python and Node.js dependencies:

```bash
uv sync
cd frontend && nvm use 22 && npm install && cd ..
```

`uv sync` reads `pyproject.toml` and installs all Python dependencies into a local virtual environment. `npm install` pulls the frontend dependencies defined in `frontend/package.json`.

## Step 3: Start the Application

Run a single command to start everything:

```bash
make dev
```

This command performs three actions in sequence:

1. **Starts PostgreSQL** in a Docker container (`make infra-up`)
2. **Starts the backend** with hot reload on `http://localhost:8000`
3. **Starts the frontend** with hot module replacement on `http://localhost:5173`

Wait until you see output from both the backend (Uvicorn) and frontend (Vite) confirming they are ready.

## Step 4: Verify the Setup

Run each of these checks to confirm the stack is healthy.

**Check the frontend**: Open [http://localhost:5173](http://localhost:5173) in your browser. You should see the Pulse Board interface.

**Check the backend health endpoint**: Open a new terminal and run:

```bash
curl http://localhost:8000/health
```

You should see a JSON response indicating the service and database are healthy:

```json
{"status": "healthy", "database": "connected"}
```

**Browse the API documentation**: Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser. The interactive Swagger UI lists all available API endpoints with request and response schemas.

## Step 5: Try It Out

Now that the application is running, exercise its core features.

### Create a Topic

1. Open [http://localhost:5173](http://localhost:5173) in your browser.
2. Type a topic in the submission form (for example: "Should we adopt weekly retrospectives?").
3. Submit it. The topic appears on the board immediately.

### Vote on the Topic

1. Click the upvote button on the topic you just created. The score increments to 1.
2. Click the upvote button again. The vote toggles off and the score returns to 0.
3. Click the downvote button. The score decrements to -1.

### See Real-Time Updates

1. Open a second browser tab (or a different browser) to [http://localhost:5173](http://localhost:5173).
2. In the first tab, create a new topic or change a vote.
3. Watch the second tab -- the score and any new topics update instantly without a page refresh.

This live synchronization is powered by WebSocket connections between every connected browser and the backend.

### Create an Event

1. Open [http://localhost:5173](http://localhost:5173) in your browser.
2. Click "Create Event" and fill in a title and description for your session.
3. Submit the form. A confirmation page appears displaying a join code.
4. Copy the join code -- you will share it with participants so they can join the event.

### Join an Event

1. Open a second browser tab to [http://localhost:5173](http://localhost:5173).
2. Click "Join Event" and enter the join code from the previous step.
3. You are now on the event board. From this tab you can submit topics and cast votes, just as in the basic workflow above.

Participants on separate devices follow the same join flow -- give them the join code and they are immediately connected to the live session.

### Create and Run a Poll

1. In the host tab, click the admin link to open the host dashboard for your event.
2. Click "Create Poll" and choose a poll type:
   - **Multiple choice** -- participants select one or more predefined options
   - **Rating** -- participants submit a numeric rating
   - **Open text** -- participants type a free-form response
   - **Word cloud** -- participants submit words that are aggregated into a visual word cloud
3. Fill in the poll question and any required options, then save.
4. Click "Activate" to make the poll visible to participants.
5. In the participant tabs, the active poll appears and participants can submit their responses.
6. Watch the results panel in the host dashboard -- responses appear in real-time as participants submit them.

To stop accepting responses, deactivate the poll from the host dashboard. You can create and activate multiple polls during a single event session.

### Use Present Mode

1. From the event admin page, click "Present" to open the present mode view in a new tab.
2. The present mode view displays:
   - A QR code that participants can scan to join the event directly
   - Live poll results for any currently active poll
   - A scrolling feed of submitted topics
3. This view is optimized for projection on a large screen during a meeting or live event. It updates automatically as polls are activated and topics are submitted.

## Stopping the Application

Press `Ctrl+C` in the terminal where `make dev` is running. This stops the backend, frontend, and the PostgreSQL container.

To stop only the infrastructure (PostgreSQL) without stopping the application servers:

```bash
make infra-down
```

To remove all build artifacts, caches, Docker volumes, and installed dependencies:

```bash
make clean
```

## Next Steps

- **[Development Setup Guide](development-setup.md)** -- Set up a full development environment with individual service control, testing, linting, and code quality tools.
- **[Deployment Guide](deployment.md)** -- Build and deploy Pulse Board with Docker for production use.
- **[API Documentation](http://localhost:8000/docs)** -- Explore the full API via the interactive Swagger UI (requires a running backend).
- **[Architecture Decision Records](../architecture/decisions/)** -- Understand the design decisions behind the technology stack and architecture.
