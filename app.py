import signal
import logging
from flask import Flask

from config.settings import employee_data, feedback_data, client, global_model
from models.data_manager import load_shared_feedback_data, load_shared_employee_data
from routes.admin_routes import admin_bp
from utils.server_utils import cleanup_servers, signal_handler

logger = logging.getLogger(__name__)

admin_app = Flask(__name__)
admin_app.secret_key = 'admin-secret-key-change-in-production'

admin_app.register_blueprint(admin_bp)

logger.info("Loading initial data...")
feedback_data.extend(load_shared_feedback_data())
employee_data.update(load_shared_employee_data())
logger.info(f"Loaded {len(feedback_data)} feedback entries and {len(employee_data)} employee records")


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
