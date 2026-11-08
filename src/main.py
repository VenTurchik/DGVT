"""Командная строка DGVT."""

import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_REPOSITORY = "https://registry.npmjs.org"
PACKAGE_PART = r"[a-z0-9-][a-z0-9._-]*"
NPM_NAME = re.compile(rf"(?:@{PACKAGE_PART}/)?{PACKAGE_PART}")
TEST_NAME = re.compile(r"[A-Z]+")
NUMBER = r"(?:0|[1-9][0-9]*)"
PRERELEASE = rf"(?:{NUMBER}|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
VERSION = re.compile(
    rf"{NUMBER}\.{NUMBER}\.{NUMBER}"
    rf"(?:-{PRERELEASE}(?:\.{PRERELEASE})*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


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


def main():
    """Напечатать конфигурацию в формате ключ=значение."""
    args = parse_args()
    print(f"package={args.package}")
    print(f"repository={args.repository}")
    print(f"test_mode={str(args.test_mode).lower()}")
    print(f"version={args.version or ''}")
    print(f"ascii={str(args.ascii).lower()}")


if __name__ == "__main__":
    main()
