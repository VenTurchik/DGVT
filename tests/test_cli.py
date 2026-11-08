"""Проверки запуска DGVT через run.sh."""

import subprocess
import sys
from pathlib import Path

import pytest

from src import main

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    """Запустить CLI из корня проекта и получить его вывод."""
    return subprocess.run(
        [str(ROOT / "run.sh"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )


@pytest.mark.parametrize(
    ("root", "edges"),
    [
        ("A", ["A -> B", "A -> C", "B -> D", "C -> D", "D -> E"]),
        ("F", ["F -> G", "G -> F"]),
        ("H", ["H"]),
    ],
)
def test_local_graph(root, edges):
    """CLI выводит достижимую часть графа, в том числе циклы."""
    result = run_cli(
        "--package", root, "--test-mode",
        "--repository", "examples/graphs.json",
    )
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == edges


def test_unknown_vertex():
    """Неизвестный корень даёт ошибку выполнения."""
    result = run_cli(
        "--package", "Z", "--test-mode",
        "--repository", "examples/graphs.json",
    )
    assert result.returncode == 1
    assert "вершина Z не найдена" in result.stderr


@pytest.mark.parametrize(
    ("args", "option"),
    [
        (["--version", "1.0.0"], "--package"),
        (["--package", "Bad Name", "--version", "1.0.0"], "--package"),
        (["--package", "a", "--test-mode"], "--package"),
        (["--package", "a"], "--version"),
        (["--package", "a", "--version", "^1.0.0"], "--version"),
        (["--package", "a", "--version", "1.0.0-01"], "--version"),
        (["--package", "A", "--test-mode", "--version", "1.0.0"], "--version"),
        (
            ["--package", "a", "--version", "1.0.0", "--repository", "ftp://a"],
            "--repository",
        ),
        (
            [
                "--package", "a", "--version", "1.0.0",
                "--repository", "https://localhost:abc",
            ],
            "--repository",
        ),
        (["--package", "A", "--test-mode"], "--repository"),
        (
            [
                "--package", "A", "--test-mode", "--repository",
                "examples/missing.json",
            ],
            "--repository",
        ),
        (
            ["--package", "A", "--test-mode", "--repository", "."],
            "--repository",
        ),
        (["--package", "a", "--version", "1.0.0", "--ascii=true"], "--ascii"),
        (
            ["--package", "a", "--version", "1.0.0", "--test-mode=1"],
            "--test-mode",
        ),
    ],
)
def test_invalid_argument(args, option):
    """Неверная конфигурация отклоняется без вывода значений и traceback."""
    result = run_cli(*args)
    assert result.returncode == 2
    assert result.stdout == ""
    assert option in result.stderr.splitlines()[-1]
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("D", ["B", "C", "A"]),
        ("F", ["G"]),
        ("H", ["Обратных зависимостей нет."]),
    ],
)
def test_reverse_local_graph(target, expected):
    """Найти зависимые вершины во всём файле и исключить саму цель."""
    result = run_cli(
        "--package", "A", "--test-mode", "--repository",
        "examples/graphs.json", "--reverse", target,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == expected


def test_reverse_unknown_target():
    """Неизвестная цель обратного поиска даёт ошибку выполнения."""
    result = run_cli(
        "--package", "A", "--test-mode", "--repository",
        "examples/graphs.json", "--reverse", "Z",
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "вершина Z не найдена" in result.stderr


def test_reverse_npm_graph(monkeypatch, capsys):
    """Обратный поиск в npm различает версии одного пакета."""
    graph = {
        "root@1.0.0": ["a@1.0.0", "b@1.0.0"],
        "a@1.0.0": ["dep@1.0.0"],
        "b@1.0.0": ["dep@2.0.0"],
        "dep@1.0.0": [],
        "dep@2.0.0": [],
        "outside@1.0.0": ["dep@2.0.0"],
    }
    monkeypatch.setattr(main, "npm_neighbors", lambda _: graph.__getitem__)
    monkeypatch.setattr(
        sys, "argv",
        ["DGVT", "--package", "root", "--version", "1.0.0",
         "--reverse", "dep@2.0.0"],
    )
    assert main.main() == 0
    assert capsys.readouterr().out.splitlines() == ["b@1.0.0", "root@1.0.0"]
