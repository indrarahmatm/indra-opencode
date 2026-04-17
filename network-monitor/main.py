import schedule
import time
import argparse
import logging
import sys
from datetime import datetime

# Import our modules
import config
import network_checker
import telegram_sender
import notification_queue

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(config.LOG_FILE), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Initialize notification queue database
notification_queue.init_db()


def job():
    """Main job function to run network check and send email"""
    logger.info("=" * 50)
    logger.info("Starting network stability check")
    logger.info("=" * 50)

    try:
        # Run network checks
        check_results = network_checker.run_all_checks(
            targets=config.PING_TARGETS, count=config.PING_COUNT
        )

        # Log results
        logger.info(f"Overall Status: {check_results['overall_status']}")
        for result in check_results["results"]:
            logger.info(
                f"{result['target']}: {result['avg_ms']:.1f}ms avg, "
                f"{result['packet_loss_pct']:.1f}% loss"
            )

        # First, try to send any pending notifications
        send_pending_notifications()

        # Send notification via Telegram
        success = telegram_sender.send_network_notification(check_results)

        if success:
            logger.info(
                "Network check completed and Telegram notification sent successfully"
            )
        else:
            logger.warning(
                "Network check completed but FAILED to send Telegram - saving to queue"
            )
            notification_queue.save_pending_notification(check_results)

    except Exception as e:
        logger.error(f"Error in network monitoring job: {e}", exc_info=True)

    logger.info("=" * 50)
    logger.info("Network stability check finished")
    logger.info("=" * 50)


def send_pending_notifications():
    """Send all pending notifications from SQLite queue"""
    pending = notification_queue.get_pending_notifications()

    if not pending:
        return

    logger.info(f"Found {len(pending)} pending notifications to send")

    for notif in pending:
        check_results = {
            "timestamp": notif["timestamp"],
            "overall_status": notif["overall_status"],
            "results": notif["results"],
        }

        success = telegram_sender.send_network_notification(check_results)

        if success:
            notification_queue.mark_as_sent(notif["id"])
            logger.info(f"Sent pending notification ID {notif['id']}")
        else:
            logger.warning(f"Failed to send pending notification ID {notif['id']}")


def run_scheduler():
    """Run the scheduler continuously"""
    logger.info(f"Setting up daily schedule at {config.SCHEDULE_TIME}")
    schedule.every().day.at(config.SCHEDULE_TIME).do(job)

    logger.info("Scheduler started. Waiting for scheduled time...")
    logger.info(f"Next run scheduled for today at {config.SCHEDULE_TIME}")

    # Run once immediately for testing (optional)
    # job()

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Network Stability Monitor")
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run the check once immediately instead of scheduling",
    )
    parser.add_argument(
        "--test-email", action="store_true", help="Test Telegram notification"
    )

    args = parser.parse_args()

    if args.test_email:
        logger.info("Testing Telegram functionality...")
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
                },
                {
                    "target": "1.1.1.1",
                    "min_ms": 11.2,
                    "avg_ms": 13.1,
                    "max_ms": 16.8,
                    "packet_loss_pct": 0.0,
                    "reachable": True,
                },
            ],
        }
        success = telegram_sender.send_network_notification(dummy_results)
        if success:
            logger.info("Test Telegram notification sent successfully!")
        else:
            logger.error("Failed to send test Telegram notification")
        return

    if args.run_now:
        logger.info("Running network check once...")
        job()
    else:
        logger.info("Starting Network Stability Monitor in scheduled mode")
        logger.info(f"Will run daily at {config.SCHEDULE_TIME}")
        run_scheduler()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal. Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
