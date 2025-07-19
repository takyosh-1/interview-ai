import json
import os
import logging
from datetime import datetime
from config.settings import FEEDBACK_DATA_FILE, EMPLOYEE_DATA_FILE, CONVERSATION_DATA_FILE, CUSTOM_CHATBOT_DATA_FILE, DEFAULT_CHATBOT_DATA_FILE, EMPLOYEE_PROFILE_DATA_FILE

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

def load_default_chatbot_data():
    """Load default chatbot data from JSON file"""
    try:
        if os.path.exists(DEFAULT_CHATBOT_DATA_FILE):
            with open(DEFAULT_CHATBOT_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} default chatbots")
                return data
        else:
            logger.info("Default chatbot data file not found, initializing with 3 core chatbots")
    except Exception as e:
        logger.error(f"Error loading default chatbot data: {e}")
    
    default_data = {
        "default_業務": {
            "id": "default_業務",
            "type": "業務",
            "name": "業務について聞くチャットボット",
            "initial_message": "業務に関するご相談をお聞かせください。どのようなことでお困りでしょうか？",
            "system_prompt": "あなたは業務に関する相談を専門とするチャットボットです。業務の効率化、プロセス改善、業務上の課題について親身に相談に乗ってください。",
            "created_at": datetime.now().isoformat(),
            "is_default": True
        },
        "default_人間関係": {
            "id": "default_人間関係", 
            "type": "人間関係",
            "name": "人間関係について聞くチャットボット",
            "initial_message": "職場での人間関係についてお聞かせください。どのようなことが気になっていますか？",
            "system_prompt": "あなたは職場の人間関係に関する相談を専門とするチャットボットです。同僚、上司、部下との関係性について親身に相談に乗ってください。",
            "created_at": datetime.now().isoformat(),
            "is_default": True
        },
        "default_キャリア": {
            "id": "default_キャリア",
            "type": "キャリア", 
            "name": "キャリアについて聞くチャットボット",
            "initial_message": "キャリアについてのご相談をお聞かせください。将来のことで何か気になることはありますか？",
            "system_prompt": "あなたはキャリア開発に関する相談を専門とするチャットボットです。スキルアップ、昇進、転職、将来の目標について親身に相談に乗ってください。",
            "created_at": datetime.now().isoformat(),
            "is_default": True
        }
    }
    save_default_chatbot_data(default_data)
    return default_data

def save_default_chatbot_data(data):
    """Save default chatbot data to JSON file"""
    try:
        with open(DEFAULT_CHATBOT_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} default chatbots")
    except Exception as e:
        logger.error(f"Error saving default chatbot data: {e}")
