import asyncio
import httpx

async def save_profile():
    url = "http://localhost:8000/profile/save"

    payload = {
        "user_id": 9000,
        "name": "Alice",
        "gender": "female",
        "city": "Moscow",
        "age": 20,
        "interesting_gender": "male",
        "about": "Шаболда"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        print("Status:", response.status_code)
        print("Response:", response.json())

if __name__ == "__main__":
    asyncio.run(save_profile())
