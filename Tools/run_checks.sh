#!/usr/bin/env bash
# 运行所有不依赖 Unity 编译的检查。
#
# 当前环境受 EsafeNet DocGuard 透明加密限制（见 Documentation/reports/环境报告.md 4.1），
# C# 无法编译，因此这些纯数据校验是现阶段唯一可跑通的验证手段。
#
# 用法（Git Bash）:
#   bash Tools/run_checks.sh

set -uo pipefail

PY="C:/Users/OFFICE/AppData/Roaming/uv/python/cpython-3.12.13-windows-x86_64-none/python.exe"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONIOENCODING=utf-8

status=0

run() {
    local name="$1"; shift
    echo "═══════════════════════════════════════════"
    echo "  $name"
    echo "═══════════════════════════════════════════"
    if "$@"; then
        echo "→ 通过"
    else
        echo "→ 失败"
        status=1
    fi
    echo
}

run "课程 JSON 校验" "$PY" Tools/validate_course.py \
    UnityProject/Assets/Content/Courses/animal_001.json

run "课程校验器自测" "$PY" Tools/test_validate_course.py

run "数据库 schema 自测" "$PY" Tools/test_database_schema.py

if [ "$status" -eq 0 ]; then
    echo "全部检查通过"
else
    echo "存在失败的检查"
fi
exit "$status"
