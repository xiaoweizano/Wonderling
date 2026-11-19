#!/usr/bin/env python3
"""数据库 schema 自测。

用 Python 内置的 sqlite3 执行 schema_v1.sql，验证：
  - 语法可执行、能建出全部表
  - 外键级联删除生效
  - CHECK 约束真实拦截非法数据
  - 索引存在

Unity 端的 SQLite 插件行为可能略有差异，但约束语义一致；
这里的测试保证 schema 本身没有写错。

用法:
    py Tools/test_database_schema.py
"""
from __future__ import annotations

import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCHEMA = os.path.join(
    ROOT, "UnityProject", "Assets", "Content", "Database", "schema_v1.sql"
)

EXPECTED_TABLES = {
    "child_profiles", "courses", "lesson_progress", "task_records",
    "vocabulary", "learning_mastery", "rewards", "app_settings",
}

EXPECTED_INDEXES = {
    "idx_task_records_lookup",
    "idx_lesson_progress_profile",
    "idx_rewards_profile",
}

NOW = 1_700_000_000_000  # 固定时间戳，避免测试结果随时间变化

results: list[tuple[str, bool, str]] = []


def check(name: str) -> None:
    """装饰器：断言型用例。函数正常返回即通过，抛异常则记录失败。"""
    def wrapper(fn):
        try:
            fn()
            results.append((name, True, ""))
        except AssertionError as exc:
            results.append((name, False, str(exc)))
        except sqlite3.Error as exc:
            results.append((name, False, f"SQLite: {exc}"))
        return fn
    return wrapper


def new_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(open(SCHEMA, encoding="utf-8").read())
    return conn


def expect_error(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> None:
    """断言语句必须被约束拒绝。"""
    try:
        conn.execute(sql, params)
    except sqlite3.IntegrityError:
        return
    raise AssertionError(f"约束未生效，语句被执行成功: {sql.strip()[:60]}")


def seed_profile(conn: sqlite3.Connection, profile_id: str = "p1") -> None:
    conn.execute(
        "INSERT INTO child_profiles (id, display_name, created_at, updated_at) "
        "VALUES (?, NULL, ?, ?)",
        (profile_id, NOW, NOW),
    )


def seed_course(conn: sqlite3.Connection, course_id: str = "animal_001") -> None:
    conn.execute(
        "INSERT INTO courses (course_id, schema_version, content_version, title) "
        "VALUES (?, 1, '0.1.0', 'Meet the Animals')",
        (course_id,),
    )


@check("schema 可执行并建出全部表")
def _() -> None:
    conn = new_db()
    tables = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    missing = EXPECTED_TABLES - tables
    assert not missing, f"缺少表: {missing}"
    conn.close()


@check("user_version 被设为 1")
def _() -> None:
    conn = new_db()
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version == 1, f"user_version={version}"
    conn.close()


@check("三个查询索引均存在")
def _() -> None:
    conn = new_db()
    indexes = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
    }
    missing = EXPECTED_INDEXES - indexes
    assert not missing, f"缺少索引: {missing}"
    conn.close()


@check("外键默认开启")
def _() -> None:
    conn = new_db()
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.close()


@check("删除档案时级联删除进度与任务记录")
def _() -> None:
    conn = new_db()
    seed_profile(conn)
    seed_course(conn)
    conn.execute(
        "INSERT INTO lesson_progress (id, profile_id, course_id, current_step_id, "
        "status, stars, started_at, updated_at) VALUES "
        "('lp1', 'p1', 'animal_001', 'teach_cat', 'in_progress', 0, ?, ?)",
        (NOW, NOW),
    )
    conn.execute(
        "INSERT INTO task_records (id, profile_id, course_id, step_id, task_type, "
        "created_at) VALUES ('tr1', 'p1', 'animal_001', 'listen_cat', "
        "'listening_choice', ?)",
        (NOW,),
    )
    conn.execute("DELETE FROM child_profiles WHERE id = 'p1'")
    remaining = conn.execute("SELECT COUNT(*) FROM lesson_progress").fetchone()[0]
    tasks = conn.execute("SELECT COUNT(*) FROM task_records").fetchone()[0]
    assert remaining == 0 and tasks == 0, \
        f"级联删除失败: progress={remaining}, tasks={tasks}"
    conn.close()


@check("同一档案同一课程只能有一条进度记录")
def _() -> None:
    conn = new_db()
    seed_profile(conn)
    seed_course(conn)
    sql = ("INSERT INTO lesson_progress (id, profile_id, course_id, current_step_id, "
           "status, stars, started_at, updated_at) VALUES (?, 'p1', 'animal_001', "
           "'teach_cat', 'in_progress', 0, ?, ?)")
    conn.execute(sql, ("lp1", NOW, NOW))
    expect_error(conn, sql, ("lp2", NOW, NOW))
    conn.close()


@check("星星数超出 0..3 被拒绝")
def _() -> None:
    conn = new_db()
    seed_profile(conn)
    seed_course(conn)
    expect_error(
        conn,
        "INSERT INTO lesson_progress (id, profile_id, course_id, current_step_id, "
        "status, stars, started_at, updated_at) VALUES "
        "('lp1', 'p1', 'animal_001', 'teach_cat', 'in_progress', 5, ?, ?)",
        (NOW, NOW),
    )
    conn.close()


@check("未知进度状态被拒绝")
def _() -> None:
    conn = new_db()
    seed_profile(conn)
    seed_course(conn)
    expect_error(
        conn,
        "INSERT INTO lesson_progress (id, profile_id, course_id, current_step_id, "
        "status, stars, started_at, updated_at) VALUES "
        "('lp1', 'p1', 'animal_001', 'teach_cat', 'teleported', 0, ?, ?)",
        (NOW, NOW),
    )
    conn.close()


@check("correct_count 不得超过 seen_count")
def _() -> None:
    conn = new_db()
    seed_profile(conn)
    expect_error(
        conn,
        "INSERT INTO vocabulary (profile_id, word_id, last_seen_at, seen_count, "
        "correct_count) VALUES ('p1', 'cat', ?, 1, 3)",
        (NOW,),
    )
    conn.close()


@check("掌握度超出 0..1 被拒绝")
def _() -> None:
    conn = new_db()
    seed_profile(conn)
    expect_error(
        conn,
        "INSERT INTO learning_mastery (profile_id, word_id, mastery_level, "
        "last_reviewed_at) VALUES ('p1', 'cat', 1.5, ?)",
        (NOW,),
    )
    conn.close()


@check("task_records.is_correct 可为 NULL（跟读不判定对错）")
def _() -> None:
    conn = new_db()
    seed_profile(conn)
    conn.execute(
        "INSERT INTO task_records (id, profile_id, course_id, step_id, task_type, "
        "is_correct, created_at) VALUES ('tr1', 'p1', 'animal_001', 'repeat_cat', "
        "'repeat_speech', NULL, ?)",
        (NOW,),
    )
    value = conn.execute(
        "SELECT is_correct FROM task_records WHERE id = 'tr1'"
    ).fetchone()[0]
    assert value is None, f"is_correct={value!r}，应为 NULL"
    conn.close()


@check("is_correct 只接受 0/1/NULL")
def _() -> None:
    conn = new_db()
    seed_profile(conn)
    expect_error(
        conn,
        "INSERT INTO task_records (id, profile_id, course_id, step_id, task_type, "
        "is_correct, created_at) VALUES ('tr1', 'p1', 'animal_001', 'listen_cat', "
        "'listening_choice', 2, ?)",
        (NOW,),
    )
    conn.close()


@check("未知奖励类型被拒绝")
def _() -> None:
    conn = new_db()
    seed_profile(conn)
    expect_error(
        conn,
        "INSERT INTO rewards (id, profile_id, reward_type, reward_id, earned_at) "
        "VALUES ('r1', 'p1', 'money', 'gold', ?)",
        (NOW,),
    )
    conn.close()


@check("引用不存在的课程被拒绝")
def _() -> None:
    conn = new_db()
    seed_profile(conn)
    expect_error(
        conn,
        "INSERT INTO lesson_progress (id, profile_id, course_id, current_step_id, "
        "status, stars, started_at, updated_at) VALUES "
        "('lp1', 'p1', 'ghost_course', 'teach_cat', 'in_progress', 0, ?, ?)",
        (NOW, NOW),
    )
    conn.close()


failed = [r for r in results if not r[1]]
for name, ok, detail in results:
    print(f"{'通过' if ok else '失败'}  {name}")
    if not ok and detail:
        print(f"      {detail}")

print(f"\n合计: {len(results) - len(failed)} 通过, {len(failed)} 失败")
sys.exit(0 if not failed else 1)
