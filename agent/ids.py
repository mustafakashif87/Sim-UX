"""Run IDs: `<UTC time>-<persona>-<6 hex>`, e.g. `20261014T113651Z-error_prone-a9102d`.

One run ID names one log folder. The API makes the ID before the run starts,
so a client can follow it at once; the loop makes one itself otherwise.
"""

import re
import uuid
from datetime import UTC, datetime

RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z-[a-z][a-z0-9_]*-[0-9a-f]{6}$")


def new_run_id(persona_id: str) -> str:
    return f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{persona_id}-{uuid.uuid4().hex[:6]}"


def is_run_id(text: str) -> bool:
    """True for a well-formed run ID. Also keeps paths built from it inside the log root."""
    return bool(RUN_ID_PATTERN.match(text))
