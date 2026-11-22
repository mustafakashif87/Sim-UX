"""Small helpers detectors share for reading observation trees."""

from agent.contracts import Observation
from agent.perception import Node, parse_snapshot, walk


def nodes(obs: Observation) -> list[Node]:
    return list(walk(parse_snapshot(obs.tree)))


def by_ref(obs: Observation, ref: str | None) -> Node | None:
    """The node the persona saw under this ref, if any."""
    if ref is None:
        return None
    return next((n for n in nodes(obs) if n.ref == ref), None)


def same_screen(a: Observation, b: Observation) -> bool:
    """Same URL and the same accessibility tree (focus and notes ignored)."""
    return a.url_path == b.url_path and a.tree == b.tree
