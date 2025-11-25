"""
Multi-channel notification service (Email, SMS, WhatsApp)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import aiohttp

from config.settings import settings
from utils.logger import setup_logger
from utils.helpers import retry_async

logger = setup_logger(__name__)


class NotificationService:
    """Service for sending notifications across multiple channels"""
    
    def __init__(self):
        self.smtp_configured = bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD)
        self.twilio_configured = bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)
    
    @retry_async(max_retries=2, delay=3)
    async def send_email(
        self,
        customer_id: str,
        subject: str,
        message: str
    ) -> bool:
        """
        Send email notification
        
        Args:
            customer_id: Customer identifier (email)
            subject: Email subject
            message: Email body
            
        Returns:
            Success status
        """
        try:
            logger.info(f"📧 Sending email to {customer_id}...")
            
            # Mock email for demo (replace with actual email)
            recipient = f"{customer_id}@example.com"
            
            if not self.smtp_configured:
                logger.warning("⚠️ SMTP not configured, simulating email send")
                logger.info(f"📧 [SIMULATED] Email sent to {recipient}")
                logger.debug(f"Subject: {subject}")
                logger.debug(f"Message: {message[:100]}...")
                return True
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = recipient
            
            # Add HTML and plain text versions
            text_part = MIMEText(message, 'plain')
            html_part = MIMEText(f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #2563eb;">HaiIntel Customer Support</h2>
                        <div style="background: #f3f4f6; padding: 20px; border-radius: 8px;">
                            {message.replace(chr(10), '<br>')}
                        </div>
                        <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
                            This is an automated message from HaiIntel Support System.
                        </p>
                    </div>
                </body>
            </html>
            """, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email send error: {str(e)}")
            # Don't fail workflow due to email errors
            return False
    
    @retry_async(max_retries=2, delay=3)
    async def send_sms(
        self,
        customer_id: str,
        message: str
    ) -> bool:
        """
        Send SMS notification via Twilio
        
        Args:
            customer_id: Customer phone number
            message: SMS message
            
        Returns:
            Success status
        """
        try:
            logger.info(f"📱 Sending SMS to {customer_id}...")
            
            if not self.twilio_configured:
                logger.warning("⚠️ Twilio not configured, simulating SMS send")
                logger.info(f"📱 [SIMULATED] SMS sent to {customer_id}")
                logger.debug(f"Message: {message[:100]}...")
                return True
            
            # Twilio API call
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
            
            auth = aiohttp.BasicAuth(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            
            data = {
                "From": settings.TWILIO_PHONE_NUMBER,
                "To": customer_id,
                "Body": message[:1600]  # SMS character limit
            }
            
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.post(url, data=data) as response:
                    if response.status == 201:
                        logger.info(f"✅ SMS sent successfully to {customer_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Twilio error: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ SMS send error: {str(e)}")
            return False
    
    @retry_async(max_retries=2, delay=3)
    async def send_whatsapp(
        self,
        customer_id: str,
        message: str
    ) -> bool:
        """
        Send WhatsApp message via Twilio
        
        Args:
            customer_id: Customer WhatsApp number
            message: WhatsApp message
            
        Returns:
            Success status
        """
        try:
            logger.info(f"💬 Sending WhatsApp to {customer_id}...")
            
            if not self.twilio_configured:
                logger.warning("⚠️ Twilio not configured, simulating WhatsApp send")
                logger.info(f"💬 [SIMULATED] WhatsApp sent to {customer_id}")
                logger.debug(f"Message: {message[:100]}...")
                return True
            
            # Twilio WhatsApp API
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
            
            auth = aiohttp.BasicAuth(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            
            # Format WhatsApp number
            whatsapp_to = f"whatsapp:{customer_id}"
            whatsapp_from = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"
            
            data = {
                "From": whatsapp_from,
                "To": whatsapp_to,
                "Body": message
            }
            
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.post(url, data=data) as response:
                    if response.status == 201:
                        logger.info(f"✅ WhatsApp sent successfully to {customer_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Twilio WhatsApp error: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ WhatsApp send error: {str(e)}")
            return False
    
    async def send_multi_channel(
        self,
        customer_id: str,
        subject: str,
        message: str,
        channels: list
    ) -> dict:
        """
        Send notification to multiple channels
        
        Args:
            customer_id: Customer identifier
            subject: Message subject (for email)
            message: Message content
            channels: List of channels to use
            
        Returns:
            Status for each channel
        """
        results = {}
        
        for channel in channels:
            try:
                if channel == "email":
                    results[channel] = await self.send_email(customer_id, subject, message)
                elif channel == "sms":
                    results[channel] = await self.send_sms(customer_id, message)
                elif channel == "whatsapp":
                    results[channel] = await self.send_whatsapp(customer_id, message)
                else:
                    logger.warning(f"⚠️ Unknown channel: {channel}")
                    results[channel] = False
            except Exception as e:
                logger.error(f"❌ Error sending to {channel}: {str(e)}")
                results[channel] = False
        
        return results
