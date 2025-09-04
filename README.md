# Kopi Challenge – Rickbot (Debate Bot API)

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-brightgreen)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Render](https://img.shields.io/badge/deployed%20on-Render-purple)](https://rickbot-k4ad.onrender.com/)

---

## 🌐 Demo

* **Live on Render:** [https://rickbot-k4ad.onrender.com/](https://rickbot-k4ad.onrender.com/)
* Includes a **minimal static frontend** in `/` (`static/index.html`) to test the API without Postman or cURL.

---

## 📖 About The Project

This project implements a **debate chatbot API** created for the **Kopi Challenge**.
The bot is designed to **hold a debate and try to convince the other side**, always defending a fixed stance, even when the topic may be irrational (e.g., *“The Earth is flat”*).

### Name: **Rickbot**

I decided to name the bot **Rickbot**, inspired by *Rick Sánchez* from *Rick and Morty*. Rick constantly debates, challenges others, and defends his views with extreme arguments, which felt like the perfect fit for a debate chatbot.

### Key features:

* The **first turn** sets the *topic* and the *stance* (pro/contra).
* Every bot response starts with `[[STANCE:pro]]` or `[[STANCE:contra]]`.
* The bot never changes its stance or topic.
* All answers are in **English** and ≤ 180 words.
* Conversation history is trimmed to the **last 5 turns** (10 messages).

---

## 🚀 Additional decisions (beyond the challenge)

### 1. Extended request on the first turn

The challenge only required:

```json
{ "conversation_id": "text" | null, "message": "text" }
```

I extended the first request to also allow:

* Selecting the **LLM provider** (`gemini`, `openai`, `deepseek`).
* Choosing the **stance** (`pro` or `contra`).
* (Future) Adding a **language field** so the user can choose the debate language.

👉 These options are only available at the start of a conversation. Once a `conversation_id` is set, only the `message` can be updated.

---

### 2. Multi-LLM Providers

Instead of relying on just one model, I integrated **three providers**:

* **Gemini** (Google)
* **OpenAI**
* **DeepSeek**

👉 This makes it possible to compare outputs, experiment with different models, and keep the system flexible for future providers.

---

### 3. Database persistence

Even though it wasn’t required, I added **SQLite with SQLAlchemy**.

👉 Reasons:

* Keep conversations after server restarts (memory-only storage is not enough in real use).
* Provide a base that can later scale to PostgreSQL or MySQL.
* Store metadata (timestamps, history) to enable **analytics** like response length or usage frequency.

---

### 4. Extra endpoint: `GET /conversation/{id}`

I created an additional endpoint to **retrieve the history of a conversation**.

👉 Reasons:

* Useful to review or audit a full debate.
* Makes it easier to integrate with more advanced frontends or dashboards.
* Helpful for debugging, since I can verify the stored conversation in DB or memory.

---

### 5. Minimal frontend

I built a small **HTML + JS page** under `/static`.

* Allows sending messages and selecting stance and provider on the first turn.
* Shows conversation history.
* Performs health checks and measures latency.
* Displays the `conversation_id`.

👉 Goal: make the API more **user-friendly** and easy to demo, even for people with no API background.
⚠️ In the future, I plan to **hide the `conversation_id`** on the UI for better security and UX.

---

### 6. Tests

Due to time limits, I focused only on the most important rules:

* First turn always includes stance marker and banner.
* Answers are ≤ 180 words.
* Bot replies in English, even if the user asks for Spanish.
* Conversation history trimmed to 10 messages.

👉 Priority was to validate the **critical rules of the challenge**.

⚡ Future improvements:

* Full HTTP integration tests with FastAPI.
* Simulated provider errors (RateLimit, Timeout).
* Stress/load tests to ensure answers stay <30s.

---

### 7. Deployment on Render

I deployed the project on **Render** because:

* It supports Docker-based services with minimal setup.
* It allowed me to quickly share a **public URL**: [rickbot-k4ad.onrender.com](https://rickbot-k4ad.onrender.com/).
* The free plan was more than enough for this challenge.

---

## 🛠️ Built With

* [FastAPI](https://fastapi.tiangolo.com/) – Web framework
* [Uvicorn](https://www.uvicorn.org/) – ASGI server
* [Pydantic v2](https://docs.pydantic.dev/) – Data validation
* [SQLAlchemy 2.x](https://docs.sqlalchemy.org/) – ORM
* [SQLite](https://www.sqlite.org/) – Lightweight database
* [Docker & Compose](https://docs.docker.com/) – Containers
* [Pytest](https://docs.pytest.org/) – Testing
* [OpenAI SDK](https://github.com/openai/openai-python), [Google Generative AI](https://ai.google.dev/), [DeepSeek API](https://api-docs.deepseek.com/) – LLM providers

---

## 🚀 Getting Started

### Requirements

* Python 3.11+
* Docker + Docker Compose

### Local setup

```bash
make install     # install dependencies
make test        # run tests
uvicorn fastapi_app:app --reload
```

### With Docker

```bash
make run         # start at http://localhost:8000
make down        # stop the service
make clean       # remove containers and volumes
```

### Environment variables

* `USE_DB` = `1` to use SQLite (default `0` = memory only)
* `DB_URL` = `sqlite:////app/data/conversations.db` (default: `./conversations.db`)
* `GEMINI_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY` = LLM credentials
* `DEFAULT_PROVIDER` = default provider (`gemini`, `openai`, `deepseek`)

---

## 📦 Usage

### Example with `curl`

```bash
curl -X POST http://localhost:8000/conversation \
  -H "Content-Type: application/json" \
  -H "X-LLM-Provider: gemini" \
  -H "X-Stance: pro" \
  -d '{"conversation_id": null, "message": "The Earth is flat"}'
```

### Example with public URL

```bash
curl -s -X POST https://rickbot-k4ad.onrender.com/conversation \
  -H "Content-Type: application/json" \
  -H "X-LLM-Provider: openai" \
  -H "X-Stance: pro" \
  -d '{"conversation_id": null, "message":"The Earth is flat."}'
```

### Endpoints

* `POST /conversation` – Send a message and get a reply
* `GET /conversation/{id}` – Retrieve recent history (10 messages)
* `GET /health` – Service health check
* `/` – Minimal static client

---

## 🔮 Roadmap

* Database migrations with Alembic (instead of `create_all`)
* Global error handler for `ProviderError` → cleaner responses on 401/403/429/5xx
* Strict timeouts to guarantee <30s response time
* Improved static UI with chat-style design
* Hide `conversation_id` on the frontend
* Metrics, logging, and conversation analytics
* Add multilingual support (not just English)
* Authentication for public deployments

---

## 👩‍💻 Contact

**Juliette Ceballos**

* 🌐 [Live demo](https://rickbot-k4ad.onrender.com/)
* 💼 [GitHub](https://github.com/julietteceb16)

---





