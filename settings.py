from dotenv import load_dotenv
import os
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = "@CHIZAI_BOT"
HF_TOKEN = os.getenv("HF_TOKEN")
GROQ_TOKEN = os.getenv("GROQ_API_KEY")

FIRST_BALANCE = 2000

ADMIN_IDS = {51433765171}