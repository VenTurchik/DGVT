#!/bin/sh
project_dir=$(dirname -- "$0")
PYTHONPATH="$project_dir${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m src.main "$@"
