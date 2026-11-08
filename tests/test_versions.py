"""Проверки границ диапазонов npm."""

import pytest

from src.versions import parse_requirement, select_version

VERSIONS = [
    "0.0.4", "0.0.5", "0.2.3", "0.2.9", "0.3.0", "1.0.0",
    "1.1.0", "1.2.3", "1.2.4", "1.2.10", "1.3.0", "2.0.0",
    "2.1.0-beta.1", "3.0.0-beta.1",
]


@pytest.mark.parametrize(
    ("requirement", "expected"),
    [
        ("1.2.3", "1.2.3"),
        ("=v3.0.0-beta.1", "3.0.0-beta.1"),
        ("^0.0.4", "0.0.4"),
        ("^0.2.3", "0.2.9"),
        ("^0.0", "0.0.5"),
        ("^0", "0.3.0"),
        ("~1.2.3", "1.2.10"),
        ("~1", "1.3.0"),
        (">= 1.2.3 <1.3.0", "1.2.10"),
        (">1.2 <2", "1.3.0"),
        ("<=1.2", "1.2.10"),
        ("<1.2", "1.1.0"),
        ("1.0.0 - 1.2", "1.2.10"),
        ("1.0.0 - 1.2.4", "1.2.4"),
        ("~1.2.3 || 2.x", "2.0.0"),
        ("1.2.*", "1.2.10"),
        ("1", "1.3.0"),
        ("*", "2.0.0"),
        ("", "2.0.0"),
        ("<*", None),
        (">=3", None),
        (">1.2.3-rc.1 <=1.2.3", "1.2.3"),
    ],
)
def test_select_version(requirement, expected):
    """Выбрать точную версию или максимум с учётом границ."""
    assert select_version(VERSIONS, *parse_requirement(requirement)) == expected


@pytest.mark.parametrize("requirement", ["git+https://example.org", "file:../x",
                                         "npm:other@1.0.0", "latest", ">=oops"])
def test_unsupported_requirement(requirement):
    """Не заменять нестандартную спецификацию значением latest."""
    with pytest.raises(ValueError, match="неподдерживаемая"):
        parse_requirement(requirement)
