  """
HaiIntel Customer Issue Workflow Orchestrator
Multi-channel customer support automation with AI-powered classification
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uvicorn
import asyncio

from services.llm_service import LLMService
from services.ticket_service import TicketService
from services.notification_service import NotificationService
from services.analytics_service import AnalyticsService
from services.slack_service import SlackService
from utils.logger import setup_logger
from utils.helpers import generate_ticket_id, calculate_priority
from config.settings import settings

# Initialize logger
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HaiIntel Workflow Orchestrator",
    description="AI-powered multi-channel customer support automation",
    version="1.0.0"
)

# Initialize services
llm_service = LLMService()
ticket_service = TicketService()
notification_service = NotificationService()
analytics_service = AnalyticsService()
slack_service = SlackService()


class CustomerIssueRequest(BaseModel):
    """Customer issue request model"""
    customerId: str = Field(..., description="Unique customer identifier")
    channel: str = Field(..., description="Communication channel (email/sms/whatsapp)")
    message: str = Field(..., description="Customer message/complaint")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class WorkflowResponse(BaseModel):
    """Workflow response model"""
    success: bool
    ticket_id: str
    category: str
    sentiment: str
    priority: str
    channels_notified: List[str]
    estimated_resolution: str
    message: str


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting HaiIntel Workflow Orchestrator...")
    logger.info(f"✅ Environment: {settings.ENVIRONMENT}")
    logger.info(f"✅ Port: {settings.PORT}")
    

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down HaiIntel Workflow Orchestrator...")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "HaiIntel Workflow Orchestrator",
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "llm": "operational",
            "ticket_system": "operational",
            "notifications": "operational",
            "analytics": "operational"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


async def schedule_reminder(ticket_id: str, customer_id: str, category: str):
    """Schedule 24-hour reminder for unresolved tickets"""
    try:
        logger.info(f"⏰ Scheduling 24h reminder for ticket {ticket_id}")
        
        # Simulate waiting (in production, use Celery or similar)
        await asyncio.sleep(settings.REMINDER_DELAY_SECONDS)
        
        # Check ticket status
        ticket_status = await ticket_service.get_ticket_status(ticket_id)
        
        if ticket_status != "resolved":
            logger.warning(f"⚠️ Ticket {ticket_id} still unresolved after 24h")
            
            # Send reminder notifications
            reminder_message = f"Reminder: Ticket {ticket_id} ({category}) is still pending resolution."
            
            await notification_service.send_email(
                customer_id,
                "Ticket Status Reminder",
                reminder_message
            )
            
            # Notify Slack
            await slack_service.send_alert(
                f"🔔 Unresolved Ticket Alert",
                f"Ticket {ticket_id} for customer {customer_id} is still open after 24 hours.",
                "warning"
            )
            
            logger.info(f"✅ Reminder sent for ticket {ticket_id}")
        else:
            logger.info(f"✅ Ticket {ticket_id} already resolved")
            
    except Exception as e:
        logger.error(f"❌ Error scheduling reminder: {str(e)}", exc_info=True)


@app.post("/webhook/customer-issue", response_model=WorkflowResponse)
async def handle_customer_issue(
    request: CustomerIssueRequest,
    background_tasks: BackgroundTasks
):
    """
    Main webhook endpoint for handling customer issues
    
    Workflow:
    1. Receive customer issue
    2. LLM classification (category + sentiment)
    3. Create ticket
    4. Multi-channel acknowledgment
    5. Schedule 24h reminder
    6. Analytics tracking
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"📨 Received issue from customer {request.customerId} via {request.channel}")
        logger.debug(f"Message: {request.message}")
        
        # Step 1: LLM Classification
        logger.info("🤖 Step 1: Analyzing message with LLM...")
        classification = await llm_service.classify_issue(request.message)
        
        category = classification.get("category", "general_inquiry")
        sentiment = classification.get("sentiment", "neutral")
        urgency = classification.get("urgency", "medium")
        
        logger.info(f"✅ Classification: {category} | Sentiment: {sentiment} | Urgency: {urgency}")
        
        # Calculate priority
        priority = calculate_priority(sentiment, urgency, category)
        
        # Step 2: Create Ticket
        logger.info("🎫 Step 2: Creating ticket...")
        ticket_id = generate_ticket_id()
        
        ticket_data = {
            "ticket_id": ticket_id,
            "customer_id": request.customerId,
            "channel": request.channel,
            "category": category,
            "sentiment": sentiment,
            "priority": priority,
            "message": request.message,
            "status": "open",
            "created_at": datetime.utcnow().isoformat()
        }
        
        ticket_response = await ticket_service.create_ticket(ticket_data)
        logger.info(f"✅ Ticket created: {ticket_id}")
        
        # Step 3: Multi-Channel Acknowledgment
        logger.info("📢 Step 3: Sending multi-channel acknowledgments...")
        
        acknowledgment_message = f"""
Thank you for contacting us!

Your issue has been received and assigned ticket ID: {ticket_id}
Category: {category.replace('_', ' ').title()}
Priority: {priority.upper()}

Our team will respond within {settings.SLA_HOURS.get(priority, 24)} hours.
"""
        
        # Send to at least 2 channels
        channels_notified = []
        
        # Always send to original channel
        if request.channel == "whatsapp":
            await notification_service.send_whatsapp(request.customerId, acknowledgment_message)
            channels_notified.append("whatsapp")
        elif request.channel == "sms":
            await notification_service.send_sms(request.customerId, acknowledgment_message)
            channels_notified.append("sms")
        elif request.channel == "email":
            await notification_service.send_email(
                request.customerId,
                f"Ticket #{ticket_id} - We've received your request",
                acknowledgment_message
            )
            channels_notified.append("email")
        
        # Send to email as backup (if not already sent)
        if "email" not in channels_notified:
            await notification_service.send_email(
                request.customerId,
                f"Ticket #{ticket_id} - We've received your request",
                acknowledgment_message
            )
            channels_notified.append("email")
        
        # Send SMS for high priority
        if priority == "high" and "sms" not in channels_notified:
            sms_message = f"HaiIntel: Your urgent issue (Ticket {ticket_id}) is being prioritized. We'll respond within 2 hours."
            await notification_service.send_sms(request.customerId, sms_message)
            channels_notified.append("sms")
        
        logger.info(f"✅ Notifications sent via: {', '.join(channels_notified)}")
        
        # Step 4: Slack Notification
        logger.info("💬 Step 4: Sending Slack notification...")
        slack_color = {
            "high": "danger",
            "medium": "warning",
            "low": "good"
        }.get(priority, "warning")
        
        await slack_service.send_alert(
            f"🎫 New Ticket: {ticket_id}",
            f"Customer: {request.customerId}\nCategory: {category}\nSentiment: {sentiment}\nPriority: {priority}\nChannel: {request.channel}",
            slack_color
        )
        
        # Step 5: Schedule 24h Reminder
        logger.info("⏰ Step 5: Scheduling reminder...")
        background_tasks.add_task(
            schedule_reminder,
            ticket_id,
            request.customerId,
            category
        )
        
        # Step 6: Analytics Tracking
        logger.info("📊 Step 6: Tracking analytics...")
        await analytics_service.track_issue(
            ticket_id=ticket_id,
            customer_id=request.customerId,
            category=category,
            sentiment=sentiment,
            priority=priority,
            channel=request.channel,
            resolution_time=None
        )
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"✅ Workflow completed in {processing_time:.2f}s")
        
        # Estimated resolution time
        estimated_hours = settings.SLA_HOURS.get(priority, 24)
        estimated_resolution = (datetime.utcnow() + timedelta(hours=estimated_hours)).isoformat()
        
        return WorkflowResponse(
            success=True,
            ticket_id=ticket_id,
            category=category,
            sentiment=sentiment,
            priority=priority,
            channels_notified=channels_notified,
            estimated_resolution=estimated_resolution,
            message=f"Issue processed successfully. Ticket {ticket_id} created."
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing customer issue: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing issue: {str(e)}"
        )


@app.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """Get analytics dashboard data"""
    try:
        dashboard_data = await analytics_service.get_dashboard_data()
        return JSONResponse(content=dashboard_data)
    except Exception as e:
        logger.error(f"❌ Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tickets/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Get ticket status"""
    try:
        status = await ticket_service.get_ticket_details(ticket_id)
        if not status:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching ticket: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )
