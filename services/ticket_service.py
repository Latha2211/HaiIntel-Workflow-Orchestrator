"""
Ticket Service for creating and managing customer tickets
"""

import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import settings
from utils.logger import setup_logger
from utils.helpers import retry_async

logger = setup_logger(__name__)


class TicketService:
    """Service for ticket creation and management"""
    
    def __init__(self):
        self.api_url = settings.TICKET_API_URL
        self.timeout = aiohttp.ClientTimeout(total=settings.TICKET_API_TIMEOUT)
        self.tickets_cache = {}  # In-memory cache for demo
    
    @retry_async(max_retries=settings.MAX_RETRIES, delay=settings.RETRY_DELAY)
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new support ticket
        
        Args:
            ticket_data: Ticket information
            
        Returns:
            Created ticket response
        """
        try:
            logger.info(f"🎫 Creating ticket {ticket_data.get('ticket_id')}...")
            
            # Store in local cache
            ticket_id = ticket_data.get('ticket_id')
            self.tickets_cache[ticket_id] = {
                **ticket_data,
                "status": "open",
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Call external API (reqres.in for demo)
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                payload = {
                    "name": f"Ticket_{ticket_data.get('ticket_id')}",
                    "job": ticket_data.get('category', 'support'),
                    "ticket_data": ticket_data
                }
                
                async with session.post(self.api_url, json=payload) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        logger.info(f"✅ Ticket {ticket_id} created successfully")
                        
                        # Update cache with external response
                        self.tickets_cache[ticket_id]['external_id'] = result.get('id')
                        self.tickets_cache[ticket_id]['api_response'] = result
                        
                        return {
                            "success": True,
                            "ticket_id": ticket_id,
                            "external_id": result.get('id'),
                            "created_at": result.get('createdAt'),
                            "data": self.tickets_cache[ticket_id]
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ API error: {response.status} - {error_text}")
                        
                        # Still return success with cache data
                        return {
                            "success": True,
                            "ticket_id": ticket_id,
                            "note": "Ticket stored locally, external API unavailable",
                            "data": self.tickets_cache[ticket_id]
                        }
                        
        except aiohttp.ClientError as e:
            logger.error(f"❌ Network error creating ticket: {str(e)}")
            # Graceful degradation - still store locally
            return {
                "success": True,
                "ticket_id": ticket_data.get('ticket_id'),
                "note": "Ticket stored locally, network unavailable",
                "data": self.tickets_cache.get(ticket_data.get('ticket_id'))
            }
        except Exception as e:
            logger.error(f"❌ Error creating ticket: {str(e)}", exc_info=True)
            raise
    
    async def get_ticket_status(self, ticket_id: str) -> str:
        """Get current ticket status"""
        try:
            ticket = self.tickets_cache.get(ticket_id)
            if ticket:
                return ticket.get('status', 'unknown')
            
            logger.warning(f"⚠️ Ticket {ticket_id} not found in cache")
            return "not_found"
            
        except Exception as e:
            logger.error(f"❌ Error getting ticket status: {str(e)}")
            return "error"
    
    async def get_ticket_details(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get full ticket details"""
        try:
            ticket = self.tickets_cache.get(ticket_id)
            if ticket:
                logger.info(f"✅ Retrieved ticket {ticket_id}")
                return ticket
            
            logger.warning(f"⚠️ Ticket {ticket_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting ticket details: {str(e)}")
            return None
    
    async def update_ticket_status(
        self,
        ticket_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update ticket status"""
        try:
            if ticket_id not in self.tickets_cache:
                logger.error(f"❌ Ticket {ticket_id} not found")
                return {"success": False, "error": "Ticket not found"}
            
            self.tickets_cache[ticket_id]['status'] = status
            self.tickets_cache[ticket_id]['updated_at'] = datetime.utcnow().isoformat()
            
            if notes:
                if 'notes' not in self.tickets_cache[ticket_id]:
                    self.tickets_cache[ticket_id]['notes'] = []
                self.tickets_cache[ticket_id]['notes'].append({
                    "note": notes,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            logger.info(f"✅ Ticket {ticket_id} updated to status: {status}")
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "status": status,
                "updated_at": self.tickets_cache[ticket_id]['updated_at']
            }
            
        except Exception as e:
            logger.error(f"❌ Error updating ticket: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_all_tickets(self, status: Optional[str] = None) -> list:
        """Get all tickets, optionally filtered by status"""
        try:
            tickets = list(self.tickets_cache.values())
            
            if status:
                tickets = [t for t in tickets if t.get('status') == status]
            
            logger.info(f"✅ Retrieved {len(tickets)} tickets")
            return tickets
            
        except Exception as e:
            logger.error(f"❌ Error retrieving tickets: {str(e)}")
            return []
    
    async def close_ticket(
        self,
        ticket_id: str,
        resolution: str
    ) -> Dict[str, Any]:
        """Close a ticket with resolution"""
        try:
            if ticket_id not in self.tickets_cache:
                return {"success": False, "error": "Ticket not found"}
            
            self.tickets_cache[ticket_id]['status'] = 'resolved'
            self.tickets_cache[ticket_id]['resolution'] = resolution
            self.tickets_cache[ticket_id]['resolved_at'] = datetime.utcnow().isoformat()
            self.tickets_cache[ticket_id]['updated_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"✅ Ticket {ticket_id} closed")
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "status": "resolved",
                "resolution": resolution
            }
            
        except Exception as e:
            logger.error(f"❌ Error closing ticket: {str(e)}")
            return {"success": False, "error": str(e)}
