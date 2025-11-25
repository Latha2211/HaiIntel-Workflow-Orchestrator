"""
Integration tests for the complete workflow
"""

import pytest
import httpx
import asyncio
from datetime import datetime


BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_duplicate_payment_workflow():
    """Test complete workflow for duplicate payment issue"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "customerId": "99876",
            "channel": "whatsapp",
            "message": "My credit card payment was deducted twice yesterday."
        }
        
        response = await client.post(
            f"{BASE_URL}/webhook/customer-issue",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] is True
        assert "ticket_id" in data
        assert data["category"] == "duplicate_payment"
        assert data["sentiment"] in ["negative", "very_negative"]
        assert data["priority"] in ["high", "medium"]
        assert len(data["channels_notified"]) >= 2
        
        print(f"\n✅ Ticket created: {data['ticket_id']}")
        print(f"   Category: {data['category']}")
        print(f"   Sentiment: {data['sentiment']}")
        print(f"   Priority: {data['priority']}")
        print(f"   Channels: {', '.join(data['channels_notified'])}")


@pytest.mark.asyncio
async def test_account_access_workflow():
    """Test workflow for account access issue"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "customerId": "12345",
            "channel": "email",
            "message": "I cannot log into my account. It says my password is incorrect."
        }
        
        response = await client.post(
            f"{BASE_URL}/webhook/customer-issue",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["category"] == "account_access"
        assert data["priority"] == "high"


@pytest.mark.asyncio
async def test_general_inquiry_workflow():
    """Test workflow for general inquiry"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "customerId": "54321",
            "channel": "sms",
            "message": "What are your business hours?"
        }
        
        response = await client.post(
            f"{BASE_URL}/webhook/customer-issue",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["category"] == "general_inquiry"
        assert data["priority"] == "low"


@pytest.mark.asyncio
async def test_ticket_retrieval():
    """Test ticket retrieval after creation"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Create ticket first
        payload = {
            "customerId": "67890",
            "channel": "email",
            "message": "Test issue for retrieval"
        }
        
        create_response = await client.post(
            f"{BASE_URL}/webhook/customer-issue",
            json=payload
        )
        
        ticket_id = create_response.json()["ticket_id"]
        
        # Retrieve ticket
        get_response = await client.get(f"{BASE_URL}/tickets/{ticket_id}")
        
        assert get_response.status_code == 200
        ticket_data = get_response.json()
        
        assert ticket_data["ticket_id"] == ticket_id
        assert ticket_data["customer_id"] == "67890"


@pytest.mark.asyncio
async def test_analytics_dashboard():
    """Test analytics dashboard endpoint"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/analytics/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify analytics structure
        assert "summary" in data
        assert "by_category" in data
        assert "by_sentiment" in data
        assert "by_channel" in data
        
        print(f"\n📊 Analytics Summary:")
        print(f"   Total Issues: {data['summary']['total_issues']}")
        print(f"   Last 24h: {data['summary']['last_24h']}")
        print(f"   Resolution Rate: {data['summary']['resolution_rate']}%")


@pytest.mark.asyncio
async def test_multiple_issues():
    """Test handling multiple issues in sequence"""
    test_cases = [
        {
            "customerId": "TEST001",
            "channel": "whatsapp",
            "message": "I need a refund for order #12345"
        },
        {
            "customerId": "TEST002",
            "channel": "email",
            "message": "Your app is not working on my phone"
        },
        {
            "customerId": "TEST003",
            "channel": "sms",
            "message": "Can you add dark mode to the app?"
        }
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, payload in enumerate(test_cases, 1):
            response = await client.post(
                f"{BASE_URL}/webhook/customer-issue",
                json=payload
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            print(f"\n✅ Issue {i}/3 processed: {data['ticket_id']}")
            
            # Small delay between requests
            await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling with invalid input"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Missing required field
        payload = {
            "customerId": "ERROR001",
            "channel": "email"
            # Missing 'message' field
        }
        
        response = await client.post(
            f"{BASE_URL}/webhook/customer-issue",
            json=payload
        )
        
        assert response.status_code == 422  # Validation error


def run_manual_test():
    """Run a manual integration test"""
    print("\n" + "="*60)
    print("🧪 HaiIntel Workflow - Manual Integration Test")
    print("="*60)
    
    # Test data
    test_issue = {
        "customerId": "MANUAL_TEST_001",
        "channel": "whatsapp",
        "message": "I was charged twice for the same subscription. This is very frustrating!"
    }
    
    print(f"\n📝 Test Issue:")
    print(f"   Customer: {test_issue['customerId']}")
    print(f"   Channel: {test_issue['channel']}")
    print(f"   Message: {test_issue['message']}")
    
    # Run async test
    async def execute():
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/webhook/customer-issue",
                json=test_issue
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ SUCCESS!")
                print(f"\n📋 Response:")
                print(f"   Ticket ID: {data['ticket_id']}")
                print(f"   Category: {data['category']}")
                print(f"   Sentiment: {data['sentiment']}")
                print(f"   Priority: {data['priority']}")
                print(f"   Channels Notified: {', '.join(data['channels_notified'])}")
                print(f"   Estimated Resolution: {data['estimated_resolution']}")
            else:
                print(f"\n❌ FAILED!")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.text}")
    
    asyncio.run(execute())
    print("\n" + "="*60)


if __name__ == "__main__":
    # Run manual test when executed directly
    run_manual_test()
