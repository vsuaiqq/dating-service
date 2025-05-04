import asyncio
import httpx

async def add_swipe():
    url = "http://localhost:8000/swipe"
    headers = {
        'X-Telegram-Username': 'heavyrain8'
    }
    payload = {
        "from_user_id": 6377453286,
        "to_user_id": 1651668580,
        "action": "like",  # / "question", "dislike"
        "message": None  # "....." при action == "question"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        print("Status:", response.status_code)
        print("Response:", response.json())

if __name__ == "__main__":
    asyncio.run(add_swipe())
