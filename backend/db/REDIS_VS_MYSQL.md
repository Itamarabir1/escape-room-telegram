# Redis vs MySQL – חדר בריחה רב־קבוצות

## עקרון
- **MySQL (או PostgreSQL):** ארכיב קבוע – חדרים, משימות, קבוצות, סטטוס חידות לכל קבוצה, לוג תשובות, זמני סיום.
- **Redis:** סשן פעיל בלבד – מה שצריך מהיר בתוך משחק (סטטוס חידות של הקבוצה, חדר נוכחי, טיימר).

## מפתחות Redis מומלצים (לכל קבוצה)

```
group:{group_id}:tasks        → Hash: task_id → "solved" | "pending"
group:{group_id}:current_room → 1, 2, …
group:{group_id}:started_at   → Unix timestamp (לחישוב זמן קבוצה)
group:{group_id}:task:{task_id}:attempts → 5
```

## לוגיקה כשמישהו שולח תשובה

```python
def handle_answer(group_id, player_id, task_id, answer):
    # 1. בדוק אם התשובה נכונה (מול Tasks.correct_answer)
    correct = check_answer(task_id, answer)

    # 2. שמור ב-Answers_Log תמיד (MySQL)
    insert_answers_log(group_id, task_id, player_id, answer, correct)

    # 3. אם נכון — עדכן Redis (ואז/או Group_Tasks ב-MySQL)
    if correct:
        redis.hset(f"group:{group_id}:tasks", str(task_id), "solved")
        update_group_tasks_mysql(group_id, task_id, player_id)  # ארכיב

        notify_group(group_id, f"✅ {username} פתר את החידה!")

        current_room_id = redis.get(f"group:{group_id}:current_room") or 1
        if all_tasks_solved_in_room(group_id, current_room_id):
            advance_to_next_room(group_id)
            notify_group(group_id, "🚪 החדר נפתח! עוברים לחדר הבא...")
```

## סיום חדר / סיום משחק

```python
def on_room_complete(group_id):
    # שמור סטטוס ל-MySQL (ארכיב)
    save_group_tasks_to_mysql(group_id)
    redis.delete(f"group:{group_id}:*")  # או רק מפתחות הסשן של החדר הנוכחי

def on_game_finished(group_id):
    # זמן קבוצה = now - started_at (מ-Redis או מ-Groups.started_at)
    set Groups.finished_at = NOW(), עדכן זמנים ב-DB
```

## טיימר
זמן הקבוצה נקבע לפי `started_at` (ב-Redis ואז ב-Groups) ו־`finished_at` (ב-Groups). הפרונט שולח את הטיימר הנוכחי; בבקנד אפשר לאמת מול `started_at`.
