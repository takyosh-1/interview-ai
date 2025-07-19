import signal
import logging
from flask import Flask, render_template, request, Response, stream_with_context, jsonify

from config.settings import employee_data, feedback_data, client, global_model, session_url_mapping
from models.data_manager import load_shared_feedback_data, load_shared_employee_data
from routes.admin_routes import admin_bp
from utils.server_utils import cleanup_servers, signal_handler

logger = logging.getLogger(__name__)

admin_app = Flask(__name__)
admin_app.secret_key = 'admin-secret-key-change-in-production'

admin_app.register_blueprint(admin_bp)

@admin_app.route('/chat/<session_token>')
def employee_chat_home(session_token):
    from services.employee_server import handle_employee_home
    
    if session_token not in session_url_mapping:
        return "Invalid or expired chatbot URL", 404
    
    session_id = session_url_mapping[session_token]
    return handle_employee_home(session_id)

@admin_app.route('/chat/<session_token>/chat', methods=['POST'])
def employee_chat_api(session_token):
    from services.employee_server import handle_employee_chat
    
    if session_token not in session_url_mapping:
        return jsonify({"error": "Invalid or expired chatbot URL"}), 404
    
    session_id = session_url_mapping[session_token]
    return handle_employee_chat(session_id)

logger.info("Loading initial data...")
feedback_data.extend(load_shared_feedback_data())
employee_data.update(load_shared_employee_data())

for session_id, session_data in employee_data.items():
    session_token = session_data.get('session_token')
    if session_token:
        session_url_mapping[session_token] = session_id

logger.info(f"Loaded {len(feedback_data)} feedback entries and {len(employee_data)} employee records")
logger.info(f"Restored {len(session_url_mapping)} session URL mappings")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("管理者フィードバックシステムを起動中...")
    if client:
        logger.info(f"使用モデル: {global_model}")
    else:
        logger.warning("デモモードで起動中（OpenAI APIなし）")
    
    import os
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"管理者ダッシュボード: http://localhost:{port}")
    logger.info("従業員専用URLは管理者ダッシュボードから生成してください")
    
    try:
        logger.info(f"Starting Flask admin application on port {port}")
        admin_app.run(debug=True, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, cleaning up...")
        cleanup_servers()
    except Exception as e:
        logger.error(f"Error running admin app: {e}")
        cleanup_servers()
