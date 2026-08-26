#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
venv_dir="${TMPDIR:-/tmp}/dba5103_assignment1_venv"
python_command="${PYTHON:-python3}"

if [[ ! -x "$venv_dir/bin/python" ]]; then
    "$python_command" -m venv "$venv_dir"
fi

if ! "$venv_dir/bin/python" -c "import docx, matplotlib, numpy, PIL, scipy" 2>/dev/null; then
    "$venv_dir/bin/python" -m pip install --quiet \
        matplotlib numpy pillow scipy python-docx
fi

cd "$project_root"
exec "$venv_dir/bin/python" workings/assignment1_solution.py
