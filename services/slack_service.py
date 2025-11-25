"""
Slack service for team notifications
"""

import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime

from config.settings import settings
from utils.logger import setup_logger
from utils.helpers import retry_async

logger = setup_logger(__name__)


class SlackService:
    """Service for Slack notifications"""
    
    def __init__(self):
        self.webhook_url = settings.SLACK_WEBHOOK_URL
        self.channel = settings.SLACK_CHANNEL
        self.configured = bool(self.webhook_url)
    
    @retry_async(max_retries=2, delay=3)
    async def send_alert(
        self,
        title: str,
        message: str,
        color: str = "warning",
        fields: Optional[list] = None
    ) -> bool:
        """
        Send alert to Slack
        
        Args:
            title: Alert title
            message: Alert message
            color: Alert color (good, warning, danger)
            fields: Additional fields
            
        Returns:
            Success status
        """
        try:
            logger.info(f"💬 Sending Slack alert: {title}")
            
            if not self.configured:
                logger.warning("⚠️ Slack webhook not configured, simulating alert")
                logger.info(f"💬 [SIMULATED] Slack alert: {title}")
                logger.debug(f"Message: {message}")
                return True
            
            # Build Slack message
            payload = {
                "channel": self.channel,
                "username": "HaiIntel Bot",
                "icon_emoji": ":robot_face:",
                "attachments": [
                    {
                        "color": self._get_color_code(color),
                        "title": title,
                        "text": message,
                        "footer": "HaiIntel Workflow Orchestrator",
                        "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            # Add fields if provided
            if fields:
                payload["attachments"][0]["fields"] = fields
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Slack alert sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Slack error: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Slack send error: {str(e)}")
            return False
    
    async def send_ticket_notification(
        self,
        ticket_id: str,
        customer_id: str,
        category: str,
        priority: str,
        sentiment: str,
        channel: str
    ) -> bool:
        """Send formatted ticket notification"""
        try:
            color = {
                "high": "danger",
                "medium": "warning",
                "low": "good"
            }.get(priority, "warning")
            
            fields = [
                {
                    "title": "Ticket ID",
                    "value": ticket_id,
                    "short": True
                },
                {
                    "title": "Customer",
                    "value": customer_id,
                    "short": True
                },
                {
                    "title": "Category",
                    "value": category.replace("_", " ").title(),
                    "short": True
                },
                {
                    "title": "Priority",
                    "value": priority.upper(),
                    "short": True
                },
                {
                    "title": "Sentiment",
                    "value": self._get_sentiment_emoji(sentiment) + " " + sentiment.title(),
                    "short": True
                },
                {
                    "title": "Channel",
                    "value": channel.title(),
                    "short": True
                }
            ]
            
            return await self.send_alert(
                title=f"🎫 New Support Ticket: {ticket_id}",
                message=f"A new {priority} priority ticket has been created",
                color=color,
                fields=fields
            )
            
        except Exception as e:
            logger.error(f"❌ Error sending ticket notification: {str(e)}")
            return False
    
    async def send_reminder_alert(
        self,
        ticket_id: str,
        category: str,
        hours_open: int
    ) -> bool:
        """Send reminder for unresolved ticket"""
        try:
            return await self.send_alert(
                title=f"⏰ Unresolved Ticket Alert",
                message=f"Ticket {ticket_id} ({category}) has been open for {hours_open} hours without resolution",
                color="danger"
            )
        except Exception as e:
            logger.error(f"❌ Error sending reminder alert: {str(e)}")
            return False
    
    async def send_analytics_summary(
        self,
        summary: Dict[str, Any]
    ) -> bool:
        """Send daily analytics summary"""
        try:
            fields = [
                {
                    "title": "Total Issues",
                    "value": str(summary.get("total_issues", 0)),
                    "short": True
                },
                {
                    "title": "Last 24h",
                    "value": str(summary.get("last_24h", 0)),
                    "short": True
                },
                {
                    "title": "Avg Resolution",
                    "value": f"{summary.get('avg_resolution_hours', 0)}h",
                    "short": True
                },
                {
                    "title": "Resolution Rate",
                    "value": f"{summary.get('resolution_rate', 0)}%",
                    "short": True
                }
            ]
            
            return await self.send_alert(
                title="📊 Daily Analytics Summary",
                message="Here's your daily customer support analytics",
                color="good",
                fields=fields
            )
            
        except Exception as e:
            logger.error(f"❌ Error sending analytics summary: {str(e)}")
            return False
    
    def _get_color_code(self, color: str) -> str:
        """Convert color name to hex code"""
        colors = {
            "good": "#36a64f",
            "warning": "#ff9800",
            "danger": "#f44336",
            "info": "#2196f3"
        }
        return colors.get(color, colors["warning"])
    
    def _get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji for sentiment"""
        emojis = {
            "positive": "😊",
            "neutral": "😐",
            "negative": "😞",
            "very_negative": "😡"
        }
        return emojis.get(sentiment, "🤔")
