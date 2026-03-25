import os
import logging
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

class SlackAlertData(BaseModel):
    github_username: str
    known_affiliation: str | None
    event_type: str
    repo_name: str | None
    domain: str | None
    summary: str

async def send_slack_alert(alert_data: SlackAlertData) -> bool:
    """
    Sends a formatted Markdown message to a Slack Webhook.
    """
    if not SLACK_WEBHOOK_URL:
        logger.error("SLACK_WEBHOOK_URL is not set. Skipping Slack alert.")
        return False

    affiliation_text = f" ({alert_data.known_affiliation})" if alert_data.known_affiliation else ""
    domain_text = f"*{alert_data.domain}*" if alert_data.domain else "Unknown Domain"
    target_repo = alert_data.repo_name if alert_data.repo_name else "an unknown repo"
    
    # Constructing a Slack block kit message
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚨 Sovereign Git Anomaly Detected",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Target:* <https://github.com/{alert_data.github_username}|{alert_data.github_username}>{affiliation_text}\n*Domain:* {domain_text}\n*Trigger Event:* `{alert_data.event_type}` on `{target_repo}`"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Claude Summary:*\n> {alert_data.summary}"
            }
        },
        {
            "type": "divider"
        }
    ]

    payload = {"blocks": blocks}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SLACK_WEBHOOK_URL,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Slack alert sent successfully for {alert_data.github_username}.")
            return True
    except Exception as e:
        logger.error(f"Failed to push alert to Slack Webhook: {e}")
        return False
