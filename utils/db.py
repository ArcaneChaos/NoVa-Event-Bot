import sqlite3
import os

DB_PATH = "db/nova.db"
os.makedirs("db", exist_ok=True)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            datetime_utc TEXT NOT NULL,
            creator TEXT
        );

        CREATE TABLE IF NOT EXISTS rsvps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            player_name TEXT NOT NULL,
            discord_id TEXT,
            response TEXT CHECK(response IN ('yes', 'no')),
            reminder_minutes INTEGER DEFAULT NULL,
            UNIQUE(event_id, player_name),
            FOREIGN KEY (event_id) REFERENCES events(id)
        );

        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL UNIQUE,
            timezone TEXT NOT NULL,
            availability_start TEXT,
            availability_end TEXT
        );
        """)
        conn.commit()

def get_all_events():
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM events ORDER BY datetime_utc DESC")
        return [dict(row) for row in cursor.fetchall()]

def count_rsvps(event_id: int) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM rsvps WHERE event_id = ? AND response = 'yes'", (event_id,))
        return cursor.fetchone()[0]

def get_player_timezone(player_name: str) -> str:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT timezone FROM players WHERE player_name = ?", (player_name,))
        row = cursor.fetchone()
        return row["timezone"] if row else ""

def get_event_by_id(event_id: int) -> dict:
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}

def update_event(event_id: int, title: str, time_str: str, desc: str):
    with get_connection() as conn:
        conn.execute("""UPDATE events SET title = ?, datetime_utc = ?, description = ? WHERE id = ?""",
                     (title, time_str, desc, event_id))
        conn.commit()

def set_player_time(player_name: str, timezone: str, start: str, end: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO players (player_name, timezone, availability_start, availability_end)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(player_name) DO UPDATE SET
              timezone=excluded.timezone,
              availability_start=excluded.availability_start,
              availability_end=excluded.availability_end
        """, (player_name, timezone, start, end))
        conn.commit()

def get_rsvp(event_id: int, player_name: str) -> str:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT response FROM rsvps WHERE event_id = ? AND player_name = ?",
            (event_id, player_name))
        row = cursor.fetchone()
        return row["response"] if row else ""

def set_rsvp(event_id: int, player_name: str, response: str, reminder_minutes: int = None, discord_id: str = None):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO rsvps (event_id, player_name, discord_id, response, reminder_minutes)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(event_id, player_name) DO UPDATE SET
              response = excluded.response,
              reminder_minutes = excluded.reminder_minutes,
              discord_id = excluded.discord_id
        """, (event_id, player_name, discord_id, response, reminder_minutes))
        conn.commit()

def set_reminder(event_id: int, player_name: str, minutes: int):
    with get_connection() as conn:
        conn.execute("""
            UPDATE rsvps SET reminder_minutes = ?
            WHERE event_id = ? AND player_name = ?
        """, (minutes, event_id, player_name))
        conn.commit()

def get_reminders_due(event_id: int):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT player_name, discord_id, reminder_minutes FROM rsvps
            WHERE event_id = ? AND response = 'yes' AND reminder_minutes IS NOT NULL
        """, (event_id,))
        return [dict(row) for row in cursor.fetchall()]

def clear_reminder(event_id: int, player_name: str):
    with get_connection() as conn:
        conn.execute("""
            UPDATE rsvps SET reminder_minutes = NULL
            WHERE event_id = ? AND player_name = ?
        """, (event_id, player_name))
        conn.commit()

def create_event(title: str, utc_time: str, desc: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO events (title, datetime_utc, description, creator)
            VALUES (?, ?, ?, 'admin')
        """, (title, utc_time, desc))
        conn.commit()

def get_all_player_availability():
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT player_name, timezone, availability_start, availability_end FROM players
            WHERE timezone IS NOT NULL AND availability_start IS NOT NULL AND availability_end IS NOT NULL
        """)
        return [dict(row) for row in cursor.fetchall()]

def get_reminder_minutes(event_id: int, player_name: str):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT reminder_minutes FROM rsvps
            WHERE event_id = ? AND player_name = ?
        """, (event_id, player_name))
        row = cursor.fetchone()
        return row["reminder_minutes"] if row and row["reminder_minutes"] else None

def delete_event(event_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.execute("DELETE FROM rsvps WHERE event_id = ?", (event_id,))
        conn.commit()

def delete_expired_events(now_str: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM events WHERE datetime_utc < ?", (now_str,))
        deleted = cursor.rowcount
        conn.execute("DELETE FROM rsvps WHERE event_id NOT IN (SELECT id FROM events)")
        conn.commit()
        return deleted

def delete_offline_player(player_name: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM players WHERE player_name = ?", (player_name,))
        conn.commit()

