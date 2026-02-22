-- ============================================================
-- Escape Room Multiplayer – Schema (MySQL)
-- טבלאות: Rooms, Players, Tasks, Task_Answers
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------
-- 1. Rooms – חדרים במשחק
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_name VARCHAR(50) UNIQUE NOT NULL,
    room_order INT NOT NULL,
    room_description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 2. Players – שחקנים (מקושרים לחדר נוכחי)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Players (
    player_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    group_name VARCHAR(50),
    joined_at DATETIME NOT NULL,
    current_room_id INT,
    total_speed INT DEFAULT 0,
    UNIQUE KEY uq_player_group (username, group_name),
    FOREIGN KEY (current_room_id) REFERENCES Rooms(room_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 3. Tasks – משימות בתוך חדר
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    task_name VARCHAR(50),
    task_description TEXT,
    task_type ENUM('puzzle','search','logic','code') NOT NULL,
    task_status ENUM('pending','done') DEFAULT 'pending',
    assigned_to INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES Rooms(room_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES Players(player_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 4. Task_Answers – היסטוריית פתרונות
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Task_Answers (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    player_id INT NOT NULL,
    answer_text TEXT,
    submitted_at DATETIME NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    time_taken INT,
    FOREIGN KEY (task_id) REFERENCES Tasks(task_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (player_id) REFERENCES Players(player_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- אינדקסים לשיפור ביצועים
-- ------------------------------------------------------------
CREATE INDEX idx_players_current_room ON Players(current_room_id);
CREATE INDEX idx_players_joined_at ON Players(joined_at);
CREATE INDEX idx_tasks_room_status ON Tasks(room_id, task_status);
CREATE INDEX idx_task_answers_task_player ON Task_Answers(task_id, player_id);
CREATE INDEX idx_task_answers_submitted ON Task_Answers(submitted_at);
