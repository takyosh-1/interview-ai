import uuid
import time
import logging
from datetime import datetime
from flask import render_template, request, Response, stream_with_context, jsonify

from config.settings import client, global_model, employee_data
from models.data_manager import load_shared_feedback_data, save_shared_feedback_data, load_conversation_data, save_conversation_data, load_custom_chatbot_data
from services.ai_service import get_chatbot_system_prompt

logger = logging.getLogger(__name__)

def handle_employee_home(session_id):
    """Handle employee chatbot home page"""
    if session_id not in employee_data:
        return "Session not found", 404
    
    session_info = employee_data[session_id]
    chatbot_type = session_info.get('chatbot_type', '業務')
    chatbot_id = session_info.get('chatbot_id', '')
    session_name = session_info.get('session_name', f"{chatbot_type}チャットボット")
    
    logger.info(f"Loading chatbot home for {chatbot_type} - ID: {session_id}")
    
    initial_message = None
    if chatbot_id and chatbot_id.startswith("custom:"):
        custom_id = chatbot_id.replace("custom:", "")
        custom_chatbots = load_custom_chatbot_data()
        if custom_id in custom_chatbots:
            initial_message = custom_chatbots[custom_id]['initial_message']
    elif chatbot_id and chatbot_id.startswith("default:"):
        from models.data_manager import load_default_chatbot_data
        default_type = chatbot_id.replace("default:", "")
        default_chatbots = load_default_chatbot_data()
        default_key = f"default_{default_type}"
        if default_key in default_chatbots:
            initial_message = default_chatbots[default_key]['initial_message']
    
    return render_template("employee_chat.html", 
                         chatbot_type=chatbot_type,
                         session_name=session_name,
                         session_id=session_id,
                         initial_message=initial_message)

def handle_employee_chat(session_id):
    """Handle employee chat API endpoint"""
    if session_id not in employee_data:
        return jsonify({"error": "Session not found"}), 404
    
    session_info = employee_data[session_id]
    chatbot_type = session_info.get('chatbot_type', '業務')
    chatbot_id = session_info.get('chatbot_id', '')
    session_name = session_info.get('session_name', f"{chatbot_type}チャットボット")
    data = request.get_json()
    user_message = data.get("message", "").strip()
    
    logger.info(f"Received chat message for {chatbot_type}: {len(user_message)} characters")
    
    if not user_message:
        logger.warning(f"Empty message received for {chatbot_type}")
        return jsonify({"error": "メッセージが空です"}), 400
    
    conversation_data = load_conversation_data()
    if session_id not in conversation_data:
        conversation_data[session_id] = {
            'chatbot_type': chatbot_type,
            'session_name': session_name,
            'messages': [],
            'created_at': datetime.now().isoformat()
        }
    
    conversation_data[session_id]['messages'].append({
        'role': 'user',
        'content': user_message,
        'timestamp': datetime.now().isoformat()
    })
    
    feedback_entry = {
        'id': str(uuid.uuid4()),
        'session_id': session_id,
        'chatbot_type': chatbot_type,
        'session_name': session_name,
        'user_message': user_message,
        'timestamp': datetime.now().isoformat(),
        'ai_response': ''
    }
    
    employee_profile = None
    if session_info.get('employee_profile'):
        employee_profile = session_info['employee_profile']
    elif session_info.get('employee_id'):
        from models.data_manager import load_employee_profile_data
        profiles = load_employee_profile_data()
        employee_profile = profiles.get(session_info['employee_id'])
    
    logger.info(f"Employee profile for system prompt: {employee_profile is not None}")
    system_prompt = get_chatbot_system_prompt(chatbot_type, chatbot_id, employee_profile)

    def stream():
        logger.info(f"Client connected: {client is not None}")
        try:
            if client is None:
                logger.info(f"Generating demo response for {chatbot_type} (no AI client available)")
                demo_response = f"""ありがとうございます。{chatbot_type}に関するご相談ですね。

                {user_message}について、お話しいただきありがとうございます。

                現在はデモモードで動作しているため、実際のAI応答は提供できませんが、本番環境では{chatbot_type}に特化した詳細なアドバイスを提供します。

                何か他にお聞かせいただきたいことがあれば、お気軽にお話しください。"""
                
                conversation_data[session_id]['messages'].append({
                    'role': 'assistant',
                    'content': demo_response,
                    'timestamp': datetime.now().isoformat()
                })
                save_conversation_data(conversation_data)
                
                feedback_entry['ai_response'] = demo_response
                current_feedback = load_shared_feedback_data()
                current_feedback.append(feedback_entry)
                save_shared_feedback_data(current_feedback)
                logger.info(f"Saved demo feedback entry for {chatbot_type}")
                
                for char in demo_response:
                    yield char
                    time.sleep(0.02)
            else:
                logger.info(f"Generating AI response for {chatbot_type} using {global_model}")
                
                messages = [{"role": "system", "content": system_prompt}]
                
                recent_messages = conversation_data[session_id]['messages'][-20:]
                for msg in recent_messages:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
                
                response = client.chat.completions.create(
                    model=global_model,
                    messages=messages,
                    stream=True
                )
                
                ai_response = ""
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        ai_response += content
                        yield content 
                
                conversation_data[session_id]['messages'].append({
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': datetime.now().isoformat()
                })
                save_conversation_data(conversation_data)
                
                feedback_entry['ai_response'] = ai_response
                current_feedback = load_shared_feedback_data()
                current_feedback.append(feedback_entry)
                save_shared_feedback_data(current_feedback)
                logger.info(f"Saved AI feedback entry for {chatbot_type} ({len(ai_response)} characters)")
                
        except Exception as e:
            logger.error(f"Error in chat stream for {chatbot_type}: {e}")
            error_message = f"申し訳ございません。エラーが発生しました: {str(e)}"
            
            conversation_data[session_id]['messages'].append({
                'role': 'assistant',
                'content': error_message,
                'timestamp': datetime.now().isoformat()
            })
            save_conversation_data(conversation_data)
            
            feedback_entry['ai_response'] = error_message
            current_feedback = load_shared_feedback_data()
            current_feedback.append(feedback_entry)
            save_shared_feedback_data(current_feedback)
            yield error_message
    
    return Response(stream_with_context(stream()), mimetype='text/plain')

def create_employee_session(session_id, session_token):
    """Create a new employee session with URL mapping"""
    from config.settings import session_url_mapping
    
    if session_id not in employee_data:
        logger.error(f"Session ID {session_id} not found in employee data")
        return False
    
    session_info = employee_data[session_id]
    session_url_mapping[session_token] = session_id
    
    logger.info(f"Created employee session for {session_info.get('chatbot_type', 'unknown')} with token {session_token}")
    return True
