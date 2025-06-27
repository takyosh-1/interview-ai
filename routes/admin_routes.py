import uuid
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify

from config.settings import employee_data, running_servers
from models.data_manager import load_shared_feedback_data, load_shared_employee_data, save_shared_employee_data
from services.employee_server import start_employee_server
from services.ai_service import generate_summary_with_ai

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/")
def admin_home():
    return render_template("admin_home.html")

@admin_bp.route("/create-employee-url", methods=["POST"])
def create_employee_url():
    data = request.get_json()
    chatbot_type = data.get("chatbot_type", "").strip()
    session_name = data.get("session_name", "").strip()
    
    logger.info(f"Creating chatbot URL for type: {chatbot_type}, session: {session_name}")
    
    if not chatbot_type:
        logger.warning(f"Invalid chatbot URL creation request: chatbot_type='{chatbot_type}'")
        return jsonify({"success": False, "error": "チャットボットの種類を選択してください"})
    
    session_id = str(uuid.uuid4())
    base_port = 5001
    port = base_port
    
    while port in [server['port'] for server in running_servers.values()]:
        port += 1
    
    display_name = session_name if session_name else f"{chatbot_type}チャットボット"
    
    employee_data[session_id] = {
        'chatbot_type': chatbot_type,
        'session_name': display_name,
        'created_at': datetime.now().isoformat(),
        'port': port
    }
    
    save_shared_employee_data(employee_data)
    
    if start_employee_server(session_id, port):
        employee_url = f"http://localhost:{port}"
        logger.info(f"Successfully created chatbot URL for {chatbot_type}: {employee_url}")
        return jsonify({
            "success": True, 
            "employee_url": employee_url,
            "port": port,
            "session_id": session_id,
            "chatbot_type": chatbot_type
        })
    else:
        logger.error(f"Failed to start chatbot server for {chatbot_type} on port {port}")
        return jsonify({"success": False, "error": "チャットボットサーバーの起動に失敗しました"})

@admin_bp.route("/employees")
def list_employees():
    logger.info("Fetching chatbot session list")
    current_employee_data = load_shared_employee_data()
    
    sessions = []
    for session_id, session_data in current_employee_data.items():
        server_info = running_servers.get(session_id, {})
        sessions.append({
            'id': session_id,
            'chatbot_type': session_data.get('chatbot_type', '不明'),
            'session_name': session_data.get('session_name', '不明'),
            'created_at': session_data['created_at'],
            'port': session_data.get('port'),
            'url': server_info.get('url'),
            'status': 'running' if session_id in running_servers else 'stopped'
        })
    return jsonify(sessions)

@admin_bp.route("/dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@admin_bp.route("/data")
def admin_data():
    chatbot_filter = request.args.get('chatbot_type', 'all')
    session_filter = request.args.get('session', 'all')
    logger.info(f"Fetching admin data with filters - chatbot_type: {chatbot_filter}, session: {session_filter}")
    
    current_feedback = load_shared_feedback_data()
    
    filtered_data = current_feedback
    if chatbot_filter != 'all':
        filtered_data = [f for f in filtered_data if f.get('chatbot_type') == chatbot_filter]
    if session_filter != 'all':
        filtered_data = [f for f in filtered_data if f.get('session_id') == session_filter]
    
    chatbot_types = list(set([f.get('chatbot_type', '不明') for f in current_feedback]))
    
    unique_sessions = {}
    for f in current_feedback:
        session_id = f.get('session_id')
        if session_id and session_id not in unique_sessions:
            unique_sessions[session_id] = {
                'id': session_id, 
                'name': f.get('session_name', f.get('chatbot_type', '不明'))
            }
    sessions = list(unique_sessions.values())
    
    analytics = {
        'total_feedback': len(filtered_data),
        'chatbot_types': chatbot_types,
        'sessions': sessions,
        'recent_feedback': sorted(filtered_data, key=lambda x: x['timestamp'], reverse=True)[:10],
        'chatbot_counts': {},
        'session_counts': {}
    }
    
    for chatbot_type in chatbot_types:
        analytics['chatbot_counts'][chatbot_type] = len([f for f in current_feedback if f.get('chatbot_type') == chatbot_type])
    
    for session in sessions:
        analytics['session_counts'][session['id']] = len([f for f in current_feedback if f.get('session_id') == session['id']])
    
    return jsonify({
        'feedback': filtered_data,
        'analytics': analytics
    })

@admin_bp.route("/summary")
def admin_summary():
    logger.info("Generating admin summary")
    current_feedback = load_shared_feedback_data()
    summary = generate_summary_with_ai(current_feedback)
    logger.info("Admin summary generated successfully")
    return jsonify({"summary": summary})

@admin_bp.route("/feedback/<feedback_id>")
def admin_feedback_detail(feedback_id):
    logger.info(f"Fetching feedback detail for ID: {feedback_id}")
    current_feedback = load_shared_feedback_data()
    feedback = next((f for f in current_feedback if f['id'] == feedback_id), None)
    if not feedback:
        logger.warning(f"Feedback not found for ID: {feedback_id}")
        return jsonify({"error": "フィードバックが見つかりません"}), 404
    logger.info(f"Successfully retrieved feedback detail for ID: {feedback_id}")
    return jsonify(feedback)
