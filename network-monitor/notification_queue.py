import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "pending_notifications.db"


def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            overall_status TEXT NOT NULL,
            results_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def save_pending_notification(check_results: Dict[str, Any]) -> bool:
    """
    Save notification to SQLite when email fails

    Args:
        check_results: Network check results dictionary

    Returns:
        True if saved successfully
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO pending_notifications 
               (timestamp, overall_status, results_json, created_at, sent) 
               VALUES (?, ?, ?, ?, 0)""",
            (
                check_results["timestamp"],
                check_results["overall_status"],
                json.dumps(check_results["results"]),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

        conn.commit()
        conn.close()

        logger.info(f"Notification saved to SQLite: {check_results['timestamp']}")
        return True

    except Exception as e:
        logger.error(f"Failed to save pending notification: {e}")
        return False


def get_pending_notifications() -> List[Dict[str, Any]]:
    """
    Get all pending notifications that haven't been sent

    Returns:
        List of pending notification dictionaries
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """SELECT id, timestamp, overall_status, results_json, created_at 
               FROM pending_notifications WHERE sent = 0 ORDER BY created_at ASC"""
        )

        rows = cursor.fetchall()
        conn.close()

        notifications = []
        for row in rows:
            notifications.append(
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "overall_status": row[2],
                    "results": json.loads(row[3]),
                    "created_at": row[4],
                }
            )

        return notifications

    except Exception as e:
        logger.error(f"Failed to get pending notifications: {e}")
        return []


def mark_as_sent(notification_id: int):
    """Mark a notification as sent"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE pending_notifications SET sent = 1 WHERE id = ?", (notification_id,)
        )

        conn.commit()
        conn.close()

        logger.info(f"Notification {notification_id} marked as sent")

    except Exception as e:
        logger.error(f"Failed to mark notification as sent: {e}")


def delete_notification(notification_id: int):
    """Delete a notification from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM pending_notifications WHERE id = ?", (notification_id,)
        )

        conn.commit()
        conn.close()

        logger.info(f"Notification {notification_id} deleted")

    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")


def get_pending_count() -> int:
    """Get count of pending notifications"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM pending_notifications WHERE sent = 0")

        count = cursor.fetchone()[0]
        conn.close()

        return count

    except Exception as e:
        logger.error(f"Failed to get pending count: {e}")
        return 0


if __name__ == "__main__":
    init_db()
    print("Database initialized")

    # Test functions
    print(f"Pending count: {get_pending_count()}")
    print(f"Pending notifications: {get_pending_notifications()}")
