#!/usr/bin/env python3
"""
Test script to run network check without scheduler dependencies
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import network_checker
import email_sender
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_once():
    """Run network check once and send email"""
    logger.info("="*50)
    logger.info("Starting network stability check (test run)")
    logger.info("="*50)
    
    try:
        # Run network checks
        check_results = network_checker.run_all_checks(
            targets=config.PING_TARGETS,
            count=config.PING_COUNT
        )
        
        # Log results
        logger.info(f"Overall Status: {check_results['overall_status']}")
        for result in check_results['results']:
            logger.info(
                f"{result['target']}: {result['avg_ms']:.1f}ms avg, "
                f"{result['packet_loss_pct']:.1f}% loss"
            )
        
        # Try to send email (will fail without proper SMTP setup, but we'll see the error)
        logger.info("Attempting to send email...")
        success = email_sender.send_email(
            check_results=check_results,
            sender_email=config.EMAIL_SENDER,
            sender_password=config.EMAIL_PASSWORD,
            receiver_email=config.EMAIL_RECEIVER,
            smtp_host=config.SMTP_HOST,
            smtp_port=config.SMTP_PORT
        )
        
        if success:
            logger.info("Network check completed and email sent successfully")
        else:
            logger.warning("Network check completed but email sending failed (check credentials)")
            
    except Exception as e:
        logger.error(f"Error in network monitoring job: {e}", exc_info=True)
    
    logger.info("="*50)
    logger.info("Network stability check finished")
    logger.info("="*50)

if __name__ == "__main__":
    run_once()
