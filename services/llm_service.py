"""
LLM Service for intelligent issue classification and sentiment analysis
"""

import json
from typing import Dict, Any
import aiohttp
from openai import AsyncOpenAI
import anthropic

from config.settings import settings
from utils.logger import setup_logger
from utils.helpers import retry_async

logger = setup_logger(__name__)


class LLMService:
    """Service for LLM-based classification and analysis"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        
        if self.provider == "openai":
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        elif self.provider == "anthropic":
            self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            logger.warning(f"⚠️ Unknown LLM provider: {self.provider}, defaulting to mock")
            self.client = None
    
    def _build_classification_prompt(self, message: str) -> str:
        """Build the classification prompt"""
        return f"""Analyze the following customer support message and classify it.

Customer Message: "{message}"

Provide a JSON response with the following fields:
- category: One of [duplicate_payment, refund_request, account_access, technical_issue, billing_inquiry, general_inquiry, complaint, feature_request]
- sentiment: One of [positive, neutral, negative, very_negative]
- urgency: One of [low, medium, high, critical]
- summary: A brief one-line summary of the issue
- suggested_action: Recommended next step

Respond ONLY with valid JSON, no additional text."""
    
    @retry_async(max_retries=settings.MAX_RETRIES, delay=settings.RETRY_DELAY)
    async def classify_issue(self, message: str) -> Dict[str, Any]:
        """
        Classify customer issue using LLM
        
        Args:
            message: Customer message text
            
        Returns:
            Classification results with category, sentiment, urgency
        """
        try:
            logger.info(f"🤖 Classifying issue with {self.provider}...")
            
            if self.provider == "openai":
                return await self._classify_with_openai(message)
            elif self.provider == "anthropic":
                return await self._classify_with_anthropic(message)
            else:
                return self._mock_classification(message)
                
        except Exception as e:
            logger.error(f"❌ LLM classification error: {str(e)}", exc_info=True)
            # Fallback to mock classification
            logger.info("⚠️ Falling back to rule-based classification")
            return self._mock_classification(message)
    
    async def _classify_with_openai(self, message: str) -> Dict[str, Any]:
        """Classify using OpenAI"""
        try:
            prompt = self._build_classification_prompt(message)
            
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert customer support analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result = json.loads(content)
            logger.info(f"✅ OpenAI classification: {result.get('category')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ OpenAI error: {str(e)}")
            raise
    
    async def _classify_with_anthropic(self, message: str) -> Dict[str, Any]:
        """Classify using Anthropic Claude"""
        try:
            prompt = self._build_classification_prompt(message)
            
            response = await self.client.messages.create(
                model=settings.LLM_MODEL,
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result = json.loads(content)
            logger.info(f"✅ Anthropic classification: {result.get('category')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Anthropic error: {str(e)}")
            raise
    
    def _mock_classification(self, message: str) -> Dict[str, Any]:
        """
        Rule-based mock classification for testing/fallback
        """
        message_lower = message.lower()
        
        # Category detection
        category = "general_inquiry"
        if any(word in message_lower for word in ["duplicate", "double", "twice", "charged twice"]):
            category = "duplicate_payment"
        elif any(word in message_lower for word in ["refund", "money back", "return"]):
            category = "refund_request"
        elif any(word in message_lower for word in ["login", "password", "access", "locked"]):
            category = "account_access"
        elif any(word in message_lower for word in ["error", "bug", "not working", "broken"]):
            category = "technical_issue"
        elif any(word in message_lower for word in ["bill", "invoice", "charge", "payment"]):
            category = "billing_inquiry"
        elif any(word in message_lower for word in ["angry", "disappointed", "terrible", "worst"]):
            category = "complaint"
        elif any(word in message_lower for word in ["suggest", "feature", "add", "would be nice"]):
            category = "feature_request"
        
        # Sentiment detection
        sentiment = "neutral"
        negative_words = ["angry", "frustrated", "terrible", "worst", "hate", "horrible", "disappointed"]
        positive_words = ["great", "thank", "excellent", "happy", "love", "appreciate"]
        
        negative_count = sum(1 for word in negative_words if word in message_lower)
        positive_count = sum(1 for word in positive_words if word in message_lower)
        
        if negative_count > positive_count:
            sentiment = "very_negative" if negative_count > 2 else "negative"
        elif positive_count > negative_count:
            sentiment = "positive"
        
        # Urgency detection
        urgency = "medium"
        urgent_words = ["urgent", "asap", "immediately", "critical", "emergency"]
        if any(word in message_lower for word in urgent_words):
            urgency = "critical"
        elif category in ["duplicate_payment", "account_access"]:
            urgency = "high"
        elif sentiment == "very_negative":
            urgency = "high"
        elif category in ["feature_request", "general_inquiry"]:
            urgency = "low"
        
        result = {
            "category": category,
            "sentiment": sentiment,
            "urgency": urgency,
            "summary": message[:100] + "..." if len(message) > 100 else message,
            "suggested_action": self._get_suggested_action(category)
        }
        
        logger.info(f"✅ Mock classification: {category}")
        return result
    
    def _get_suggested_action(self, category: str) -> str:
        """Get suggested action based on category"""
        actions = {
            "duplicate_payment": "Initiate refund process and verify transaction records",
            "refund_request": "Review refund eligibility and process accordingly",
            "account_access": "Reset password and verify account security",
            "technical_issue": "Escalate to technical team for investigation",
            "billing_inquiry": "Review billing details and provide clarification",
            "general_inquiry": "Provide information and resources",
            "complaint": "Acknowledge issue and escalate to manager",
            "feature_request": "Log request for product team review"
        }
        return actions.get(category, "Review and respond to customer")
    
    async def analyze_sentiment_batch(self, messages: list) -> list:
        """Analyze sentiment for multiple messages"""
        results = []
        for message in messages:
            try:
                classification = await self.classify_issue(message)
                results.append({
                    "message": message,
                    "sentiment": classification.get("sentiment"),
                    "category": classification.get("category")
                })
            except Exception as e:
                logger.error(f"❌ Error analyzing message: {str(e)}")
                results.append({
                    "message": message,
                    "sentiment": "unknown",
                    "category": "unknown"
                })
        return results
