# personas

One YAML file per persona, setting its perception, action, memory and perturbation constraints.

| File | Persona | Axis it changes | Status |
| --- | --- | --- | --- |
| `error_prone.yaml` | P1 Error-prone user | Perturbation | Built; evaluation runs (3 conditions × 5 seeds) pending |
| `memoryless.yaml` | P2 Memoryless first-time user | Memory (`history_turns: 0`) | Config only |
| `low_literacy.yaml` | P3 Low-literacy or non-native reader | Perception (`vocab_filter`) | Config only; the filter fails loudly until its word list is chosen |

Planned: P4 to P14 (screen-reader, keyboard-only, touch, low-vision zoom, skimmer, interrupted, slow-connection, help-seeker, habitual, power user, older adult). They are specified in `docs/persona-catalogue.md` and have no YAML files yet. Their configs need the proposed schema keys added to `agent/persona.py` first.

Owner: Person B. Spec: Config schema.
