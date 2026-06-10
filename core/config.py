# core/config.py
# This file loads your secret keys from the .env file
# so you never hardcode them in your code.
from dotenv import load_dotenv
import os
load_dotenv()  # reads your .env file

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
