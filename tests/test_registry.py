"""Проверки получения метаданных без сетевых запросов."""

import json
from io import BytesIO
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from src import registry

REPOSITORY = "https://example.org/npm/"
PACKAGE = "@scope/demo"
VERSION = "1.0.0"
URL = "https://example.org/npm/@scope%2Fdemo"


def read_dependencies():
    """Получить и разобрать метаданные проверяемого пакета."""
    versions = registry.fetch_versions(REPOSITORY, PACKAGE)
    return registry.get_dependencies(versions, PACKAGE, VERSION)


@pytest.mark.parametrize("release", [{}, {"dependencies": {}}])
def test_no_dependencies(monkeypatch, release):
    """Пустое или отсутствующее поле означает отсутствие зависимостей."""
    response = {"versions": {VERSION: release}}
    fake = Mock(return_value=BytesIO(json.dumps(response).encode()))
    monkeypatch.setattr(registry, "urlopen", fake)
    assert read_dependencies() == {}


def test_select_exact_version(monkeypatch):
    """Прочитать только нужную версию и закодировать scoped-имя."""
    expected = {"dep": "^2.0.0", "@other/dep": "~1.0.0"}
    response = {
        "dist-tags": {"latest": "2.0.0"},
        "versions": {
            VERSION: {
                "dependencies": expected, "devDependencies": {"dev": "*"},
            },
            "2.0.0": {"dependencies": {"other": "*"}},
        },
    }
    fake = Mock(return_value=BytesIO(json.dumps(response).encode()))
    monkeypatch.setattr(registry, "urlopen", fake)
    assert read_dependencies() == expected
    assert fake.call_args.args[0].full_url == URL


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (b"{", "некорректный JSON"),
        (b"[]", "ожидался объект"),
        (b'{"versions":[]}', "нет словаря версий"),
        (b'{"versions":{}}', "версия @scope/demo@1.0.0 не найдена"),
        (b'{"versions":{"1.0.0":null}}', "некорректные данные версии"),
        (
            b'{"versions":{"1.0.0":{"dependencies":null}}}',
            "должно быть словарём",
        ),
        (
            b'{"versions":{"1.0.0":{"dependencies":{"x":1}}}}',
            "некорректная запись",
        ),
    ],
)
def test_invalid_response(monkeypatch, body, message):
    """Повреждённый ответ или отсутствующая версия дают понятную ошибку."""
    monkeypatch.setattr(registry, "urlopen", Mock(return_value=BytesIO(body)))
    with pytest.raises(registry.RegistryError, match=message):
        read_dependencies()


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (
            HTTPError(URL, 404, "Not Found", {}, None),
            "пакет @scope/demo не найден",
        ),
        (HTTPError(URL, 503, "Unavailable", {}, None), "HTTP 503"),
        (URLError("unreachable"), "unreachable"),
        (TimeoutError("timed out"), "timed out"),
    ],
)
def test_request_error(monkeypatch, error, message):
    """Отказы HTTP, соединения и тайм-аут превращаются в ошибку DGVT."""
    monkeypatch.setattr(registry, "urlopen", Mock(side_effect=error))
    with pytest.raises(registry.RegistryError, match=message):
        read_dependencies()
