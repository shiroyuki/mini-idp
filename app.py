""" Bootstrap Script for FastAPI CLI """
from dotenv import load_dotenv
load_dotenv()  # Try to load .env as soon as possible before the Imagination container is requested.
# noinspection PyUnresolvedReferences
from midp.web import app