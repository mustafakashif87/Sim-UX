"""Perception: turn a Playwright accessibility snapshot into what the model sees.

Pure functions, no browser. `agent/browser.py` takes the snapshot from a page;
this module parses it, assigns each element a short ref (e1, e2, ...), applies
the persona's perception filters and renders the text the model receives.

The model only ever sees refs. RefMap, which says how to find each ref's
element again, stays inside the harness (spec: "Shared perception base").
"""

import json
import re
from dataclasses import dataclass, field

import yaml

# Snapshot keys that are not elements: plain text and properties like /url.
_TEXT_ROLE = "text"

# `role "name" [attr] [attr=value]`; the name is a JSON-style quoted string.
_KEY = re.compile(
    r"^(?P<role>[a-z]+)"
    r'(?:\s+(?P<name>"(?:[^"\\]|\\.)*"))?'
    r"(?P<attrs>(?:\s+\[[^\]]+\])*)$"
)
_ATTR = re.compile(r"\[([^\]=]+)(?:=([^\]]*))?\]")


@dataclass
class Node:
    role: str
    name: str | None = None
    attrs: dict[str, str] = field(default_factory=dict)
    text: str | None = None  # inline value, e.g. a textbox's current content
    props: dict[str, str] = field(default_factory=dict)  # e.g. {"url": "other.html"}
    children: list["Node"] = field(default_factory=list)
    ref: str | None = None


@dataclass(frozen=True)
class RefTarget:
    """How browser.py finds a ref's element: the nth element with this role and
    name, in document order. `nth_in_role` is used when the element has no name."""

    role: str
    name: str | None
    nth: int
    nth_in_role: int


RefMap = dict[str, RefTarget]


class SnapshotError(ValueError):
    pass


def parse_snapshot(snapshot: str) -> list[Node]:
    """Parse Playwright's YAML aria snapshot into a tree of Nodes."""
    data = yaml.safe_load(snapshot) or []
    if not isinstance(data, list):
        raise SnapshotError("snapshot must be a YAML list")
    return [n for item in data if (n := _parse_item(item)) is not None]


def _parse_item(item: object) -> Node | None:
    if isinstance(item, str):
        return _parse_key(item)
    if isinstance(item, dict) and len(item) == 1:
        key, value = next(iter(item.items()))
        key = str(key)
        if key.startswith("/"):
            return None  # a property; attached by the parent
        node = _parse_key(key)
        if isinstance(value, list):
            for child in value:
                if isinstance(child, dict) and len(child) == 1:
                    k, v = next(iter(child.items()))
                    if str(k).startswith("/"):
                        node.props[str(k)[1:]] = str(v)
                        continue
                if (c := _parse_item(child)) is not None:
                    node.children.append(c)
        elif value is not None:
            node.text = str(value)
        return node
    raise SnapshotError(f"unexpected snapshot entry: {item!r}")


def _parse_key(key: str) -> Node:
    m = _KEY.match(key.strip())
    if not m:
        raise SnapshotError(f"unrecognised snapshot line: {key!r}")
    name = json.loads(m["name"]) if m["name"] else None
    attrs = {k.strip(): (v or "").strip() for k, v in _ATTR.findall(m["attrs"] or "")}
    # A rendered tree (e.g. a logged observation) carries refs as [ref=eN].
    return Node(role=m["role"], name=name, attrs=attrs, ref=attrs.pop("ref", None))


def assign_refs(nodes: list[Node]) -> RefMap:
    """Give every element (not plain text) a ref, in document order."""
    refs: RefMap = {}
    by_name: dict[tuple[str, str | None], int] = {}
    by_role: dict[str, int] = {}
    for node in walk(nodes):
        if node.role == _TEXT_ROLE:
            continue
        key = (node.role, node.name)
        node.ref = f"e{len(refs) + 1}"
        refs[node.ref] = RefTarget(
            role=node.role,
            name=node.name,
            nth=by_name.get(key, 0),
            nth_in_role=by_role.get(node.role, 0),
        )
        by_name[key] = by_name.get(key, 0) + 1
        by_role[node.role] = by_role.get(node.role, 0) + 1
    return refs


def walk(nodes: list[Node]):
    """Yield every node in document order."""
    for node in nodes:
        yield node
        yield from walk(node.children)


def _not_built(name: str, reason: str):
    """A filter a config may name but no run may use yet: fail loudly rather
    than silently show the full tree."""

    def apply(nodes: list[Node]) -> list[Node]:
        raise NotImplementedError(f"perception filter '{name}' is not built yet: {reason}")

    return apply


# Perception filters by config name (spec: Persona framework). Each takes and
# returns the node list; later personas add their filters here.
FILTERS = {
    "full_tree": lambda nodes: nodes,
    # P3: words outside a common-word list become [unknown]. Its word list is an
    # open decision in the spec, so the filter is registered (P3's config is
    # valid) but cannot run until the list is chosen.
    "vocab_filter": _not_built("vocab_filter", "the P3 word list is an open decision"),
}


def apply_filters(nodes: list[Node], names: list[str]) -> list[Node]:
    for name in names:
        if name not in FILTERS:
            raise ValueError(f"unknown perception filter: {name}")
        nodes = FILTERS[name](nodes)
    return nodes


def render(nodes: list[Node], indent: int = 0) -> str:
    """Render nodes as the tree text the model sees, with refs and no HTML.

    The output is Playwright's snapshot format plus refs, and is valid YAML:
    `parse_snapshot(render(nodes))` gives the same tree back, which is how
    detectors read logged observations.
    """
    lines: list[str] = []
    for node in nodes:
        pad = "  " * indent
        if node.role == _TEXT_ROLE:
            lines.append(f"{pad}- text: {_value(node.text or '')}")
            continue
        head = node.role
        if node.name is not None:
            head += f" {json.dumps(node.name, ensure_ascii=False)}"
        for k, v in node.attrs.items():
            head += f" [{k}={v}]" if v else f" [{k}]"
        head += f" [ref={node.ref}]" if node.ref else ""
        line = f"{pad}- {_key(head)}"
        if node.text is not None:
            line += f": {_value(node.text)}"
        elif node.children or node.props:
            line += ":"  # a parent, as in Playwright's format
        lines.append(line)
        for k, v in node.props.items():
            lines.append(f"{pad}  - /{k}: {_value(v)}")
        if node.children:
            lines.append(render(node.children, indent + 1))
    return "\n".join(line for line in lines if line)


def _loads(text: str):
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        return None


def _value(text: str) -> str:
    """Text after a colon, quoted only when YAML would misread it, e.g. "a: b",
    "123" or "#tag"."""
    return text if _loads(f"k: {text}") == {"k": text} else json.dumps(text, ensure_ascii=False)


def _key(head: str) -> str:
    """An element line, single-quoted only when YAML would misread it, as
    Playwright does: 'button "Save: now"'."""
    if _loads(f"- {head}") == [head] and _loads(f"{head}: v") == {head: "v"}:
        return head
    return "'" + head.replace("'", "''") + "'"
