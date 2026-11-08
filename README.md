# DGVT

Инструмент визуализации графа зависимостей npm-пакетов.

**Практическая работа №2 по дисциплине «Конфигурационное управление».
Вариант №12.**

## Содержание

- [Общее описание](#общее-описание)
- [Установка и запуск](#установка-и-запуск)
- [Этап 1. Минимальный CLI и конфигурация](#этап-1-минимальный-cli-и-конфигурация)
- [Тесты](#тесты)

## Общее описание

DGVT принимает имя npm-пакета и параметры анализа зависимостей.
Этапы работы зафиксированы отдельными коммитами.

## Установка и запуск

Для запуска нужны Python 3.10+ и оболочка sh. Сборка не требуется.

Из корня проекта:

```sh
./run.sh --help
./run.sh --package is-odd --version 3.0.1
```

## Этап 1. Минимальный CLI и конфигурация

На первом этапе приложение проверяет параметры и печатает конфигурацию.
Для URL проверяется формат адреса. Для тестового файла проверяется
читаемость, а разбор его содержимого относится к этапу построения графа.

### Структура проекта на этапе 1

```text
.
├── README.md
├── .gitignore
├── run.sh                    # запуск CLI
├── requirements-dev.txt      # pytest
├── src/
│   └── main.py                # разбор аргументов, проверки и вывод
├── examples/
│   └── repository.json       # пример локального репозитория
└── tests/
    └── test_cli.py            # проверки через run.sh
```

### Параметры

| Параметр | Назначение |
| --- | --- |
| `--package NAME` | Обязательное имя пакета, например `is-odd` или `@scope/pkg`. В тестовом режиме — только буквы A–Z. |
| `--repository SOURCE` | Базовый HTTP(S)-адрес без учётных данных, запроса и фрагмента. По умолчанию `https://registry.npmjs.org`. В тестовом режиме обязателен путь к читаемому файлу. |
| `--test-mode` | Переключает источник на локальный тестовый файл. |
| `--version VERSION` | Точная версия npm-пакета, обязательна в сетевом режиме. С `--test-mode` не используется. |
| `--ascii` | Флаг вывода ASCII-дерева. На этапе 1 выводится его значение. |

### Примеры работы

```sh
./run.sh --package is-odd --version 3.0.1 --ascii
```

```text
package=is-odd
repository=https://registry.npmjs.org
test_mode=false
version=3.0.1
ascii=true
```

```sh
./run.sh --package A --test-mode --repository examples/repository.json
```

```text
package=A
repository=examples/repository.json
test_mode=true
version=
ascii=false
```

### Обработка ошибок

При неверных параметрах приложение печатает сообщение в stderr и
завершается с кодом 2. Успешный запуск завершается с кодом 0.

```sh
./run.sh --version 3.0.1                                  # нет имени пакета
./run.sh --package 'Bad Name' --version 3.0.1              # неверное имя
./run.sh --package is-odd                                 # нет версии
./run.sh --package is-odd --version '^3.0.1'               # диапазон версий
./run.sh --package is-odd --version 3.0.1 --repository ftp://example.org
./run.sh --package A --test-mode                          # нет пути к файлу
./run.sh --package A --test-mode --repository missing.json
./run.sh --package is-odd --version 3.0.1 --test-mode=true # флаг без значения
./run.sh --package is-odd --version 3.0.1 --ascii=true     # флаг без значения
```

## Тесты

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Тесты запускают CLI в обоих режимах и проверяют ошибки каждого
параметра. Для тестов доступ к npm-реестру не требуется.
