import asyncio
import httpx

async def add_swipe():
    url = "http://localhost:8000/swipe/add"
    payload = {
        "from_user_id": 9000,
        "to_user_id": 1651668580,
        "action": "like",  # / "question", "dislike"
        "message": None  # "....." при action == "question"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        print("Status:", response.status_code)
        print("Response:", response.json())

if __name__ == "__main__":
    asyncio.run(add_swipe())
