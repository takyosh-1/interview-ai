import json
import os
import logging
from config.settings import FEEDBACK_DATA_FILE, EMPLOYEE_DATA_FILE, CONVERSATION_DATA_FILE, CUSTOM_CHATBOT_DATA_FILE, EMPLOYEE_PROFILE_DATA_FILE

logger = logging.getLogger(__name__)

def load_shared_feedback_data():
    try:
        if os.path.exists(FEEDBACK_DATA_FILE):
            with open(FEEDBACK_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} feedback entries from {FEEDBACK_DATA_FILE}")
                return data
        else:
            logger.info(f"Feedback data file not found: {FEEDBACK_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error loading feedback data: {e}")
    return []

def save_shared_feedback_data(data):
    try:
        with open(FEEDBACK_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} feedback entries to {FEEDBACK_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving feedback data: {e}")

def load_shared_employee_data():
    try:
        if os.path.exists(EMPLOYEE_DATA_FILE):
            with open(EMPLOYEE_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} employee records from {EMPLOYEE_DATA_FILE}")
                return data
        else:
            logger.info(f"Employee data file not found: {EMPLOYEE_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error loading employee data: {e}")
    return {}

def save_shared_employee_data(data):
    try:
        with open(EMPLOYEE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} employee records to {EMPLOYEE_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving employee data: {e}")

def load_conversation_data():
    try:
        if os.path.exists(CONVERSATION_DATA_FILE):
            with open(CONVERSATION_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} conversation records from {CONVERSATION_DATA_FILE}")
                return data
        else:
            logger.info(f"Conversation data file not found: {CONVERSATION_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error loading conversation data: {e}")
    return {}

def save_conversation_data(data):
    try:
        with open(CONVERSATION_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} conversation records to {CONVERSATION_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving conversation data: {e}")

def load_custom_chatbot_data():
    try:
        if os.path.exists(CUSTOM_CHATBOT_DATA_FILE):
            with open(CUSTOM_CHATBOT_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} custom chatbot records from {CUSTOM_CHATBOT_DATA_FILE}")
                return data
        else:
            logger.info(f"Custom chatbot data file not found: {CUSTOM_CHATBOT_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error loading custom chatbot data: {e}")
    return {}

def save_custom_chatbot_data(data):
    try:
        with open(CUSTOM_CHATBOT_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} custom chatbot records to {CUSTOM_CHATBOT_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving custom chatbot data: {e}")

def load_employee_profile_data():
    try:
        if os.path.exists(EMPLOYEE_PROFILE_DATA_FILE):
            with open(EMPLOYEE_PROFILE_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} employee profile records from {EMPLOYEE_PROFILE_DATA_FILE}")
                return data
        else:
            logger.info(f"Employee profile data file not found: {EMPLOYEE_PROFILE_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error loading employee profile data: {e}")
    return {}

def save_employee_profile_data(data):
    try:
        with open(EMPLOYEE_PROFILE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} employee profile records to {EMPLOYEE_PROFILE_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving employee profile data: {e}")
