"""Проверки форматов вывода и ошибок визуализации."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from src import main, visualization

ROOT = Path(__file__).resolve().parents[1]
EXIT_SUCCESS = 0
EXIT_RUNTIME_ERROR = 1


def test_dot_keeps_nodes_and_edges():
    """В DOT остаются все вершины и ориентированные рёбра."""
    graph = {'@scope/a"\\b': ["B"], "B": [], "C": []}
    assert visualization.to_dot(graph).splitlines() == [
        "digraph dependencies {",
        "    rankdir=LR;",
        '    "@scope/a\\"\\\\b";',
        '    "B";',
        '    "C";',
        '    "@scope/a\\"\\\\b" -> "B";',
        "}",
    ]


def test_ascii_keeps_cycles_and_shared_dependencies_finite():
    """Повторные рёбра видны, вложенность определяется отступами."""
    graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": ["A"]}
    assert visualization.ascii_tree(graph).splitlines() == [
        "A",
        "|-- B",
        "|   +-- D",
        "|       +-- A [cycle]",
        "+-- C",
        "    +-- D [seen]",
    ]
    assert visualization.ascii_tree({"A": []}) == "A"


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (FileNotFoundError(), "Установите Graphviz"),
        (subprocess.TimeoutExpired("dot", 30), "время отрисовки"),
        (
            subprocess.CalledProcessError(1, "dot", stderr="syntax error"),
            "Graphviz: syntax error",
        ),
    ],
)
def test_render_failure(monkeypatch, tmp_path, error, message):
    """Объяснить ошибку dot и сохранить исходный DOT."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=error))
    with pytest.raises(RuntimeError, match=message):
        visualization.render_graph({"A": []})
    assert (tmp_path / "output" / "A.dot").is_file()


@pytest.mark.parametrize("opens", [True, False])
def test_cli_renders_graph(monkeypatch, tmp_path, capsys, opens):
    """CLI генерирует DOT/SVG, печатает дерево и пробует открыть SVG."""
    monkeypatch.chdir(tmp_path)
    args = [
        "DGVT", "--package", "F", "--test-mode", "--repository",
        str(ROOT / "examples" / "graphs.json"),
    ]
    if opens:
        args.append("--ascii")
    monkeypatch.setattr(sys, "argv", args)
    render = Mock(return_value=subprocess.CompletedProcess(
        ["dot"], 0, stdout="<svg/>",
    ))
    monkeypatch.setattr(subprocess, "run", render)
    open_browser = Mock(return_value=opens)
    monkeypatch.setattr(visualization.webbrowser, "open", open_browser)

    expected_status = EXIT_SUCCESS if opens else EXIT_RUNTIME_ERROR
    assert main.main() == expected_status
    dot_path = tmp_path / "output" / "F.dot"
    svg_path = tmp_path / "output" / "F.svg"
    assert '"G" -> "F";' in dot_path.read_text()
    assert svg_path.read_text() == "<svg/>"
    assert render.call_args.args[0] == ["dot", "-Tsvg", "output/F.dot"]
    open_browser.assert_called_once_with(svg_path.as_uri(), new=2)
    captured = capsys.readouterr()
    assert ("+-- F [cycle]" in captured.out) == opens
    assert ("Откройте файл вручную" in captured.err) != opens
