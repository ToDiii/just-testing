
import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from . import models

def send_notifications(new_results: list[dict], db: Session):
    """
    Send notifications for new results based on active configurations.
    """
    if not new_results:
        return

    configs = db.query(models.NotificationConfig).filter(models.NotificationConfig.enabled == 1).all()
    if not configs:
        return

    print(f"Sending notifications for {len(new_results)} new results to {len(configs)} recipients...")

    # Prepare message content
    subject = f"New Scrape Results: {len(new_results)} new items found"
    
    text_body = "New results found:\n\n"
    html_body = "<h2>New results found:</h2><ul>"
    
    for result in new_results:
        text_body += f"- {result['title']} ({result['url']})\n"
        html_body += f"<li><a href='{result['url']}'>{result['title']}</a></li>"
    
    html_body += "</ul>"

    for config in configs:
        try:
            if config.type == "email":
                _send_email(config.recipient, subject, text_body, html_body)
            elif config.type == "webhook":
                _send_webhook(config.recipient, new_results)
        except Exception as e:
            print(f"Failed to send notification to {config.recipient}: {e}")

def _send_email(recipient: str, subject: str, text_body: str, html_body: str):
    # TODO: Configure SMTP settings via env vars or DB
    # For now, this is a placeholder or requires local SMTP
    # In a real app, you'd use SendGrid, AWS SES, or similar
    print(f"  -> Sending email to {recipient}")
    
    # Example using local debugging server (e.g. python -m smtpd -n -c DebuggingServer localhost:1025)
    # sender = "noreply@bauscraper.local"
    # msg = MIMEMultipart("alternative")
    # msg["Subject"] = subject
    # msg["From"] = sender
    # msg["To"] = recipient
    # msg.attach(MIMEText(text_body, "plain"))
    # msg.attach(MIMEText(html_body, "html"))
    
    # with smtplib.SMTP("localhost", 1025) as server:
    #     server.sendmail(sender, recipient, msg.as_string())

def _send_webhook(url: str, results: list[dict]):
    print(f"  -> Sending webhook to {url}")
    payload = {
        "event": "new_results",
        "count": len(results),
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"     Webhook sent successfully (Status: {response.status_code})")
    except requests.RequestException as e:
        print(f"     Webhook error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"     Response content: {e.response.text}")
        raise e

def send_test_notification(config_id: int, db: Session):
    """
    Send a test notification for a specific configuration.
    """
    config = db.query(models.NotificationConfig).filter(models.NotificationConfig.id == config_id).first()
    if not config:
        raise ValueError("Configuration not found")

    subject = "Test Notification: Bau Scraper"
    text_body = "This is a test notification from your Bau Scraper dashboard to verify your settings."
    html_body = "<h2>Test Notification</h2><p>This is a test notification from your <b>Bau Scraper</b> dashboard to verify your settings.</p>"

    if config.type == "email":
        _send_email(config.recipient, subject, text_body, html_body)
    elif config.type == "webhook":
        test_results = [{
            "title": "Test Result",
            "url": "https://example.com/test",
            "source": "System Test",
            "publication_date": "2024-01-01"
        }]
        _send_webhook(config.recipient, test_results)
    
    return True
