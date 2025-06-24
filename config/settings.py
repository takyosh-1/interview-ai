import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

SHARED_DATA_DIR = "/tmp/interview_ai_shared"
FEEDBACK_DATA_FILE = f"{SHARED_DATA_DIR}/feedback_data.json"
EMPLOYEE_DATA_FILE = f"{SHARED_DATA_DIR}/employee_data.json"

employee_data = {}
running_servers = {}
feedback_data = []
employee_access_tokens = {}

os.makedirs(SHARED_DATA_DIR, exist_ok=True)

global_model = "gpt-4o"
client = None

try:
    if os.getenv("AZURE_OPENAI_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-12-01-preview",
        )
        print("Azure OpenAI client initialized successfully")
    else:
        print("Warning: Azure OpenAI credentials not found. Running in demo mode.")
except Exception as e:
    print(f"Warning: Failed to initialize Azure OpenAI client: {e}")
    print("Running in demo mode without AI functionality.")
