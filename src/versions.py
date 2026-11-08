"""Выбор версии npm по объявленному диапазону."""

import re

NUMBER = r"(?:0|[1-9][0-9]*)"
PRERELEASE = rf"(?:{NUMBER}|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
VERSION = re.compile(
    rf"{NUMBER}\.{NUMBER}\.{NUMBER}"
    rf"(?:-{PRERELEASE}(?:\.{PRERELEASE})*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
PART = rf"(?:{NUMBER}|[xX*])"
PARTIAL = re.compile(rf"{PART}(?:\.{PART}){{0,2}}")
COMPARATOR = re.compile(r"(<=|>=|<|>|=|~>|~|\^)?(.+)")
MIN_VERSION = (0, 0, 0)
MAJOR, MINOR = 0, 1
FULL_VERSION = len(MIN_VERSION)


def version_parts(text):
    """Вернуть числовую тройку, точность записи и признак prerelease."""
    text = text.removeprefix("v")
    if VERSION.fullmatch(text):
        core, separator, _ = text.split("+", 1)[0].partition("-")
        return tuple(map(int, core.split("."))), FULL_VERSION, bool(separator)
    if not PARTIAL.fullmatch(text):
        raise ValueError(f"неподдерживаемая версия или диапазон {text!r}")
    prefix = []
    wildcard = False
    for part in text.split("."):
        if part in ("x", "X", "*"):
            wildcard = True
        elif wildcard:
            raise ValueError(f"некорректный диапазон {text!r}")
        else:
            prefix.append(int(part))
    base = tuple(prefix) + MIN_VERSION[len(prefix):]
    return base, len(prefix), False


def bump(version, index):
    """Повысить компонент версии и обнулить компоненты справа."""
    return version[:index] + (version[index] + 1,) + MIN_VERSION[index + 1:]


def caret_upper(base, precision):
    """Найти верхнюю границу caret по первому ненулевому компоненту."""
    for index, number in enumerate(base[:precision]):
        if number:
            return bump(base, index)
    return bump(base, precision - 1)


def comparator_bounds(token):
    """Перевести компаратор в полуоткрытый интервал стабильных версий."""
    operator, text = COMPARATOR.fullmatch(token).groups()
    base, precision, prerelease = version_parts(text)
    if not precision:
        upper = MIN_VERSION if operator in ("<", ">") else None
        return MIN_VERSION, upper
    next_version = bump(base, precision - 1)
    after = base if prerelease else next_version
    simple = {
        None: (base, after),
        "=": (base, after),
        ">": (after, None),
        ">=": (base, None),
        "<": (MIN_VERSION, base),
        "<=": (MIN_VERSION, after),
    }
    if operator in simple:
        return simple[operator]
    if operator == "^":
        return base, caret_upper(base, precision)
    index = MINOR if precision > MINOR else MAJOR
    return base, bump(base, index)


def clause_bounds(clause):
    """Объединить ограничения одной ветви диапазона."""
    hyphen = re.fullmatch(r"(\S+)\s+-\s+(\S+)", clause)
    if hyphen:
        first, last = hyphen.groups()
        clause = f">={first} <={last}"
    clause = re.sub(r"([<>=~^]+)\s+", r"\1", clause)
    lower, upper = MIN_VERSION, None
    for token in clause.split():
        start, end = comparator_bounds(token)
        lower = max(lower, start)
        if end is not None and (upper is None or end < upper):
            upper = end
    return lower, upper


def parse_requirement(requirement):
    """Разобрать точную версию либо альтернативные интервалы."""
    text = requirement.strip()
    exact = text.removeprefix("=").lstrip().removeprefix("v")
    if VERSION.fullmatch(exact):
        return exact, []
    return None, [clause_bounds(part.strip()) for part in text.split("||")]


def stable_candidates(versions, bounds):
    """Перебрать стабильные версии, попавшие в один из интервалов."""
    for version in versions:
        if not VERSION.fullmatch(version):
            continue
        base, _, prerelease = version_parts(version)
        if prerelease:
            continue
        if any(lo <= base and (hi is None or base < hi) for lo, hi in bounds):
            yield base, version


def select_version(versions, exact, bounds):
    """Вернуть точную или наибольшую подходящую стабильную версию."""
    if exact is not None:
        return exact if exact in versions else None
    best = max(stable_candidates(versions, bounds), default=None)
    return best[1] if best is not None else None
