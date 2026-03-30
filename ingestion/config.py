import os
from dotenv import load_dotenv

load_dotenv()

def get_config():
    return {
        "DST_BUCKET": os.getenv("DST_BUCKET"),
        "DST_REGION": os.getenv("DST_REGION"),
        "DST_PROFILE": os.getenv("DST_PROFILE"),
        "DST_ACCESS_KEY" :os.getenv("DST_ACCESS_KEY"),
        "DST_SECRET_KEY" : os.getenv("DST_SECRET_KEY"),
        "SRC_BUCKET": os.getenv("SRC_BUCKET"),
        "SRC_REGION": os.getenv("SRC_REGION"),
        "SRC_ACCESS_KEY" : os.getenv("SRC_ACCESS_KEY"),
        "SRC_SECRET_KEY" : os.getenv("SRC_SECRET_KEY")


    }