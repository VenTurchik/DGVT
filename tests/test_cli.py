"""Проверки запуска DGVT через run.sh."""

import subprocess
from pathlib import Path

import pytest

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
    ("args", "expected"),
    [
        (
            ["--package", "is-odd", "--version", "3.0.1"],
            [
                "package=is-odd",
                "repository=https://registry.npmjs.org",
                "test_mode=false",
                "version=3.0.1",
                "ascii=false",
            ],
        ),
        (
            [
                "--package", "@scope/example", "--version", "1.0.0-rc.1+dev",
                "--repository", "http://localhost:8080/npm", "--ascii",
            ],
            [
                "package=@scope/example",
                "repository=http://localhost:8080/npm",
                "test_mode=false",
                "version=1.0.0-rc.1+dev",
                "ascii=true",
            ],
        ),
        (
            [
                "--package", "A", "--test-mode", "--repository",
                "examples/repository.json",
            ],
            [
                "package=A",
                "repository=examples/repository.json",
                "test_mode=true",
                "version=",
                "ascii=false",
            ],
        ),
    ],
)
def test_print_config(args, expected):
    """CLI выводит все пять значений, в том числе значения по умолчанию."""
    result = run_cli(*args)
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == expected


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
