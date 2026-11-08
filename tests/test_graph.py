"""Проверки графа с тестовым файлом и подменой npm-реестра."""

from collections import Counter

import pytest

from src import registry
from src.graph import bfs, load_test_graph


def test_npm_graph(monkeypatch):
    """BFS сохраняет циклы и разные версии, метаданные читает один раз."""
    packages = {
        "root": {"1.0.0": {"dependencies": {"a": "^1", "b": "1.0.0"}}},
        "a": {
            "1.1.0": {"dependencies": {"a": "~1.1.0"}},
            "2.0.0": {},
        },
        "b": {"1.0.0": {"dependencies": {"a": "^2", "root": "1.0.0"}}},
    }
    calls = Counter()

    def fetch_versions(repository, name):
        """Вернуть метаданные из тестового набора и учесть обращение."""
        calls[name] += 1
        return packages[name]

    monkeypatch.setattr(registry, "fetch_versions", fetch_versions)
    graph = bfs("root@1.0.0", registry.npm_neighbors("https://example.org"))
    assert list(graph.items()) == [
        ("root@1.0.0", ["a@1.1.0", "b@1.0.0"]),
        ("a@1.1.0", ["a@1.1.0"]),
        ("b@1.0.0", ["a@2.0.0", "root@1.0.0"]),
        ("a@2.0.0", []),
    ]
    assert calls == {"root": 1, "a": 1, "b": 1}


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("{", "не удалось прочитать"),
        ("[]", "должен быть JSON-объектом"),
        ('{"a":[]}', "некорректное имя"),
        ('{"A":"B"}', "должны быть списком"),
        ('{"A":["B"]}', "неизвестная вершина"),
        ('{"A":[{}]}', "неизвестная вершина"),
    ],
)
def test_invalid_test_graph(tmp_path, body, message):
    """Ошибочные файлы отклоняются до запуска BFS."""
    path = tmp_path / "graph.json"
    path.write_text(body, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_test_graph(path)
