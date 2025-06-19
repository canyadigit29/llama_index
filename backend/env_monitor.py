#!/usr/bin/env python3
"""
Environment Variable Monitor for LlamaIndex Backend

This standalone script can be run periodically to check the health
of all environment variables and services. It can be set up as a cron job
or Railway scheduled task to alert when the environment configuration is
incorrect or missing.

Usage:
    python env_monitor.py [--notify]

The --notify flag enables sending alerts (to be configured).
"""

import sys
import os
import logging
import json
import requests
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("env_monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ENV_MONITOR")

# Import the health check functions
try:
    from env_health_check import run_health_check, log_health_check_results
except ImportError:
    logger.error("Failed to import env_health_check.py. Make sure it's in the same directory.")
    sys.exit(1)

def send_notification(report):
    """
    Send notification about health check failures.
    
    This function is a placeholder. You can configure it to send alerts via:
    - Slack webhook
    - Email
    - SMS
    - PagerDuty
    - Other notification services
    
    For now, it just logs the information.
    """
    if report["status"] == "healthy":
        logger.info("Environment health check passed, no notifications needed.")
        return
    
    # Collect all issues to report
    issues = []
    env_vars = report["environment_variables"]["details"]
    for var_name, details in env_vars.items():
        if details["status"] != "VALID":
            issues.append(f"{var_name}: {details['status']}")
    
    # Add connectivity issues
    for service, result in report["connectivity"].items():
        if not result["success"]:
            issues.append(f"{service}: {result['message']}")
    
    # Placeholder for notification logic - customize as needed
    message = f"ALERT: Environment issues detected on {os.environ.get('RAILWAY_SERVICE_NAME', 'LlamaIndex backend')}\n"
    message += f"Time: {datetime.now().isoformat()}\n"
    message += f"Issues found: {len(issues)}\n\n"
    message += "\n".join(issues)
    
    logger.warning("Would send this notification:\n%s", message)
    
    # Uncomment and configure one of these options to enable real notifications:
    
    # # Option 1: Slack webhook
    # try:
    #     webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    #     if webhook_url:
    #         requests.post(webhook_url, json={"text": message})
    # except Exception as e:
    #     logger.error(f"Failed to send Slack notification: {str(e)}")
    
    # # Option 2: Email via SMTP
    # try:
    #     import smtplib
    #     from email.message import EmailMessage
    #     
    #     smtp_server = os.environ.get("SMTP_SERVER")
    #     smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    #     smtp_username = os.environ.get("SMTP_USERNAME")
    #     smtp_password = os.environ.get("SMTP_PASSWORD")
    #     email_to = os.environ.get("ALERT_EMAIL")
    #     
    #     if all([smtp_server, smtp_username, smtp_password, email_to]):
    #         msg = EmailMessage()
    #         msg.set_content(message)
    #         msg['Subject'] = f"ALERT: Environment issues on {os.environ.get('RAILWAY_SERVICE_NAME', 'LlamaIndex')}"
    #         msg['From'] = smtp_username
    #         msg['To'] = email_to
    #         
    #         server = smtplib.SMTP(smtp_server, smtp_port)
    #         server.starttls()
    #         server.login(smtp_username, smtp_password)
    #         server.send_message(msg)
    #         server.quit()
    # except Exception as e:
    #     logger.error(f"Failed to send email notification: {str(e)}")
    
def main():
    """Run health check and send notifications if needed."""
    logger.info("Starting environment monitor check...")
    
    # Run health check with verbose output
    health_report = run_health_check(verbose=True)
    log_health_check_results(health_report)
    
    # Send notification if --notify flag is provided
    if "--notify" in sys.argv:
        send_notification(health_report)
    
    # Save health check report to file for historical tracking
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"env_health_{timestamp}.json", "w") as f:
            json.dump(health_report, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save health check report: {str(e)}")
    
    # Return success code based on health status
    return 0 if health_report["status"] == "healthy" else 1

if __name__ == "__main__":
    sys.exit(main())
