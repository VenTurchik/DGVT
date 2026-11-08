"""Загрузка локального репозитория и обход графа."""

import json
import re
from collections import deque
from pathlib import Path

TEST_NAME = re.compile(r"[A-Z]+")


def load_test_graph(filename):
    """Прочитать словарь смежности и проверить все ссылки на вершины."""
    try:
        graph = json.loads(Path(filename).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        message = f"не удалось прочитать {filename!r}: {error}"
        raise ValueError(message) from error
    if not isinstance(graph, dict):
        raise ValueError("тестовый репозиторий должен быть JSON-объектом")
    for name, neighbors in graph.items():
        if not TEST_NAME.fullmatch(name):
            raise ValueError(f"некорректное имя вершины {name!r}")
        if not isinstance(neighbors, list):
            raise ValueError(f"зависимости {name} должны быть списком")
        for neighbor in neighbors:
            if not isinstance(neighbor, str) or neighbor not in graph:
                raise ValueError(f"{name}: неизвестная вершина {neighbor!r}")
    return graph


def bfs(root, neighbors):
    """Собрать достижимые вершины и все их рёбра в порядке BFS."""
    queue = deque([root])
    seen = {root}
    graph = {}
    while queue:
        node = queue.popleft()
        graph[node] = list(dict.fromkeys(neighbors(node)))
        for child in graph[node]:
            if child not in seen:
                seen.add(child)
                queue.append(child)
    return graph


def reverse_dependencies(graph, target):
    """Найти прямых и транзитивных предшественников вершины через BFS."""
    if target not in graph:
        raise ValueError(f"вершина {target} не найдена в графе")
    reverse = {node: [] for node in graph}
    for node, children in graph.items():
        for child in children:
            reverse[child].append(node)
    return list(bfs(target, reverse.__getitem__))[1:]
