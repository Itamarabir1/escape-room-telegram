-- ============================================================
-- Escape Room Multiplayer – Schema (PostgreSQL)
-- הפרדה מלאה בין קבוצות: סטטוס חידות ב-Group_Tasks (per group).
-- שאלות/חדרים גלובליים; רק סטטוס פתרון וזמן לכל קבוצה.
-- ============================================================
-- Redis (סשן פעיל): group:{group_id}:tasks, current_room, started_at, attempts
-- PostgreSQL: ארכיב קבוע – Groups, Group_Tasks, Answers_Log, זמני סיום
-- ============================================================

-- ------------------------------------------------------------
-- טיפוס enum למשימות
-- ------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE task_type_enum AS ENUM ('puzzle', 'search', 'logic', 'code');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ------------------------------------------------------------
-- 1. Rooms – החדרים במשחק (גלובלי, זהה לכולם)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Rooms (
    room_id     SERIAL PRIMARY KEY,
    room_name   VARCHAR(50) UNIQUE NOT NULL,
    room_order  INTEGER NOT NULL,
    description TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON COLUMN Rooms.room_id IS 'מזהה חדר';

-- ------------------------------------------------------------
-- 2. Tasks – המשימות (גלובלי, זהה לכולם, בלי סטטוס)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Tasks (
    task_id         SERIAL PRIMARY KEY,
    room_id         INTEGER NOT NULL REFERENCES Rooms(room_id) ON DELETE CASCADE ON UPDATE CASCADE,
    task_name       VARCHAR(100),
    description     TEXT,
    task_type       task_type_enum NOT NULL,
    correct_answer  TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 3. Groups – קבוצות טלגרם
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Groups (
    group_id        BIGINT PRIMARY KEY,
    group_name      VARCHAR(100),
    current_room_id INTEGER DEFAULT 1 REFERENCES Rooms(room_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    started_at      TIMESTAMP NULL,
    finished_at     TIMESTAMP NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON COLUMN Groups.group_id IS 'chat_id של טלגרם';
COMMENT ON COLUMN Groups.started_at IS 'מתי התחילו (לחישוב זמן קבוצה)';
COMMENT ON COLUMN Groups.finished_at IS 'מתי סיימו את כל החדרים';

-- ------------------------------------------------------------
-- 4. Players – שחקנים (מזוהים ב-user_id של טלגרם)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Players (
    player_id   BIGINT PRIMARY KEY,
    username    VARCHAR(50),
    joined_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON COLUMN Players.player_id IS 'user_id של טלגרם';

-- ------------------------------------------------------------
-- 5. Group_Players – שחקן שייך לקבוצה
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Group_Players (
    group_id    BIGINT NOT NULL REFERENCES Groups(group_id) ON DELETE CASCADE,
    player_id   BIGINT NOT NULL REFERENCES Players(player_id) ON DELETE CASCADE,
    joined_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, player_id)
);

-- ------------------------------------------------------------
-- 6. Group_Tasks – סטטוס משימה לכל קבוצה (הלב של המערכת)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Group_Tasks (
    group_id     BIGINT NOT NULL REFERENCES Groups(group_id) ON DELETE CASCADE,
    task_id      INTEGER NOT NULL REFERENCES Tasks(task_id) ON DELETE CASCADE,
    solved_by    BIGINT NULL REFERENCES Players(player_id) ON DELETE SET NULL,
    solved_at    TIMESTAMP NULL,
    attempts     INTEGER DEFAULT 0,
    is_solved    BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (group_id, task_id)
);

COMMENT ON COLUMN Group_Tasks.solved_by IS 'player_id שפתר';

-- ------------------------------------------------------------
-- 7. Answers_Log – היסטוריית ניסיונות (per group)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Answers_Log (
    log_id       SERIAL PRIMARY KEY,
    group_id     BIGINT NOT NULL REFERENCES Groups(group_id) ON DELETE CASCADE,
    task_id      INTEGER NOT NULL REFERENCES Tasks(task_id) ON DELETE CASCADE,
    player_id    BIGINT NOT NULL REFERENCES Players(player_id) ON DELETE CASCADE,
    answer_text  TEXT,
    is_correct   BOOLEAN DEFAULT FALSE,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- אינדקסים
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_group_tasks_solved    ON Group_Tasks(group_id, is_solved);
CREATE INDEX IF NOT EXISTS idx_answers_log_group     ON Answers_Log(group_id, task_id);
CREATE INDEX IF NOT EXISTS idx_answers_log_submitted ON Answers_Log(submitted_at);
CREATE INDEX IF NOT EXISTS idx_groups_current_room   ON Groups(current_room_id);
CREATE INDEX IF NOT EXISTS idx_groups_finished_at    ON Groups(finished_at);
