import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

BOT_TOKEN = "7157068412:AAEkomBO_qCBW7SfUvblefqJ-WL6m8TZluk"
CHAT_ID = "6054204698"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
SEND_MSG_URL = f"{API_URL}/sendMessage"


def create_telegram_message(check_results: Dict[str, Any]) -> str:
    """Create Telegram message from network check results"""
    status = check_results["overall_status"]
    timestamp = check_results["timestamp"]
    results = check_results["results"]

    status_emoji = {"Stable": "✅", "Unstable": "⚠️", "Critical": "🔴", "Unknown": "❓"}

    emoji = status_emoji.get(status, "❓")

    msg = f"🌐 *Network Stability Report*\n\n"
    msg += f"Status: {emoji} *{status}*\n"
    msg += f"Waktu: {timestamp}\n\n"
    msg += "*Ping Results:*\n"

    for r in results:
        target = r["target"]
        avg = r["avg_ms"]
        loss = r["packet_loss_pct"]
        reachable = r["reachable"]

        if not reachable:
            status_icon = "🔴"
        elif loss >= 5.0 or avg >= 200.0:
            status_icon = "🔴"
        elif loss >= 1.0 or avg >= 100.0:
            status_icon = "⚠️"
        else:
            status_icon = "✅"

        msg += f"{status_icon} {target}: {avg:.1f}ms, {loss:.1f}% loss\n"

    if status == "Stable":
        rec = "Network normal. No action needed."
    elif status == "Unstable":
        rec = "Network issues detected. Monitor closely."
    else:
        rec = "Network critical! Check router/ISP."

    msg += f"\n_Recommendation: {rec}_"

    return msg


def send_telegram(text: str) -> bool:
    """Send message to Telegram"""
    try:
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        response = requests.post(SEND_MSG_URL, data=data, timeout=10)

        if response.status_code == 200:
            logger.info("Telegram message sent successfully")
            return True
        else:
            logger.error(f"Telegram API error: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        logger.error("No internet connection - Telegram message failed")
        return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def send_network_notification(check_results: Dict[str, Any]) -> bool:
    """Send network check results to Telegram"""
    message = create_telegram_message(check_results)
    return send_telegram(message)


def send_text_message(text: str) -> bool:
    """Send plain text message to Telegram"""
    return send_telegram(text)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    dummy_results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": "Stable",
        "results": [
            {
                "target": "8.8.8.8",
                "min_ms": 10.5,
                "avg_ms": 12.3,
                "max_ms": 15.7,
                "packet_loss_pct": 0.0,
                "reachable": True,
            }
        ],
    }

    print("Testing Telegram notification...")
    success = send_network_notification(dummy_results)
    print(f"Success: {success}")
