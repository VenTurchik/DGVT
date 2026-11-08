"""Командная строка DGVT."""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from .graph import TEST_NAME, bfs, load_test_graph
from .registry import RegistryError, npm_neighbors
from .versions import VERSION

DEFAULT_REPOSITORY = "https://registry.npmjs.org"
PACKAGE_PART = r"[a-z0-9-][a-z0-9._-]*"
NPM_NAME = re.compile(rf"(?:@{PACKAGE_PART}/)?{PACKAGE_PART}")


def is_registry_url(value):
    """Проверить формат базового HTTP(S)-адреса реестра."""
    if not value.isprintable() or " " in value or "\\" in value:
        return False
    try:
        url = urlsplit(value)
        host, _ = url.hostname, url.port
    except ValueError:
        return False
    if url.scheme not in ("http", "https") or not host:
        return False
    if url.username is not None or "?" in value or "#" in value:
        return False
    return True


def validate_test_mode(parser, args):
    """Проверить имя вершины, параметры и читаемость тестового файла."""
    if not TEST_NAME.fullmatch(args.package):
        parser.error("--package: в тестовом режиме нужны буквы A–Z")
    if args.version is not None:
        parser.error("--version: параметр применяется только без --test-mode")
    if not args.repository:
        parser.error("--repository: укажите путь к тестовому файлу")
    try:
        path = Path(args.repository)
        if path.is_file():
            with path.open("rb"):
                return
    except (OSError, ValueError):
        pass
    parser.error(f"--repository: не удалось открыть файл {args.repository!r}")


def parse_args():
    """Разобрать и проверить параметры запуска."""
    parser = argparse.ArgumentParser(
        prog="DGVT",
        description="Инструмент визуализации зависимостей npm",
        allow_abbrev=False,
    )
    parser.add_argument("--package", required=True, help="имя пакета")
    parser.add_argument("--repository", help="URL реестра или тестовый файл")
    parser.add_argument(
        "--test-mode", action="store_true", help="читать тестовый репозиторий"
    )
    parser.add_argument("--version", help="точная версия npm-пакета")
    parser.add_argument(
        "--ascii", action="store_true", help="включить вывод ASCII-дерева"
    )
    args = parser.parse_args()
    if args.test_mode:
        validate_test_mode(parser, args)
        return args
    if not NPM_NAME.fullmatch(args.package):
        parser.error("--package: ожидается имя npm-пакета, например @scope/pkg")
    if not args.version or not VERSION.fullmatch(args.version):
        parser.error("--version: укажите точную версию, например 1.2.3")
    if args.repository is None:
        args.repository = DEFAULT_REPOSITORY
    if not is_registry_url(args.repository):
        parser.error("--repository: ожидается базовый HTTP(S)-адрес")
    return args


def build_graph(args):
    """Построить граф для выбранного источника."""
    if args.test_mode:
        graph = load_test_graph(args.repository)
        if args.package not in graph:
            raise ValueError(f"вершина {args.package} не найдена")
        return bfs(args.package, graph.__getitem__)
    root = f"{args.package}@{args.version}"
    return bfs(root, npm_neighbors(args.repository))


def main():
    """Вывести рёбра графа транзитивных зависимостей."""
    args = parse_args()
    try:
        graph = build_graph(args)
    except (RegistryError, ValueError) as error:
        print(f"DGVT: {error}", file=sys.stderr)
        return 1
    for node, children in graph.items():
        for child in children:
            print(f"{node} -> {child}")
    if not any(graph.values()):
        print(next(iter(graph)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
