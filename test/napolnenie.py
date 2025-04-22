import random
import asyncio
import aiohttp

API_URL = "http://localhost:8000/profile/save"
NUM_PROFILES = 100

names_male = ['Alex', 'Ivan', 'Sergey', 'Dmitry', 'Nikolay', 'Andrey', 'Pavel', 'Roman', 'Mikhail', 'Oleg']
names_female = ['Maria', 'Anna', 'Olga', 'Elena', 'Natalia', 'Irina', 'Tatiana', 'Svetlana', 'Ekaterina', 'Lyudmila']
cities = ['Moscow', 'Saint Petersburg', 'Kazan', 'Novosibirsk', 'Sochi', 'Rostov-on-Don', 'Yekaterinburg', 'Krasnodar', 'Vladivostok', 'Kaliningrad']

about_templates = [
    "Hi, I'm {name} from {city}. I love {hobby} and I'm looking for someone who enjoys {interest}.",
    "Hey there! I'm {name}. {fun_fact} I live in {city} and I enjoy {hobby}.",
    "{name} here. Based in {city}. Passionate about {interest} and always curious about {fun_fact}.",
    "Hello! I'm {name}, a {age}-year-old from {city}. I spend my weekends {hobby}.",
    "Greetings! I’m {name} and I’m into {interest}. Let's connect if you're from {city} too!"
]

hobbies = ['hiking', 'reading books', 'playing chess', 'traveling', 'cooking', 'watching movies', 'painting', 'cycling', 'coding', 'dancing']
interests = ['technology', 'psychology', 'history', 'art', 'music', 'sports', 'photography', 'science fiction', 'philosophy']
fun_facts = ['I once climbed a volcano!', 'I’ve visited 20 countries.', 'I can play three instruments.', 'I bake my own bread.', 'I’m learning Japanese.']

def generate_about(name, city, age):
    template = random.choice(about_templates)
    return template.format(
        name=name,
        city=city,
        age=age,
        hobby=random.choice(hobbies),
        interest=random.choice(interests),
        fun_fact=random.choice(fun_facts)
    )

def generate_profile(user_id: int) -> dict:
    gender = random.choice(['male', 'female'])
    name = random.choice(names_male if gender == 'male' else names_female)
    interesting_gender = random.choice(['male', 'female'])
    city = random.choice(cities)
    age = random.randint(18, 45)
    about = generate_about(name, city, age)

    return {
        "user_id": user_id,
        "name": name,
        "gender": gender,
        "city": city,
        "age": age,
        "interesting_gender": interesting_gender,
        "about": about
    }

async def send_profile(session, profile):
    async with session.post(API_URL, json=profile) as resp:
        if resp.status != 200:
            text = await resp.text()
            print(f"❌ Error {resp.status} for user {profile['user_id']}: {text}")
        else:
            print(f"✅ Created user {profile['user_id']} - {profile['name']}")

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(1, NUM_PROFILES + 1):
            profile = generate_profile(user_id=1000 + i)
            tasks.append(send_profile(session, profile))
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
