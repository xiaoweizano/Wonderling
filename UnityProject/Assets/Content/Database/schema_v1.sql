-- Wonder English 本地数据库结构，版本 1。
--
-- 只保存课程进度与必要学习统计；课程静态内容由 JSON 与资源包管理，
-- 不在这里重复存储（见文档 06 第 1 节）。
--
-- 时间统一使用 UTC epoch 毫秒，整个项目保持一致。
-- 升级时递增 PRAGMA user_version，并在 DatabaseMigrator 中追加有序迁移。

PRAGMA user_version = 1;
PRAGMA foreign_keys = ON;

-- 儿童档案。不要求真实姓名、生日或精确位置。
CREATE TABLE child_profiles (
    id           TEXT    PRIMARY KEY NOT NULL,
    display_name TEXT    NULL,
    created_at   INTEGER NOT NULL,
    updated_at   INTEGER NOT NULL
);

-- 已安装课程的元数据。is_available=0 表示内容包存在但暂不可用，
-- 用于内容更新失败时保留记录而不删除历史进度。
CREATE TABLE courses (
    course_id       TEXT    PRIMARY KEY NOT NULL,
    schema_version  INTEGER NOT NULL,
    content_version TEXT    NOT NULL,
    title           TEXT    NOT NULL,
    is_available    INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0, 1))
);

-- 课程进度。同一档案对同一课程只保留一条当前进度记录，
-- 重复学习时覆盖而非累积（学习历史在 task_records 中）。
CREATE TABLE lesson_progress (
    id             TEXT    PRIMARY KEY NOT NULL,
    profile_id     TEXT    NOT NULL,
    course_id      TEXT    NOT NULL,
    current_step_id TEXT   NOT NULL,
    status         TEXT    NOT NULL
                   CHECK (status IN ('not_started', 'in_progress',
                                     'paused', 'completed', 'abandoned')),
    stars          INTEGER NOT NULL DEFAULT 0 CHECK (stars BETWEEN 0 AND 3),
    started_at     INTEGER NOT NULL,
    completed_at   INTEGER NULL,
    updated_at     INTEGER NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES child_profiles (id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses (course_id) ON DELETE RESTRICT,
    UNIQUE (profile_id, course_id)
);

-- 单次任务执行记录。is_correct 允许 NULL：跟读这类任务不判定对错，
-- 只记录是否完成，不能把"未判定"混同为"错误"。
CREATE TABLE task_records (
    id           TEXT    PRIMARY KEY NOT NULL,
    profile_id   TEXT    NOT NULL,
    course_id    TEXT    NOT NULL,
    step_id      TEXT    NOT NULL,
    task_type    TEXT    NOT NULL,
    attempts     INTEGER NOT NULL DEFAULT 1 CHECK (attempts >= 1),
    is_completed INTEGER NOT NULL DEFAULT 1 CHECK (is_completed IN (0, 1)),
    is_correct   INTEGER NULL CHECK (is_correct IS NULL OR is_correct IN (0, 1)),
    elapsed_ms   INTEGER NOT NULL DEFAULT 0 CHECK (elapsed_ms >= 0),
    created_at   INTEGER NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES child_profiles (id) ON DELETE CASCADE
);

-- 词汇接触统计，用于后续自适应复习。
CREATE TABLE vocabulary (
    profile_id   TEXT    NOT NULL,
    word_id      TEXT    NOT NULL,
    last_seen_at INTEGER NOT NULL,
    seen_count   INTEGER NOT NULL DEFAULT 0 CHECK (seen_count >= 0),
    correct_count INTEGER NOT NULL DEFAULT 0 CHECK (correct_count >= 0),
    PRIMARY KEY (profile_id, word_id),
    FOREIGN KEY (profile_id) REFERENCES child_profiles (id) ON DELETE CASCADE,
    CHECK (correct_count <= seen_count)
);

-- 掌握度。mastery_level 为 0..1 的连续值，与 seen/correct 计数分开保存，
-- 因为掌握度由自适应算法计算，计数只记录原始事实。
CREATE TABLE learning_mastery (
    profile_id       TEXT    NOT NULL,
    word_id          TEXT    NOT NULL,
    mastery_level    REAL    NOT NULL DEFAULT 0
                     CHECK (mastery_level BETWEEN 0 AND 1),
    last_reviewed_at INTEGER NOT NULL,
    PRIMARY KEY (profile_id, word_id),
    FOREIGN KEY (profile_id) REFERENCES child_profiles (id) ON DELETE CASCADE
);

CREATE TABLE rewards (
    id          TEXT PRIMARY KEY NOT NULL,
    profile_id  TEXT NOT NULL,
    reward_type TEXT NOT NULL
                CHECK (reward_type IN ('star', 'sticker', 'badge')),
    reward_id   TEXT NOT NULL,
    earned_at   INTEGER NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES child_profiles (id) ON DELETE CASCADE
);

CREATE TABLE app_settings (
    key        TEXT PRIMARY KEY NOT NULL,
    value      TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);

-- 索引：文档 06 第 3 节要求

-- 按档案+课程+时间查询任务记录（家长查看学习历史的主路径）
CREATE INDEX idx_task_records_lookup
    ON task_records (profile_id, course_id, created_at);

CREATE INDEX idx_lesson_progress_profile
    ON lesson_progress (profile_id, updated_at);

CREATE INDEX idx_rewards_profile
    ON rewards (profile_id, earned_at);
