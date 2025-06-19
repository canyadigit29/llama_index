#!/usr/bin/env python3
"""
Railway Environment Monitor

This script runs periodically to check environment health and send alerts
for any critical issues with the Railway deployment. It can be scheduled
as a cron job or a separate Railway service with a schedule.

Usage:
    python railway_env_monitor.py [--notify]

The --notify flag will attempt to send notifications via the configured channels.
"""

import os
import sys
import logging
import requests
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("railway_monitor")

# Import env health check if available
try:
    from env_health_check import run_health_check
    ENV_HEALTH_CHECK_AVAILABLE = True
except ImportError:
    ENV_HEALTH_CHECK_AVAILABLE = False
    logger.error("Could not import env_health_check - using direct API check instead")

def check_api_health():
    """
    Check the health of the API by calling the /health endpoint
    """
    # Determine the URL to check
    railway_url = os.environ.get("LLAMAINDEX_URL", None)
    local_url = f"http://localhost:{os.environ.get('PORT', '8000')}"
    
    urls_to_try = []
    
    # Add Railway URL if available
    if railway_url:
        urls_to_try.append(railway_url)
    
    # Add local URL for local testing
    if os.environ.get("CHECK_LOCAL", "").lower() in ("true", "1", "yes"):
        urls_to_try.append(local_url)
    
    # Default to localhost if no URLs specified
    if not urls_to_try:
        urls_to_try = [local_url]
    
    results = {}
    
    # Try each URL
    for url in urls_to_try:
        health_url = f"{url.rstrip('/')}/health"
        logger.info(f"Checking health endpoint: {health_url}")
        
        try:
            response = requests.get(health_url, timeout=30)
            
            # Try to parse the response as JSON
            try:
                health_data = response.json()
                status = health_data.get("status", "unknown")
                
                results[url] = {
                    "status_code": response.status_code,
                    "health_status": status,
                    "critical_failures": health_data.get("critical_failures", []),
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "railway_info": health_data.get("railway", {})
                }
            except json.JSONDecodeError:
                # Not JSON or invalid JSON
                results[url] = {
                    "status_code": response.status_code,
                    "health_status": "error",
                    "error": "Invalid JSON response",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
        except requests.RequestException as e:
            results[url] = {
                "status_code": None,
                "health_status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    return results

def send_notification(subject, message):
    """
    Send a notification using configured channels
    """
    logger.info(f"NOTIFICATION: {subject}")
    logger.info(message)
    
    # Example: Send to Slack webhook
    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if slack_webhook:
        try:
            response = requests.post(
                slack_webhook,
                json={"text": f"*{subject}*\n```\n{message}\n```"},
                timeout=10
            )
            if response.status_code == 200:
                logger.info("Notification sent to Slack successfully")
            else:
                logger.error(f"Failed to send Slack notification: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
    
    # Example: Log to Railway custom logging service
    railway_log_url = os.environ.get("RAILWAY_LOG_URL")
    if railway_log_url:
        try:
            response = requests.post(
                railway_log_url,
                json={
                    "level": "error",
                    "message": message,
                    "subject": subject,
                    "timestamp": datetime.now().isoformat()
                },
                timeout=10
            )
            if response.status_code in (200, 201, 204):
                logger.info("Notification sent to Railway logging service")
            else:
                logger.error(f"Failed to send Railway log: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending Railway log: {str(e)}")

def analyze_results_and_alert(api_results):
    """
    Analyze API health check results and send alerts if needed
    """
    # Track overall status
    all_healthy = True
    critical_issues = []
    
    # Check each endpoint result
    for url, result in api_results.items():
        # Check for connection errors
        if result.get("status_code") is None:
            all_healthy = False
            critical_issues.append(f"Could not connect to {url}: {result.get('error', 'Unknown error')}")
            continue
        
        # Check for non-200 responses
        if result.get("status_code") != 200:
            all_healthy = False
            critical_issues.append(f"Unhealthy response from {url}: HTTP {result.get('status_code')}")
            continue
        
        # Check health status
        if result.get("health_status") != "healthy":
            all_healthy = False
            critical_issues.extend(result.get("critical_failures", []))
    
    # Send notifications if issues found
    if not all_healthy and critical_issues and "--notify" in sys.argv:
        service_name = os.environ.get("RAILWAY_SERVICE_NAME", "LlamaIndex Backend")
        subject = f"🚨 ALERT: {service_name} environment issues detected"
        
        message = f"The following critical issues were detected at {datetime.now().isoformat()}:\n\n"
        message += "\n".join([f"- {issue}" for issue in critical_issues])
        message += "\n\nPlease check the Railway dashboard and logs for more details."
        
        send_notification(subject, message)
        
    return all_healthy, critical_issues

def main():
    """Main function to run the monitor"""
    logger.info("=" * 60)
    logger.info("RAILWAY ENVIRONMENT MONITOR STARTING")
    logger.info("=" * 60)
    
    # First check the API health
    api_results = check_api_health()
    all_healthy, critical_issues = analyze_results_and_alert(api_results)
    
    # Directly check environment variables if available
    if ENV_HEALTH_CHECK_AVAILABLE:
        logger.info("Running environment health check...")
        env_issues, env_summary, _ = run_health_check(log_results=True)
        
        if not env_summary["is_healthy"] and "--notify" in sys.argv:
            # Send a separate notification for environment issues
            service_name = os.environ.get("RAILWAY_SERVICE_NAME", "LlamaIndex Backend")
            subject = f"⚠️ {service_name}: Environment configuration issues"
            
            message = f"Environment check detected issues at {datetime.now().isoformat()}:\n\n"
            for issue in env_issues:
                if issue["severity"] == "critical":
                    message += f"- CRITICAL: {issue['variable']} - {issue['issue']}\n"
            
            send_notification(subject, message)
    
    # Output overall status
    if all_healthy:
        logger.info("✅ All services are healthy")
        exit_code = 0
    else:
        logger.error("❌ Issues detected with services")
        for issue in critical_issues:
            logger.error(f"- {issue}")
        exit_code = 1
    
    logger.info("=" * 60)
    logger.info("RAILWAY ENVIRONMENT MONITOR COMPLETE")
    logger.info("=" * 60)
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
