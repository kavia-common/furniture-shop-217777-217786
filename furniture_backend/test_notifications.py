"""
Test script to demonstrate the notifications system functionality.
This script shows how to use the notification endpoints and SSE streaming.
"""
import asyncio
import json
import httpx

BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_123"

async def test_notifications_system():
    """
    Test the complete notifications workflow.
    """
    async with httpx.AsyncClient() as client:
        headers = {"X-User-Id": TEST_USER_ID}
        
        print("🔔 Testing Furniture Shop Notifications System")
        print("=" * 50)
        
        # 1. Subscribe to notifications
        print("\n1. Subscribing to notifications...")
        try:
            response = await client.post(f"{BASE_URL}/notifications/subscribe", headers=headers)
            if response.status_code == 200:
                print(f"✅ Subscribed: {response.json()}")
            else:
                print(f"❌ Subscription failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return
        
        # 2. List current notifications (should be empty)
        print("\n2. Checking existing notifications...")
        try:
            response = await client.get(f"{BASE_URL}/notifications", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"📋 Current notifications: {data['total']} total, {data['unread_count']} unread")
            else:
                print(f"❌ Failed to get notifications: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting notifications: {e}")
        
        # 3. Publish test notifications
        print("\n3. Publishing test notifications...")
        test_notifications = [
            {
                "user_id": TEST_USER_ID,
                "type": "order_update",
                "title": "Order Confirmed",
                "message": "Your order #12345 for Ocean Blue Sofa has been confirmed!",
                "data": {"order_id": "12345", "product_name": "Ocean Blue Sofa"}
            },
            {
                "user_id": TEST_USER_ID,
                "type": "price_drop",
                "title": "Price Drop Alert",
                "message": "The Amber Accent Chair is now 20% off!",
                "data": {"product_id": 2, "old_price": 249.50, "new_price": 199.60}
            },
            {
                "user_id": TEST_USER_ID,
                "type": "new_arrival",
                "title": "New Arrival",
                "message": "Check out our new Nordic Dining Table collection!",
                "data": {"category": "Dining", "product_count": 5}
            }
        ]
        
        for notification in test_notifications:
            try:
                response = await client.post(f"{BASE_URL}/notifications/publish", json=notification)
                if response.status_code == 201:
                    result = response.json()
                    print(f"✅ Published {notification['type']}: {result['notification_ids']}")
                else:
                    print(f"❌ Failed to publish {notification['type']}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error publishing notification: {e}")
        
        # 4. Check notifications again
        print("\n4. Checking notifications after publishing...")
        try:
            response = await client.get(f"{BASE_URL}/notifications", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"📋 Updated notifications: {data['total']} total, {data['unread_count']} unread")
                for i, notif in enumerate(data['items'][:3], 1):
                    print(f"   {i}. [{notif['type']}] {notif['title']} - {notif['message'][:50]}...")
            else:
                print(f"❌ Failed to get notifications: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting notifications: {e}")
        
        # 5. Test SSE streaming (simulate for a few seconds)
        print("\n5. Testing SSE stream (5-second simulation)...")
        try:
            # Start SSE stream in background
            async def listen_to_stream():
                async with httpx.AsyncClient() as stream_client:
                    headers_stream = {**headers, "Accept": "text/event-stream"}
                    async with stream_client.stream("GET", f"{BASE_URL}/notifications/stream", headers=headers_stream) as response:
                        if response.status_code == 200:
                            print("🔄 Connected to SSE stream...")
                            async for line in response.aiter_lines():
                                if line.startswith("data: "):
                                    try:
                                        data = json.loads(line[6:])  # Remove "data: " prefix
                                        if data.get("type") == "connected":
                                            print(f"✅ {data['message']}")
                                        else:
                                            print(f"📨 Received: [{data.get('type')}] {data.get('title')}")
                                    except json.JSONDecodeError:
                                        pass
                        else:
                            print(f"❌ SSE connection failed: {response.status_code}")
            
            # Start streaming task
            stream_task = asyncio.create_task(listen_to_stream())
            
            # Send a real-time notification while streaming
            await asyncio.sleep(1)
            print("📤 Sending real-time notification...")
            realtime_notif = {
                "user_id": TEST_USER_ID,
                "type": "order_update",
                "title": "Order Shipped",
                "message": "Your Ocean Blue Sofa has been shipped and will arrive tomorrow!",
                "data": {"order_id": "12345", "tracking_number": "TRK789"}
            }
            
            await client.post(f"{BASE_URL}/notifications/publish", json=realtime_notif)
            
            # Let stream run for a bit then cancel
            await asyncio.sleep(2)
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                print("🔌 SSE stream closed")
                
        except Exception as e:
            print(f"❌ SSE stream error: {e}")
        
        # 6. Get usage guide
        print("\n6. Getting WebSocket usage guide...")
        try:
            response = await client.get(f"{BASE_URL}/notifications/docs/websocket-usage")
            if response.status_code == 200:
                guide = response.json()
                print(f"📖 Usage guide: {guide['type']} - {guide['description']}")
                print(f"🔗 Endpoint: {guide['endpoint']}")
            else:
                print(f"❌ Failed to get usage guide: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting usage guide: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Notifications system test completed!")
        print("\nEndpoints available:")
        print("- POST /notifications/subscribe - Subscribe to notifications")
        print("- GET /notifications/stream - SSE stream for real-time notifications")
        print("- POST /notifications/publish - Publish notifications (dev/admin)")
        print("- GET /notifications - List notifications")
        print("- PATCH /notifications/{id}/read - Mark notification as read")
        print("- POST /notifications/mark-all-read - Mark all as read")


if __name__ == "__main__":
    print("Starting notifications system test...")
    print("Note: Make sure the FastAPI server is running on http://localhost:8000")
    print("You can start it with: uvicorn src.api.main:app --host 0.0.0.0 --port 8000")
    print()
    
    try:
        asyncio.run(test_notifications_system())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
