import json
import os
from config.settings import FEEDBACK_DATA_FILE, EMPLOYEE_DATA_FILE

def load_shared_feedback_data():
    try:
        if os.path.exists(FEEDBACK_DATA_FILE):
            with open(FEEDBACK_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading feedback data: {e}")
    return []

def save_shared_feedback_data(data):
    try:
        with open(FEEDBACK_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving feedback data: {e}")

def load_shared_employee_data():
    try:
        if os.path.exists(EMPLOYEE_DATA_FILE):
            with open(EMPLOYEE_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading employee data: {e}")
    return {}

def save_shared_employee_data(data):
    try:
        with open(EMPLOYEE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving employee data: {e}")
