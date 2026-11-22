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

    def apply(nodes: list[Node], view: "View | None" = None) -> list[Node]:
        raise NotImplementedError(f"perception filter '{name}' is not built yet: {reason}")

    return apply


@dataclass(frozen=True)
class Box:
    """A bounding box in CSS px, relative to the visible viewport."""

    x: float
    y: float
    width: float
    height: float

    def intersects(self, other: "Box") -> bool:
        return (
            self.x < other.x + other.width
            and other.x < self.x + self.width
            and self.y < other.y + other.height
            and other.y < self.y + self.height
        )


@dataclass
class View:
    """What the harness knows about the page beyond the tree, for filters that
    need geometry (P4, P5, P7, P8). Never shown to the model.

    `boxes` maps id(node) of the parsed nodes to their box; nodes not on
    screen at all (display: none) have none.
    """

    viewport: Box
    boxes: dict[int, Box] = field(default_factory=dict)
    focused_ref: str | None = None
    focus_visible: bool | None = None
    window_nodes: int = 15
    rotor: tuple[str, ...] = ()
    skim_max_words: int = 8


def _copy(node: Node, **changes) -> Node:
    data = {
        "role": node.role,
        "name": node.name,
        "attrs": dict(node.attrs),
        "text": node.text,
        "props": dict(node.props),
        "children": list(node.children),
        "ref": node.ref,
    }
    return Node(**(data | changes))


# Roles whose inline text is what the user typed or chose, not page wording.
_VALUE_ROLES = {"textbox", "searchbox", "combobox", "spinbutton", "slider"}


def vocab_filter(nodes: list[Node], view: View | None = None) -> list[Node]:
    """P3: every word outside the common-word list becomes [unknown] in names
    and page text (agent/vocab.py). Values in fields are left as typed."""
    from agent.vocab import simplify

    def one(node: Node) -> Node:
        text = node.text
        if text is not None and node.role not in _VALUE_ROLES:
            text = simplify(text)
        return _copy(
            node,
            name=simplify(node.name) if node.name else node.name,
            text=text,
            children=[one(c) for c in node.children],
        )

    return [one(n) for n in nodes]


def _need_view(name: str, view: View | None) -> View:
    if view is None:
        raise ValueError(f"perception filter '{name}' needs page geometry (a View)")
    return view


def viewport_only(nodes: list[Node], view: View | None = None) -> list[Node]:
    """P7, P8: only what is on screen. A node stays when its own box meets
    the viewport, or when any of its children stays; a node without a box
    of its own (plain text) goes with its parent."""
    v = _need_view("viewport_only", view)

    def keep(node: Node, parent_visible: bool) -> Node | None:
        box = v.boxes.get(id(node))
        visible = box.intersects(v.viewport) if box else parent_visible
        kids = [k for c in node.children if (k := keep(c, visible)) is not None]
        if kids:
            return _copy(node, children=kids)
        if node.children:  # a container whose content is all off screen
            return None
        return _copy(node) if visible else None

    return [k for n in nodes if (k := keep(n, False)) is not None]


_TEXT_ROLES = {
    "text",
    "paragraph",
    "note",
    "status",
    "alert",
    "listitem",
    "cell",
    "term",
    "definition",
}


def skim_text(nodes: list[Node], view: View | None = None) -> list[Node]:
    """P8: page text past `skim_max_words` words is cut short with "…".
    Headings and control names are kept whole: people scan those."""
    limit = view.skim_max_words if view else 8

    def cut(text: str) -> str:
        words = text.split()
        return text if len(words) <= limit else " ".join(words[:limit]) + " …"

    def one(node: Node) -> Node:
        text = node.text
        if text is not None and node.role in _TEXT_ROLES:
            text = cut(text)
        return _copy(node, text=text, children=[one(c) for c in node.children])

    return [one(n) for n in nodes]


LANDMARK_ROLES = {
    "banner",
    "navigation",
    "main",
    "contentinfo",
    "complementary",
    "region",
    "search",
    "form",
}
_CONTAINER_ROLES = LANDMARK_ROLES | {
    "generic",
    "group",
    "list",
    "table",
    "rowgroup",
    "row",
    "dialog",
}


def linear_window(nodes: list[Node], view: View | None = None) -> list[Node]:
    """P4: a screen reader's reading order, one window at a time.

    The page is read as a flat list of items (containers dropped). The model
    sees `window_nodes` items from the reading position: the focused element,
    else the first item at the top of the viewport (so `scroll` reads on).
    With a rotor, the page's headings and landmarks are listed first, as a
    screen reader's rotor menu offers them."""
    v = _need_view("linear_window", view)
    flat = [n for n in walk(nodes) if n.role not in _CONTAINER_ROLES or n.text]
    items = [_copy(n, children=[]) for n in flat]
    pos = 0
    if v.focused_ref is not None:
        pos = next((i for i, n in enumerate(flat) if n.ref == v.focused_ref), 0)
    else:
        for i, n in enumerate(flat):
            box = v.boxes.get(id(n))
            if box and box.y + box.height > v.viewport.y:
                pos = i
                break
    start = max(0, pos - min(2, v.window_nodes - 1))  # a little context before
    window = items[start : start + v.window_nodes]
    rotor = []
    if "headings" in v.rotor:
        rotor += [_copy(n, children=[]) for n in walk(nodes) if n.role == "heading"]
    if "landmarks" in v.rotor:
        rotor += [_copy(n, children=[], text=None) for n in walk(nodes) if n.role in LANDMARK_ROLES]
    in_window = {n.ref for n in window if n.ref}
    return [n for n in rotor if n.ref not in in_window] + window


def visible_focus_only(nodes: list[Node], view: View | None = None) -> list[Node]:
    """P5: the tree is unchanged; `browser.observe` drops the focused element
    from the observation when it has no visible focus indicator."""
    return nodes


# Perception filters by config name (spec: Persona framework). Each takes the
# node list and an optional View and returns the node list.
FILTERS = {
    "full_tree": lambda nodes, view=None: nodes,
    "vocab_filter": vocab_filter,  # P3
    "viewport_only": viewport_only,  # P7, P8
    "skim_text": skim_text,  # P8
    "linear_window": linear_window,  # P4
    "visible_focus_only": visible_focus_only,  # P5
}
# Filters that need a View with bounding boxes.
GEOMETRY_FILTERS = {"viewport_only", "linear_window", "visible_focus_only"}


def apply_filters(nodes: list[Node], names: list[str], view: View | None = None) -> list[Node]:
    for name in names:
        if name not in FILTERS:
            raise ValueError(f"unknown perception filter: {name}")
        nodes = FILTERS[name](nodes, view)
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
