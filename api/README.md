# api

FastAPI service that starts runs, streams their steps and returns their findings. It holds the LLM key; the browser never sees it.

Owner: Person B. Spec: Delivery, Live interface.

```bash
pip install -e ".[dev,browser,api]"
uvicorn api.app:app --port 8000          # from the repo root; key from .env
```

| Endpoint | Does |
| --- | --- |
| `POST /runs` | Body `{persona, page, condition, seed}` (`page` without `.html`; `condition` is `persona` or `baseline`). Returns `202 {run_id, status}`; `422` says why a request cannot run; `429` when the queue is full |
| `GET /runs/{run_id}` | `status` (`queued`, `running`, then the loop's end status or `failed`), the request, `run.json`, every step record so far, and the findings with verified citations once the run has ended |
| `GET /runs/{run_id}/stream` | Server-sent events: one `step` event per step record as the loop writes it, then one `end` event with `status`, `error` and `findings` |
| `GET /options` | Personas (with whether each can run yet), pages with their task, and conditions |
| `GET /health` | `{"status": "ok"}` |

| Variable | Default | Meaning |
| --- | --- | --- |
| `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL` | from `.env` | The model, as for `agent.run` |
| `SIMUX_LOGS` | `logs/api/` | Where each run's log folder goes (git-ignored) |
| `SIMUX_WORKERS` | `1` | Runs at once; each drives its own Chromium |
| `SIMUX_MAX_QUEUED` | `5` | Runs waiting beyond the workers before `429` |
| `SIMUX_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Browser origins allowed to call the API (add the Vercel URL) |

The image (`api/Dockerfile`, built from the repo root) is built and smoke-tested by CI on every pull request and pushed to `ghcr.io/mustafakashif87/sim-ux-api` by CD after merge.
