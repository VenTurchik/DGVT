"""Построение DOT, SVG и текстового дерева зависимостей."""

import subprocess
import webbrowser
from pathlib import Path

OUTPUT_DIR = Path("output")
RENDER_TIMEOUT = 30


def quote_dot(name):
    """Экранировать имя узла для строки DOT."""
    name = name.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{name}"'


def to_dot(graph):
    """Сформировать DOT со всеми вершинами и рёбрами графа."""
    lines = ["digraph dependencies {", "    rankdir=LR;"]
    for node in graph:
        lines.append(f"    {quote_dot(node)};")
    for node, children in graph.items():
        for child in children:
            lines.append(f"    {quote_dot(node)} -> {quote_dot(child)};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def push_children(stack, children, prefix):
    """Добавить детей в стек в обратном порядке для печати слева направо."""
    last = len(children) - 1
    for index in range(last, -1, -1):
        stack.append((children[index], prefix, index == last))


def ascii_tree(graph):
    """Напечатать каждую ветвь один раз и отметить повторы и циклы."""
    root = next(iter(graph))
    lines = [root]
    seen = {root}
    active = {root}
    stack = []
    push_children(stack, graph[root], "")
    while stack:
        node, prefix, last = stack.pop()
        if prefix is None:
            active.remove(node)
            continue
        branch = "+-- " if last else "|-- "
        line = f"{prefix}{branch}{node}"
        if node in active:
            lines.append(line + " [cycle]")
        elif node in seen:
            lines.append(line + " [seen]")
        else:
            lines.append(line)
            seen.add(node)
            active.add(node)
            stack.append((node, None, False))
            continuation = "    " if last else "|   "
            push_children(stack, graph[node], prefix + continuation)
    return "\n".join(lines)


def render_graph(graph):
    """Сохранить DOT и отрисовать его в SVG через Graphviz."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    name = next(iter(graph)).replace("/", "_")
    dot_path = OUTPUT_DIR / f"{name}.dot"
    svg_path = OUTPUT_DIR / f"{name}.svg"
    dot_path.write_text(to_dot(graph), encoding="utf-8")
    try:
        result = subprocess.run(
            ["dot", "-Tsvg", str(dot_path)],
            check=True, capture_output=True, text=True, timeout=RENDER_TIMEOUT,
        )
    except FileNotFoundError as error:
        message = "команда dot не найдена. Установите Graphviz."
        raise RuntimeError(message) from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Graphviz превысил время отрисовки") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or f"код {error.returncode}"
        raise RuntimeError(f"Graphviz: {detail}") from error
    svg_path.write_text(result.stdout, encoding="utf-8")
    return dot_path, svg_path


def open_graph(svg_path):
    """Открыть сохранённый SVG в браузере."""
    message = f"не удалось открыть браузер. Откройте файл вручную: {svg_path}"
    try:
        opened = webbrowser.open(svg_path.resolve().as_uri(), new=2)
    except (OSError, webbrowser.Error) as error:
        raise RuntimeError(message) from error
    if not opened:
        raise RuntimeError(message)
