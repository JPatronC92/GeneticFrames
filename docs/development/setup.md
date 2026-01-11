# Development Setup Guide

Welcome to the **GeneticFrames Zoo** development team! This guide will get you up and running in minutes using Docker.

## Prerequisites

*   [Docker](https://docs.docker.com/get-docker/) & Docker Compose
*   [Git](https://git-scm.com/)

## Quick Start (The "5-Minute" Method)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/GeneticFrames.git
    cd GeneticFrames
    ```

2.  **Environment Setup:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    *Note: The default settings work out-of-the-box for local development.*

3.  **Launch the Zoo:**
    We use a Makefile to simplify commands.
    ```bash
    make dev
    ```
    This will:
    *   Build the Docker images for Backend (FastAPI) and Frontend (Vite/React).
    *   Start a Redis container.
    *   Launch the services with hot-reloading enabled.

4.  **Verify:**
    Open your browser to:
    *   **Frontend:** [http://localhost:5173](http://localhost:5173)
    *   **Backend Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

## Project Structure

*   `geneticframes-api/`: Python FastAPI backend.
*   `geneticframes-web/`: React/TypeScript frontend.
*   `docs/`: Project documentation.

## Common Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start the development environment (Docker) |
| `make test` | Run backend unit tests |
| `make zoo-status` | Check the health of the Zoo (API & Connectivity) |
| `make clean` | Remove build artifacts and temporary files |

## Troubleshooting

*   **Ports already in use?**
    Check if you have other services running on 8000 or 5173. You can change the ports in `.env`.
*   **NCBI Connection Issues?**
    Ensure you have an internet connection. By default, the app runs in "Simulation Mode" to save API calls. To enable real data, set `NCBI_LIVE_MODE=True` in your `.env`.
