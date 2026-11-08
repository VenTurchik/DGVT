"""Чтение метаданных пакетов из npm-реестра."""

import json
from http import HTTPStatus
from http.client import HTTPException
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

REQUEST_TIMEOUT = 10


class RegistryError(Exception):
    """Ожидаемая ошибка запроса или данных реестра."""


def fetch_metadata(repository, package):
    """Получить JSON со всеми опубликованными версиями пакета."""
    url = f"{repository.rstrip('/')}/{quote(package, safe='@')}"
    try:
        request = Request(
            url, headers={"Accept": "application/vnd.npm.install-v1+json"}
        )
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == HTTPStatus.NOT_FOUND:
            raise RegistryError(f"пакет {package} не найден") from error
        raise RegistryError(f"реестр ответил HTTP {error.code}") from error
    except (json.JSONDecodeError, UnicodeError) as error:
        raise RegistryError("реестр вернул некорректный JSON") from error
    except (OSError, HTTPException, ValueError) as error:
        raise RegistryError(f"ошибка запроса к реестру: {error}") from error


def get_dependencies(repository, package, version):
    """Вернуть словарь прямых зависимостей точной версии пакета."""
    metadata = fetch_metadata(repository, package)
    if not isinstance(metadata, dict):
        raise RegistryError("ожидался объект метаданных пакета")
    versions = metadata.get("versions")
    if not isinstance(versions, dict):
        raise RegistryError("в метаданных нет словаря версий")
    if version not in versions:
        raise RegistryError(f"версия {package}@{version} не найдена")
    release = versions[version]
    if not isinstance(release, dict):
        raise RegistryError(f"некорректные данные версии {package}@{version}")
    dependencies = release.get("dependencies", {})
    if not isinstance(dependencies, dict):
        raise RegistryError("поле dependencies должно быть словарём")
    for name, requirement in dependencies.items():
        if not name or not isinstance(requirement, str):
            raise RegistryError("некорректная запись в dependencies")
    return dependencies
