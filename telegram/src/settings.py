import os
from dotenv import load_dotenv


def get_or_raise(env_name: str) -> str:
    value = os.getenv(env_name)
    if value is None:
        raise ValueError(f"Environment variable {env_name} is not set")
    return value


load_dotenv()

LINODE_API_KEY = get_or_raise("LINODE_API_KEY")
BOT_API_KEY = get_or_raise("BOT_API_KEY")
ALLOWED_CHAT_IDS = get_or_raise("ALLOWED_CHAT_IDS").split(",")
STACKSCRIPT_ID = int(get_or_raise("STACKSCRIPT_ID"))
SHADOWSOCKS_PASSWORD = get_or_raise("SHADOWSOCKS_PASSWORD")
