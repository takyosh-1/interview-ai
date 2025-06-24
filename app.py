import signal
from flask import Flask

from config.settings import employee_data, feedback_data, client, global_model
from models.data_manager import load_shared_feedback_data, load_shared_employee_data
from routes.admin_routes import admin_bp
from utils.server_utils import cleanup_servers, signal_handler

admin_app = Flask(__name__)
admin_app.secret_key = 'admin-secret-key-change-in-production'

admin_app.register_blueprint(admin_bp)

feedback_data.extend(load_shared_feedback_data())
employee_data.update(load_shared_employee_data())


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("管理者フィードバックシステムを起動中...")
    if client:
        print(f"使用モデル: {global_model}")
    else:
        print("デモモードで起動中（OpenAI APIなし）")
    
    print("管理者ダッシュボード: http://localhost:5000")
    print("従業員専用URLは管理者ダッシュボードから生成してください")
    
    try:
        admin_app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        cleanup_servers()
    except Exception as e:
        print(f"Error running admin app: {e}")
        cleanup_servers()
