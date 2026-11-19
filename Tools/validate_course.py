#!/usr/bin/env python3
"""课程 JSON 校验器。

在 Unity 运行时校验之外，提供一个可在命令行/CI 中独立运行的校验工具，
让课程内容在提交前就能发现问题，不必等到编辑器里加载失败。

检查分两层：
  1. 结构校验 —— 对照 lesson.schema.json（本文件实现了所需子集，不依赖第三方库）
  2. 语义校验 —— 文档 03 第 5 节要求的引用完整性，JSON Schema 表达不了

用法:
    py validate_course.py <课程 JSON> [--schema <schema.json>] [--assets <资源目录>]

退出码: 0 全部通过；1 存在错误
"""
from __future__ import annotations

import json
import os
import re
import sys

MAX_REPORTED_ERRORS = 50

ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
WORD_PATTERN = re.compile(r"^[a-z]+$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

SUPPORTED_SCHEMA_VERSION = 1

STEP_TYPES = {
    "teacher_intro",
    "word_learning",
    "listening_choice",
    "repeat_speech",
    "drag_match",
    "memory_cards",
    "challenge",
    "level_complete",
}

TEACHER_ACTIONS = {
    "Idle", "Greeting", "Speaking", "Listening",
    "Thinking", "Encourage", "Celebrate", "Guide",
}

ASSET_TYPES = {"audio", "sprite", "prefab", "texture", "animation"}

# 每种步骤类型的必填字段（文档 03 第 5 节：必填参数按任务类型校验）
REQUIRED_BY_TYPE = {
    "teacher_intro": ["teacherAction"],
    "word_learning": ["word", "imageId", "audioId"],
    "listening_choice": ["audioId", "options", "correctAnswer"],
    "repeat_speech": ["word", "audioId"],
    "drag_match": ["pairs"],
    "memory_cards": ["cardIds"],
    "challenge": ["subSteps"],
    "level_complete": ["reward"],
}

# 这些字段的值是资源 ID，必须存在于资源清单
ASSET_REFERENCE_FIELDS = ("audioId", "introAudioId", "imageId")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def dump(self) -> int:
        for w in self.warnings:
            print(f"警告: {w}")
        shown = self.errors[:MAX_REPORTED_ERRORS]
        for e in shown:
            print(f"错误: {e}")
        if len(self.errors) > MAX_REPORTED_ERRORS:
            print(f"... 另有 {len(self.errors) - MAX_REPORTED_ERRORS} 条错误未显示")
        print(f"\n合计: {len(self.errors)} 个错误, {len(self.warnings)} 个警告")
        return 0 if not self.errors else 1


def load_json(path: str, report: Report) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        report.error(f"文件不存在: {path}")
    except json.JSONDecodeError as exc:
        report.error(f"JSON 语法错误 {path}:{exc.lineno}:{exc.colno} — {exc.msg}")
    return None


def check_required(obj: dict, fields: list[str], where: str, report: Report) -> None:
    for field in fields:
        if field not in obj or obj[field] is None:
            report.error(f"{where}: 缺少必填字段 '{field}'")


def check_top_level(course: dict, report: Report) -> None:
    check_required(
        course,
        ["schemaVersion", "courseId", "title", "worldId",
         "ageRange", "durationMinutes", "objectives", "steps"],
        "课程", report,
    )

    version = course.get("schemaVersion")
    if version != SUPPORTED_SCHEMA_VERSION:
        # 未知版本必须直接拒绝，不能尝试兼容解析
        report.error(
            f"schemaVersion={version} 不受支持，当前引擎只接受 {SUPPORTED_SCHEMA_VERSION}"
        )

    for field in ("courseId", "worldId"):
        value = course.get(field)
        if isinstance(value, str) and not ID_PATTERN.match(value):
            report.error(f"{field}='{value}' 不符合命名规则（小写字母开头，仅含小写字母/数字/下划线）")

    content_version = course.get("contentVersion")
    if content_version is not None and not VERSION_PATTERN.match(str(content_version)):
        report.error(f"contentVersion='{content_version}' 应为 x.y.z 形式")

    if course.get("ageRange") not in (None, "3-6"):
        report.error(f"ageRange='{course.get('ageRange')}' 当前只支持 '3-6'")

    duration = course.get("durationMinutes")
    if isinstance(duration, (int, float)) and not 0 < duration <= 15:
        report.error(f"durationMinutes={duration} 超出范围 (0, 15]")

    objectives = course.get("objectives")
    if isinstance(objectives, list) and not objectives:
        report.error("objectives 不能为空")


def collect_assets(course: dict, report: Report) -> dict[str, dict]:
    """返回 assetId -> 资源描述。重复 ID 视为错误。"""
    assets: dict[str, dict] = {}
    raw = course.get("assets") or []
    if not isinstance(raw, list):
        report.error("assets 必须是数组")
        return assets

    for index, asset in enumerate(raw):
        where = f"assets[{index}]"
        if not isinstance(asset, dict):
            report.error(f"{where}: 必须是对象")
            continue
        check_required(asset, ["assetId", "location", "assetType"], where, report)
        asset_id = asset.get("assetId")
        if not isinstance(asset_id, str) or not ID_PATTERN.match(asset_id):
            report.error(f"{where}: assetId='{asset_id}' 不符合命名规则")
            continue
        if asset_id in assets:
            report.error(f"{where}: assetId '{asset_id}' 重复")
            continue
        if asset.get("assetType") not in ASSET_TYPES:
            report.error(f"{where}: assetType='{asset.get('assetType')}' 不是已知类型")
        assets[asset_id] = asset
    return assets


def check_steps(course: dict, assets: dict[str, dict], asset_dir: str | None,
                report: Report) -> dict[str, dict]:
    steps: dict[str, dict] = {}
    raw = course.get("steps") or []
    if not isinstance(raw, list) or not raw:
        report.error("steps 必须是非空数组")
        return steps

    for index, step in enumerate(raw):
        where = f"steps[{index}]"
        if not isinstance(step, dict):
            report.error(f"{where}: 必须是对象")
            continue

        check_required(step, ["stepId", "type"], where, report)
        step_id = step.get("stepId")
        if not isinstance(step_id, str) or not ID_PATTERN.match(step_id):
            report.error(f"{where}: stepId='{step_id}' 不符合命名规则")
            continue
        if step_id in steps:
            report.error(f"{where}: stepId '{step_id}' 重复")
            continue

        step_type = step.get("type")
        if step_type not in STEP_TYPES:
            report.error(f"{where} ({step_id}): 未知 type='{step_type}'")
            steps[step_id] = step
            continue

        where = f"{where} ({step_id})"
        for field in REQUIRED_BY_TYPE[step_type]:
            if field not in step or step[field] is None:
                report.error(f"{where}: type={step_type} 缺少必填字段 '{field}'")

        _check_teacher_action(step, where, report)

        if step_type == "level_complete":
            _check_reward(step, where, report)
        if step_type == "listening_choice":
            _check_listening_options(step, where, report)
        if step_type == "drag_match":
            _check_pairs(step, where, report)
        if step_type == "memory_cards":
            _check_cards(step, where, report)
        if step_type == "challenge":
            _check_sub_steps(step, where, report)

        _check_asset_references(step, step_id, assets, asset_dir, report)
        _check_retry_policy(step, where, report)

        steps[step_id] = step
    return steps


def _check_teacher_action(step: dict, where: str, report: Report) -> None:
    action = step.get("teacherAction")
    if action is not None and action not in TEACHER_ACTIONS:
        report.error(f"{where}: teacherAction='{action}' 不是已知语义动作")


def _check_reward(step: dict, where: str, report: Report) -> None:
    reward = step.get("reward")
    if not isinstance(reward, dict):
        report.error(f"{where}: reward 必须是对象")
        return
    stars = reward.get("stars")
    if not isinstance(stars, int) or not 0 <= stars <= 3:
        report.error(f"{where}: reward.stars={stars} 必须在 0..3 之间")


def _check_listening_options(step: dict, where: str, report: Report) -> None:
    options = step.get("options")
    correct = step.get("correctAnswer")
    if not isinstance(options, list):
        report.error(f"{where}: options 必须是数组")
        return
    # 幼儿一次最多呈现 4 个选项
    if not 2 <= len(options) <= 4:
        report.error(f"{where}: options 数量为 {len(options)}，必须在 2..4 之间")
    if len(set(options)) != len(options):
        report.error(f"{where}: options 存在重复项")
    if correct not in options:
        report.error(f"{where}: correctAnswer='{correct}' 不在 options 中")


def _check_pairs(step: dict, where: str, report: Report) -> None:
    pairs = step.get("pairs")
    if not isinstance(pairs, list):
        report.error(f"{where}: pairs 必须是数组")
        return
    if len(pairs) < 2:
        report.error(f"{where}: pairs 至少需要 2 组")
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict):
            report.error(f"{where}: pairs[{index}] 必须是对象")
            continue
        for field in ("leftId", "rightId"):
            if not pair.get(field):
                report.error(f"{where}: pairs[{index}] 缺少 '{field}'")


def _check_cards(step: dict, where: str, report: Report) -> None:
    cards = step.get("cardIds")
    if not isinstance(cards, list):
        report.error(f"{where}: cardIds 必须是数组")
        return
    if not 4 <= len(cards) <= 8:
        report.error(f"{where}: cardIds 数量为 {len(cards)}，必须在 4..8 之间")
    if len(cards) % 2 != 0:
        # 记忆翻牌必须成对，否则必然有一张永远配不上
        report.error(f"{where}: cardIds 数量 {len(cards)} 为奇数，翻牌无法全部配对")
    if len(set(cards)) != len(cards):
        report.error(f"{where}: cardIds 存在重复项，会导致同名卡片无法区分")


def _check_sub_steps(step: dict, where: str, report: Report) -> None:
    sub_steps = step.get("subSteps")
    if not isinstance(sub_steps, list) or not sub_steps:
        report.error(f"{where}: subSteps 必须是非空数组")


def _check_asset_references(step: dict, step_id: str, assets: dict[str, dict],
                            asset_dir: str | None, report: Report) -> None:
    for field in ASSET_REFERENCE_FIELDS:
        asset_id = step.get(field)
        if asset_id is None:
            continue
        if asset_id not in assets:
            report.error(f"步骤 '{step_id}': {field}='{asset_id}' 不在资源清单中")
            continue
        if asset_dir is not None:
            _check_asset_file(assets[asset_id], step_id, field, asset_dir, report)

    options = step.get("options")
    if isinstance(options, list):
        for option in options:
            if option not in assets:
                report.error(f"步骤 '{step_id}': options 中的 '{option}' 不在资源清单中")

    for field in ("leftId", "rightId"):
        for index, pair in enumerate(step.get("pairs") or []):
            if isinstance(pair, dict):
                value = pair.get(field)
                if value and value not in assets:
                    report.error(
                        f"步骤 '{step_id}': pairs[{index}].{field}='{value}' 不在资源清单中"
                    )

    for index, card in enumerate(step.get("cardIds") or []):
        if card not in assets:
            report.error(f"步骤 '{step_id}': cardIds[{index}]='{card}' 不在资源清单中")


def _check_asset_file(asset: dict, step_id: str, field: str, asset_dir: str,
                      report: Report) -> None:
    location = asset.get("location", "")
    # 在第一阶段资源可能尚未制作，缺失只报警告，不阻断课程配置校验
    found = any(
        os.path.exists(os.path.join(asset_dir, location + ext))
        for ext in (".wav", ".ogg", ".mp3", ".png", ".jpg", ".prefab", ".asset")
    )
    if not found:
        report.warn(f"步骤 '{step_id}': {field}='{asset['assetId']}' 的资源文件尚未提供 ({location})")


def _check_retry_policy(step: dict, where: str, report: Report) -> None:
    policy = step.get("retryPolicy")
    if policy is None:
        return
    if not isinstance(policy, dict):
        report.error(f"{where}: retryPolicy 必须是对象")
        return
    attempts = policy.get("maxAttempts")
    if not isinstance(attempts, int) or not 1 <= attempts <= 5:
        report.error(f"{where}: retryPolicy.maxAttempts={attempts} 必须在 1..5 之间")
    # 项目原则：答错不得阻断课程
    if attempts is not None:
        allow_skip = policy.get("allowSkip", True)
        if not allow_skip:
            report.warn(
                f"{where}: retryPolicy.allowSkip=false，"
                f"项目要求答错不得阻断课程，请确认这是有意为之"
            )


def check_jumps(steps: dict[str, dict], report: Report) -> None:
    """校验所有跳转目标存在，并检查可达性与无限循环。"""
    jump_fields = ("next", "onCorrect", "onIncorrect")

    for step_id, step in steps.items():
        for field in jump_fields:
            if field not in step:
                continue
            target = step[field]
            if target is None:
                continue
            if target not in steps:
                report.error(f"步骤 '{step_id}': {field}='{target}' 引用了不存在的步骤")

        for sub in step.get("subSteps") or []:
            if sub not in steps:
                report.error(f"步骤 '{step_id}': subSteps 中的 '{sub}' 不存在")

    if not steps:
        return

    # 从第一步开始做可达性检查（文档 03 第 5 节：不能有未声明的孤立步骤）
    root = next(iter(steps))
    reachable: set[str] = set()
    stack = [root]
    while stack:
        current = stack.pop()
        if current in reachable or current not in steps:
            continue
        reachable.add(current)
        step = steps[current]
        for field in jump_fields:
            target = step.get(field)
            if isinstance(target, str):
                stack.append(target)
        for sub in step.get("subSteps") or []:
            stack.append(sub)

    for step_id in steps:
        if step_id not in reachable:
            report.error(f"步骤 '{step_id}' 从课程起点不可达")

    _check_cycles(steps, report)


def _check_cycles(steps: dict[str, dict], report: Report) -> None:
    """检测无退出条件的循环。

    复习类循环是合法的，但必须有次数上限。这里把带 retryPolicy.maxAttempts
    的步骤视为合法循环节点，其余成环则报告。
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {sid: WHITE for sid in steps}
    path: list[str] = []

    def visit(node: str) -> None:
        color[node] = GRAY
        path.append(node)
        step = steps[node]
        for field in ("next", "onCorrect", "onIncorrect"):
            target = step.get(field)
            if not isinstance(target, str) or target not in steps:
                continue
            if color[target] == GRAY:
                cycle = path[path.index(target):] + [target]
                bounded = all(
                    (steps[n].get("retryPolicy") or {}).get("maxAttempts")
                    for n in cycle[:-1]
                    if n in steps
                )
                if not bounded:
                    report.warn(
                        "存在无次数上限的跳转循环: " + " -> ".join(cycle)
                    )
            elif color[target] == WHITE:
                visit(target)
        path.pop()
        color[node] = BLACK

    for step_id in steps:
        if color[step_id] == WHITE:
            visit(step_id)


def main() -> int:
    args = [a for a in sys.argv[1:]]
    if not args:
        print(__doc__)
        return 2

    asset_dir = None
    if "--assets" in args:
        index = args.index("--assets")
        asset_dir = args[index + 1]
        del args[index:index + 2]
    if "--schema" in args:
        index = args.index("--schema")
        del args[index:index + 2]

    course_path = args[0]
    report = Report()
    course = load_json(course_path, report)
    if course is None:
        return report.dump()

    print(f"校验 {course_path}")
    check_top_level(course, report)
    assets = collect_assets(course, report)
    steps = check_steps(course, assets, asset_dir, report)
    check_jumps(steps, report)
    return report.dump()


if __name__ == "__main__":
    sys.exit(main())
