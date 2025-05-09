import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_FSM = os.getenv("REDIS_FSM")

KAFKA_SWIPES_TOPIC = os.getenv("KAFKA_SWIPES_TOPIC")
KAFKA_GEO_NOTIFICATIONS_TOPIC = os.getenv("KAFKA_GEO_NOTIFICATIONS_TOPIC")
KAFKA_VIDEO_NOTIFICATIONS_TOPIC = os.getenv("KAFKA_VIDEO_NOTIFICATIONS_TOPIC")

API_URL = os.getenv("API_URL")

API_SECRET_KEY = os.getenv("API_SECRET_KEY")
