import asyncio
import httpx
import sys
import time

# Configuration
API_URL = "http://localhost:8000"
TIMEOUT = 5.0

async def check_health():
    """Check API Health"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{API_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Online: {data['status']}")
                print(f"   - Redis: {data['services']['cache']}")
                return True
            else:
                print(f"❌ API Unhealthy: {response.status_code}")
                return False
    except httpx.ConnectError:
        print("❌ API Offline: Could not connect to localhost:8000")
        return False
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False

async def check_search():
    """Check Zoo Functionality (NCBI connectivity simulation)"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            start = time.time()
            response = await client.get(f"{API_URL}/api/v1/species/search?query=Tiger")
            elapsed = time.time() - start

            if response.status_code == 200:
                data = response.json()
                print(f"🦁 Zoo Search: Functional ({elapsed:.2f}s)")
                print(f"   - Found: {data['results'][0]['common_name']}")
                return True
            else:
                print(f"⚠️ Search Failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"⚠️ Search Error: {e}")
        return False

async def main():
    print("\n🔍 Checking GeneticFrames Zoo Status...\n")

    api_ok = await check_health()
    if not api_ok:
        sys.exit(1)

    zoo_ok = await check_search()

    print("\n" + "="*30)
    if api_ok and zoo_ok:
        print("🚀 STATUS: ZOO OPEN")
    else:
        print("🚧 STATUS: MAINTENANCE REQUIRED")
    print("="*30 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
