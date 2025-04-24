import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_FSM = os.getenv("REDIS_FSM")

API_URL = os.getenv("API_URL")

NUMBER_OF_RECS = os.getenv("NUMBER_OF_RECS")