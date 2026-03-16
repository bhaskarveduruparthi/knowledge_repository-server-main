import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.office365.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')        # ✅ reads from .env
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')        # ✅ reads from .env
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')


    # Redis cache settings
    CACHE_TYPE                = 'redis'
    CACHE_REDIS_URL           = 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT     = 300  # 5 minutes