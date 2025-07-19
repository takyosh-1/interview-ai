import os
import logging
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

global_model = "gpt-4o"
client = None

logger.info(f"AZURE openai endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
logger.info(f"AZURE openai key: {os.getenv('AZURE_OPENAI_KEY')}")

try:
    if os.getenv("AZURE_OPENAI_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
        logger.info("Initializing Azure OpenAI client...")
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-12-01-preview",
        )
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-12-01-preview",
        )

        logger.info("Azure OpenAI client initialized successfully")
    else:
        logger.warning("Azure OpenAI credentials not found. Running in demo mode.")
except Exception as e:
    logger.error(f"Failed to initialize Azure OpenAI client: {e}")
    logger.warning("Running in demo mode without AI functionality.")
