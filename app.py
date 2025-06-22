from flask import Flask, render_template, request, redirect, url_for, session, Response, stream_with_context, jsonify
import json
import time
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import uuid
import threading
import subprocess
import signal
import sys
import tempfile
from werkzeug.serving import make_server

admin_app = Flask(__name__)
admin_app.secret_key = 'admin-secret-key-change-in-production'

employee_data = {}
running_servers = {}
feedback_data = []
employee_access_tokens = {}

SHARED_DATA_DIR = "/tmp/interview_ai_shared"
FEEDBACK_DATA_FILE = f"{SHARED_DATA_DIR}/feedback_data.json"
EMPLOYEE_DATA_FILE = f"{SHARED_DATA_DIR}/employee_data.json"

os.makedirs(SHARED_DATA_DIR, exist_ok=True)

def load_shared_feedback_data():
    """Load feedback data from shared file"""
    try:
        if os.path.exists(FEEDBACK_DATA_FILE):
            with open(FEEDBACK_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading feedback data: {e}")
    return []

def save_shared_feedback_data(data):
    """Save feedback data to shared file"""
    try:
        with open(FEEDBACK_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving feedback data: {e}")

def load_shared_employee_data():
    """Load employee data from shared file"""
    try:
        if os.path.exists(EMPLOYEE_DATA_FILE):
            with open(EMPLOYEE_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading employee data: {e}")
    return {}

def save_shared_employee_data(data):
    """Save employee data to shared file"""
    try:
        with open(EMPLOYEE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving employee data: {e}")

feedback_data = load_shared_feedback_data()
employee_data = load_shared_employee_data()

load_dotenv()

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



def create_employee_app(employee_id, employee_name, department):
    """Create a dedicated Flask app for a specific employee"""
    employee_app = Flask(f"employee_{employee_id}")
    employee_app.secret_key = f'employee-{employee_id}-secret'
    
    @employee_app.route("/")
    def employee_home():
        return render_template("employee_chat.html", 
                             employee_name=employee_name,
                             department=department,
                             employee_id=employee_id)
    
    @employee_app.route("/chat", methods=["POST"])
    def employee_chat():
        data = request.get_json()
        user_message = data.get("message", "").strip()
        
        if not user_message:
            return jsonify({"error": "メッセージを入力してください"}), 400
        
        feedback_entry = {
            'id': str(uuid.uuid4()),
            'employee_id': employee_id,
            'employee_name': employee_name,
            'department': department,
            'user_message': user_message,
            'timestamp': datetime.now().isoformat(),
            'ai_response': None
        }
        
        system_prompt = f"""あなたは従業員の声を聞く優秀なカウンセラーです。
従業員の{employee_name}さん（{department}部署）と対話しています。

以下の観点で自然な会話を通じて情報を収集してください：
- 現在の業務状況や満足度
- チームや職場環境について
- 困っていることや改善したいこと
- 会社の統合に関する感想や懸念
- キャリアや成長に関する希望

共感的で親しみやすい口調で、従業員が話しやすい雰囲気を作ってください。
一度に多くの質問をせず、相手の話を聞いてから適切な質問や共感を示してください。"""

        def stream():
            try:
                if client is None:
                    demo_response = f"""ありがとうございます、{employee_name}さん。

お話しいただいた内容について、とても大切なフィードバックだと思います。

**現在の状況について：**
- 業務に関するご意見をお聞かせいただき、ありがとうございます
- {department}部署での状況を把握させていただきました

**今後のサポートについて：**
- 管理者チームがこのフィードバックを確認し、改善策を検討いたします
- 必要に応じて、個別の面談の機会も設けることができます

他にも気になることや改善したいことがあれば、いつでもお聞かせください。
あなたの声は会社の成長にとって非常に重要です。

*（注：現在はデモモードで動作しています。本番環境ではAIが自然な対話を行います）*"""
                    
                    for char in demo_response:
                        yield char
                        time.sleep(0.02)
                    
                    feedback_entry['ai_response'] = demo_response
                    
                    current_feedback = load_shared_feedback_data()
                    current_feedback.append(feedback_entry)
                    save_shared_feedback_data(current_feedback)
                    return
                
                response = client.chat.completions.create(
                    model=global_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    stream=True,
                    temperature=0.7,
                    top_p=0.9,
                )
                
                ai_response = ""
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        ai_response += content
                        yield content
                
                feedback_entry['ai_response'] = ai_response
                
                current_feedback = load_shared_feedback_data()
                current_feedback.append(feedback_entry)
                save_shared_feedback_data(current_feedback)
                
            except Exception as e:
                yield f"エラーが発生しました: {str(e)}"
        
        return Response(stream_with_context(stream()), content_type="text/event-stream")
    
    return employee_app

def create_employee_access_token(employee_id, employee_name, department):
    """Create a unique access token for the employee"""
    import secrets
    access_token = secrets.token_urlsafe(32)
    
    employee_access_tokens[access_token] = {
        'employee_id': employee_id,
        'employee_name': employee_name,
        'department': department,
        'created_at': datetime.now().isoformat()
    }
    
    return access_token

def create_employee_server_file_old(employee_id, employee_name, department, port):
    """Legacy function - keeping for reference but not used"""
    server_content = f'''
from flask import Flask, render_template, request, Response, stream_with_context, jsonify
import json
import time
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = 'employee-{employee_id}-secret'

EMPLOYEE_ID = "{employee_id}"
EMPLOYEE_NAME = "{employee_name}"
DEPARTMENT = "{department}"

client = None
try:
    if os.getenv("AZURE_OPENAI_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-12-01-preview",
        )
except Exception as e:
    print(f"Warning: Failed to initialize Azure OpenAI client: {{e}}")

feedback_data = []
try:
    with open('feedback_data.json', 'r', encoding='utf-8') as f:
        feedback_data = json.load(f)
except FileNotFoundError:
    feedback_data = []

def save_feedback_data():
    with open('feedback_data.json', 'w', encoding='utf-8') as f:
        json.dump(feedback_data, f, ensure_ascii=False, indent=2)

@app.route("/")
def employee_home():
    return render_template("employee_chat.html", 
                         employee_name=EMPLOYEE_NAME,
                         department=DEPARTMENT,
                         employee_id=EMPLOYEE_ID)

@app.route("/chat", methods=["POST"])
def employee_chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({{"error": "メッセージを入力してください"}}), 400
    
    feedback_entry = {{
        'id': str(uuid.uuid4()),
        'employee_id': EMPLOYEE_ID,
        'employee_name': EMPLOYEE_NAME,
        'department': DEPARTMENT,
        'user_message': user_message,
        'timestamp': datetime.now().isoformat(),
        'ai_response': None
    }}
    
    system_prompt = f"""あなたは従業員の声を聞く優秀なカウンセラーです。
従業員の{{EMPLOYEE_NAME}}さん（{{DEPARTMENT}}部署）と対話しています。

以下の観点で自然な会話を通じて情報を収集してください：
- 現在の業務状況や満足度
- チームや職場環境について
- 困っていることや改善したいこと
- 会社の統合に関する感想や懸念
- キャリアや成長に関する希望

共感的で親しみやすい口調で、従業員が話しやすい雰囲気を作ってください。
一度に多くの質問をせず、相手の話を聞いてから適切な質問や共感を示してください。"""

    def stream():
        try:
            if client is None:
                demo_response = f"""ありがとうございます、{{EMPLOYEE_NAME}}さん。

お話しいただいた内容について、とても大切なフィードバックだと思います。

**現在の状況について：**
- 業務に関するご意見をお聞かせいただき、ありがとうございます
- {{DEPARTMENT}}部署での状況を把握させていただきました

**今後のサポートについて：**
- 管理者チームがこのフィードバックを確認し、改善策を検討いたします
- 必要に応じて、個別の面談の機会も設けることができます

他にも気になることや改善したいことがあれば、いつでもお聞かせください。
あなたの声は会社の成長にとって非常に重要です。

*（注：現在はデモモードで動作しています。本番環境ではAIが自然な対話を行います）*"""
                
                for char in demo_response:
                    yield char
                    time.sleep(0.02)
                
                feedback_entry['ai_response'] = demo_response
                feedback_data.append(feedback_entry)
                save_feedback_data()
                return
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {{"role": "system", "content": system_prompt}},
                    {{"role": "user", "content": user_message}}
                ],
                stream=True,
                temperature=0.7,
                top_p=0.9,
            )
            
            ai_response = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    ai_response += content
                    yield content
            
            feedback_entry['ai_response'] = ai_response
            feedback_data.append(feedback_entry)
            save_feedback_data()
            
        except Exception as e:
            yield f"エラーが発生しました: {{str(e)}}"
    
    return Response(stream_with_context(stream()), content_type="text/event-stream")

if __name__ == "__main__":
    print(f"Starting employee server for {{EMPLOYEE_NAME}} ({{DEPARTMENT}}) on port {port}")
    app.run(host='0.0.0.0', port={port}, debug=False, use_reloader=False)
'''
    
    filename = f"employee_server_{employee_id}.py"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(server_content)
    
    return filename

def start_employee_server(employee_id, port):
    """Start a dedicated Flask server for an employee on a specific port using Werkzeug server"""
    if employee_id not in employee_data:
        return False
    
    employee_info = employee_data[employee_id]
    
    try:
        employee_app = create_employee_app(employee_id, employee_info['name'], employee_info['department'])
        
        server = make_server('0.0.0.0', port, employee_app, threaded=True)
        
        def run_server():
            try:
                print(f"Starting employee server for {employee_info['name']} on port {port}")
                server.serve_forever()
            except Exception as e:
                print(f"Error running employee server on port {port}: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        time.sleep(1)
        
        running_servers[employee_id] = {
            'port': port,
            'thread': server_thread,
            'server': server,
            'url': f"http://localhost:{port}",
            'app': employee_app
        }
        
        print(f"Employee server started for {employee_info['name']} at http://localhost:{port}")
        return True
        
    except Exception as e:
        print(f"Error starting server for employee {employee_id} on port {port}: {e}")
        return False

def generate_summary_with_ai(feedback_list):
    """Generate AI summary of all feedback"""
    if not feedback_list:
        return "フィードバックがまだありません。"
    
    if client is None:
        return """**全体要約（デモモード）**

現在のフィードバック状況：
- 従業員からの貴重な意見が収集されています
- 各部署からの多様な視点が含まれています
- 業務改善や職場環境に関する建設的な提案があります

**主要な傾向：**
- コミュニケーションの改善要望
- 業務効率化への関心
- チームワーク強化の必要性

**推奨アクション：**
- 定期的な部署間ミーティングの実施
- 業務プロセスの見直し
- 従業員満足度向上施策の検討

*（注：本番環境ではAIが詳細な分析を提供します）*"""
    
    try:
        feedback_text = "\n\n".join([
            f"従業員: {f['employee_name']} ({f['department']})\n"
            f"日時: {f['timestamp']}\n"
            f"内容: {f['user_message']}\n"
            f"AI応答: {f['ai_response'][:200]}..."
            for f in feedback_list[-20:]  # Last 20 feedback entries
        ])
        
        summary_prompt = f"""以下の従業員フィードバックデータを分析し、包括的な要約を作成してください：

{feedback_text}

以下の観点で分析してください：
1. 全体的な傾向と共通テーマ
2. 部署別の特徴的な課題
3. 緊急度の高い問題
4. 改善提案
5. 従業員満足度の状況
6. 経営陣への推奨アクション

日本語で、管理者が理解しやすい形式で要約してください。"""
        
        response = client.chat.completions.create(
            model=global_model,
            messages=[
                {"role": "system", "content": "あなたは人事・組織分析の専門家です。従業員フィードバックを分析し、経営陣向けの洞察に富んだ要約を作成します。"},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"要約生成中にエラーが発生しました: {str(e)}"



@admin_app.route("/")
def admin_home():
    return render_template("admin_home.html")

@admin_app.route("/create-employee-url", methods=["POST"])
def create_employee_url():
    data = request.get_json()
    employee_name = data.get("name", "").strip()
    department = data.get("department", "").strip()
    
    if not employee_name or not department:
        return jsonify({"success": False, "error": "従業員名と部署を入力してください"})
    
    employee_id = str(uuid.uuid4())
    base_port = 5001
    port = base_port
    
    while port in [server['port'] for server in running_servers.values()]:
        port += 1
    
    employee_data[employee_id] = {
        'name': employee_name,
        'department': department,
        'created_at': datetime.now().isoformat(),
        'port': port
    }
    
    save_shared_employee_data(employee_data)
    
    if start_employee_server(employee_id, port):
        employee_url = f"http://localhost:{port}"
        return jsonify({
            "success": True, 
            "employee_url": employee_url,
            "port": port,
            "employee_id": employee_id
        })
    else:
        return jsonify({"success": False, "error": "従業員サーバーの起動に失敗しました"})

@admin_app.route("/employees")
def list_employees():
    current_employee_data = load_shared_employee_data()
    
    employees = []
    for emp_id, emp_data in current_employee_data.items():
        server_info = running_servers.get(emp_id, {})
        employees.append({
            'id': emp_id,
            'name': emp_data['name'],
            'department': emp_data['department'],
            'created_at': emp_data['created_at'],
            'port': emp_data.get('port'),
            'url': server_info.get('url'),
            'status': 'running' if emp_id in running_servers else 'stopped'
        })
    return jsonify(employees)

@admin_app.route("/dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@admin_app.route("/data")
def admin_data():
    current_feedback = load_shared_feedback_data()
    
    department_filter = request.args.get('department', 'all')
    employee_filter = request.args.get('employee', 'all')
    
    filtered_data = current_feedback
    if department_filter != 'all':
        filtered_data = [f for f in filtered_data if f['department'] == department_filter]
    if employee_filter != 'all':
        filtered_data = [f for f in filtered_data if f['employee_id'] == employee_filter]
    
    departments = list(set([f['department'] for f in current_feedback]))
    
    unique_employees = {}
    for f in current_feedback:
        emp_id = f['employee_id']
        if emp_id not in unique_employees:
            unique_employees[emp_id] = {'id': emp_id, 'name': f['employee_name']}
    employees = list(unique_employees.values())
    
    analytics = {
        'total_feedback': len(filtered_data),
        'departments': departments,
        'employees': employees,
        'recent_feedback': sorted(filtered_data, key=lambda x: x['timestamp'], reverse=True)[:10],
        'department_counts': {},
        'employee_counts': {}
    }
    
    for dept in departments:
        analytics['department_counts'][dept] = len([f for f in current_feedback if f['department'] == dept])
    
    for emp in employees:
        analytics['employee_counts'][emp['id']] = len([f for f in current_feedback if f['employee_id'] == emp['id']])
    
    return jsonify({
        'feedback': filtered_data,
        'analytics': analytics
    })

@admin_app.route("/summary")
def admin_summary():
    """Generate AI-powered summary of all feedback"""
    current_feedback = load_shared_feedback_data()
    summary = generate_summary_with_ai(current_feedback)
    return jsonify({"summary": summary})

@admin_app.route("/feedback/<feedback_id>")
def admin_feedback_detail(feedback_id):
    current_feedback = load_shared_feedback_data()
    feedback = next((f for f in current_feedback if f['id'] == feedback_id), None)
    if not feedback:
        return jsonify({"error": "フィードバックが見つかりません"}), 404
    return jsonify(feedback)

def cleanup_servers():
    """Clean up all running employee servers"""
    for employee_id in list(running_servers.keys()):
        server_info = running_servers[employee_id]
        print(f"Shutting down server for employee {employee_id}")
        
        if 'server' in server_info:
            try:
                server_info['server'].shutdown()
            except Exception as e:
                print(f"Error shutting down server: {e}")
        
        # Terminate the subprocess (legacy cleanup)
        if 'process' in server_info:
            try:
                server_info['process'].terminate()
                server_info['process'].wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_info['process'].kill()
            except Exception as e:
                print(f"Error terminating process: {e}")
        
        if 'server_file' in server_info:
            try:
                os.remove(server_info['server_file'])
            except Exception as e:
                print(f"Error removing server file: {e}")
        
        del running_servers[employee_id]

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\nShutting down all servers...")
    cleanup_servers()
    sys.exit(0)

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
