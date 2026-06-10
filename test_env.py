import os
from dotenv import load_dotenv

load_dotenv()
print("STRIPE_SECRET_KEY =", "OK" if os.getenv("STRIPE_SECRET_KEY") else "MISSING")
