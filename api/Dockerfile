# SimUX API image. Build from the repository root:
#   docker build -f api/Dockerfile -t simux-api .
#   docker run -p 8000:8000 -e LLM_API_KEY=... -e SIMUX_CORS_ORIGINS=https://<web host> simux-api
#
# The base image ships Chromium and its system libraries for one Playwright
# release. Keep its tag equal to the Playwright version pinned below (and
# inside the cap in pyproject.toml), or the browser and the driver disagree.
FROM mcr.microsoft.com/playwright/python:v1.65.2-noble

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    SIMUX_LOGS=/data/logs

WORKDIR /app

# The code plus the persona configs and test app the runs read. Installed
# editable, so agent/ still finds personas/ and test-app/ beside it.
COPY pyproject.toml ./
COPY agent/ agent/
COPY grounding/ grounding/
COPY api/ api/
COPY personas/ personas/
COPY test-app/ test-app/
RUN pip install -e ".[browser,api]" "playwright==1.65.2" \
    && mkdir -p /data/logs \
    && chown -R pwuser /data /app

# pwuser is the base image's unprivileged user; Chromium's sandbox needs one.
USER pwuser

EXPOSE 8000
# Hosts such as Render and Railway set PORT; 8000 otherwise.
CMD ["sh", "-c", "uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
