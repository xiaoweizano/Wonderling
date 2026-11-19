#!/usr/bin/env python3
"""课程校验器的自测。

修正校验器时先跑这个，确认没有把已有的检查改坏。
每一条用例都对应文档 03 第 5 节列出的一条规则。

用法:
    py Tools/test_validate_course.py
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VALIDATOR = os.path.join(HERE, "validate_course.py")
COURSE = os.path.join(ROOT, "UnityProject", "Assets", "Content", "Courses", "animal_001.json")


def run_validator(course: dict) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as fh:
        json.dump(course, fh, ensure_ascii=False)
        path = fh.name
    try:
        proc = subprocess.run(
            [sys.executable, VALIDATOR, path],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        return proc.returncode, proc.stdout
    finally:
        os.unlink(path)


def load_course() -> dict:
    with open(COURSE, encoding="utf-8") as fh:
        return json.load(fh)


def find_step(course: dict, step_id: str) -> dict:
    for step in course["steps"]:
        if step["stepId"] == step_id:
            return step
    raise KeyError(step_id)


results: list[tuple[str, bool, str]] = []


def case(name: str, mutate, expect_fail: bool, expect_text: str = "") -> None:
    course = copy.deepcopy(load_course())
    mutate(course)
    code, output = run_validator(course)
    ok = (code != 0) == expect_fail and (expect_text in output if expect_text else True)
    results.append((name, ok, output.strip().splitlines()[-1] if output.strip() else ""))


# —— 基线：当前课程必须完全通过 ——
def _noop(course: dict) -> None:
    pass


case("原始课程通过校验", _noop, expect_fail=False)

# —— 文档 03 第 5 节：未知 schemaVersion 应拒绝加载 ——
case("未知 schemaVersion 被拒绝",
     lambda c: c.__setitem__("schemaVersion", 99),
     expect_fail=True, expect_text="schemaVersion")

# —— 文档 03 第 5 节：每个 stepId 唯一 ——
case("重复 stepId 被拒绝",
     lambda c: c["steps"].append(copy.deepcopy(c["steps"][0])),
     expect_fail=True, expect_text="重复")

# —— 文档 03 第 5 节：next 必须引用存在的 stepId ——
def _break_jump(c: dict) -> None:
    find_step(c, "teach_cat")["next"] = "no_such_step"


case("坏跳转被拒绝", _break_jump, expect_fail=True, expect_text="不存在")

# —— 文档 03 第 5 节：资源 ID 必须存在于资源清单 ——
def _missing_asset(c: dict) -> None:
    find_step(c, "teach_cat")["imageId"] = "animal_unknown"


case("引用不存在的资源被拒绝", _missing_asset, expect_fail=True, expect_text="不在资源清单")

# —— 文档 03 第 5 节：必填参数按任务类型校验 ——
def _drop_required(c: dict) -> None:
    del find_step(c, "listen_cat")["options"]


case("缺少任务类型必填字段被拒绝", _drop_required, expect_fail=True, expect_text="缺少必填字段")

# —— 正确答案必须在选项内 ——
def _wrong_answer(c: dict) -> None:
    step = find_step(c, "listen_cat")
    step["options"] = ["animal_cat", "animal_dog"]
    step["correctAnswer"] = "animal_duck"


case("正确答案不在选项中被拒绝", _wrong_answer, expect_fail=True, expect_text="不在 options 中")

# —— 记忆翻牌必须成对 ——
def _odd_cards(c: dict) -> None:
    find_step(c, "memory_game")["cardIds"] = find_step(c, "memory_game")["cardIds"][:5]


case("翻牌数量为奇数被拒绝", _odd_cards, expect_fail=True, expect_text="奇数")

# —— 幼儿选项数量上限 ——
def _too_many_options(c: dict) -> None:
    step = find_step(c, "listen_cat")
    step["options"] = ["animal_cat", "animal_dog", "animal_duck", "card_cat_a", "card_dog_a"]


case("选项超过 4 个被拒绝", _too_many_options, expect_fail=True, expect_text="2..4")

# —— 从起点不可达 ——
def _orphan(c: dict) -> None:
    c["steps"].append({
        "stepId": "orphan_step",
        "type": "teacher_intro",
        "teacherAction": "Idle",
        "next": "welcome",
    })


case("孤立步骤被拒绝", _orphan, expect_fail=True, expect_text="不可达")

# —— 未知步骤类型 ——
def _unknown_type(c: dict) -> None:
    find_step(c, "teach_cat")["type"] = "teleport"


case("未知步骤类型被拒绝", _unknown_type, expect_fail=True, expect_text="未知 type")

# —— 未知老师语义动作 ——
def _unknown_action(c: dict) -> None:
    find_step(c, "welcome")["teacherAction"] = "Dance"


case("未知老师动作被拒绝", _unknown_action, expect_fail=True, expect_text="teacherAction")

# —— JSON 语法错误 ——
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
    fh.write('{"courseId": "broken", ')
    broken_path = fh.name
try:
    proc = subprocess.run(
        [sys.executable, VALIDATOR, broken_path],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    results.append(("语法错误的 JSON 被拒绝", proc.returncode != 0 and "语法错误" in proc.stdout, ""))
finally:
    os.unlink(broken_path)

# —— 输出 ——
failed = [r for r in results if not r[1]]
for name, ok, detail in results:
    print(f"{'通过' if ok else '失败'}  {name}")
    if not ok and detail:
        print(f"      {detail}")

print(f"\n合计: {len(results) - len(failed)} 通过, {len(failed)} 失败")
sys.exit(0 if not failed else 1)
