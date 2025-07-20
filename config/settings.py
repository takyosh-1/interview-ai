import os
import logging
import string
import random
import traceback
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

SHARED_DATA_DIR = "/tmp/interview_ai_shared"
FEEDBACK_DATA_FILE = f"{SHARED_DATA_DIR}/feedback_data.json"
EMPLOYEE_DATA_FILE = f"{SHARED_DATA_DIR}/employee_data.json"
CONVERSATION_DATA_FILE = f"{SHARED_DATA_DIR}/conversation_data.json"
CUSTOM_CHATBOT_DATA_FILE = f"{SHARED_DATA_DIR}/custom_chatbot_data.json"
DEFAULT_CHATBOT_DATA_FILE = f"{SHARED_DATA_DIR}/default_chatbot_data.json"
EMPLOYEE_PROFILE_DATA_FILE = f"{SHARED_DATA_DIR}/employee_profile_data.json"

os.makedirs(SHARED_DATA_DIR, exist_ok=True)

def generate_random_string(length=6):
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choices(characters, k=length))

session_url_mapping = {}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/interview_ai_shared/app.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

employee_data = {}
running_servers = {}
feedback_data = []
employee_access_tokens = {}

logger.info(f"Shared data directory initialized: {SHARED_DATA_DIR}")

import openai
logger.info(f"OpenAI SDK version: {openai.__version__}")


global_model = "gpt-4o"
client = None

# Log Azure OpenAI environment variables
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
key = os.getenv("AZURE_OPENAI_KEY")
logger.info(f"AZURE openai endpoint: {endpoint}")
logger.info(f"AZURE openai key: {key}")

# Log module info for AzureOpenAI (to detect wrong import)
logger.info(f"AzureOpenAI class from module: {AzureOpenAI.__module__}")

# Log proxy-related env vars
for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    if os.getenv(var):
        logger.warning(f"Environment variable {var} is set: {os.getenv(var)}")

try:
    if key and endpoint:
        logger.info("Initializing Azure OpenAI client...")

        # Log input arguments
        init_kwargs = {
            "api_key": key,
            "azure_endpoint": endpoint,
            "api_version": "2024-12-01-preview"
        }
        logger.info(f"Client init kwargs: {init_kwargs}")

        client = AzureOpenAI(**init_kwargs)

        logger.info("Azure OpenAI client initialized successfully")
    else:
        logger.warning("Azure OpenAI credentials not found. Running in demo mode.")
except Exception as e:
    logger.error("Failed to initialize Azure OpenAI client:")
    logger.error(traceback.format_exc())
    logger.warning("Running in demo mode without AI functionality.")
