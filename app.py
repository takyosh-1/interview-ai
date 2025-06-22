from flask import Flask, render_template, request, redirect, url_for, session, Response, stream_with_context, jsonify
import json
import time
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

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

feedback_data = []
employee_sessions = {}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/employee")
def employee_interface():
    if 'employee_id' not in session:
        return redirect(url_for('employee_setup'))
    return render_template("employee_chat.html")

@app.route("/employee/setup", methods=["GET", "POST"])
def employee_setup():
    if request.method == "POST":
        data = request.get_json()
        employee_name = data.get("name", "").strip()
        department = data.get("department", "").strip()
        
        if employee_name and department:
            employee_id = str(uuid.uuid4())
            session['employee_id'] = employee_id
            session['employee_name'] = employee_name
            session['department'] = department
            
            employee_sessions[employee_id] = {
                'name': employee_name,
                'department': department,
                'created_at': datetime.now().isoformat()
            }
            
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "名前と部署を入力してください"})
    
    return render_template("employee_setup.html")

@app.route("/employee/chat", methods=["POST"])
def employee_chat():
    if 'employee_id' not in session:
        return jsonify({"error": "セッションが無効です"}), 401
    
    data = request.get_json()
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"error": "メッセージを入力してください"}), 400
    
    employee_id = session['employee_id']
    employee_name = session['employee_name']
    department = session['department']
    
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
                    time.sleep(0.02)  # Simulate typing effect
                
                feedback_entry['ai_response'] = demo_response
                feedback_data.append(feedback_entry)
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
            feedback_data.append(feedback_entry)
            
        except Exception as e:
            yield f"エラーが発生しました: {str(e)}"
    
    return Response(stream_with_context(stream()), content_type="text/event-stream")

@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route("/admin/data")
def admin_data():
    department_filter = request.args.get('department', 'all')
    
    filtered_data = feedback_data
    if department_filter != 'all':
        filtered_data = [f for f in feedback_data if f['department'] == department_filter]
    
    departments = list(set([f['department'] for f in feedback_data]))
    
    analytics = {
        'total_feedback': len(filtered_data),
        'departments': departments,
        'recent_feedback': sorted(filtered_data, key=lambda x: x['timestamp'], reverse=True)[:10],
        'department_counts': {}
    }
    
    for dept in departments:
        analytics['department_counts'][dept] = len([f for f in feedback_data if f['department'] == dept])
    
    return jsonify({
        'feedback': filtered_data,
        'analytics': analytics
    })

@app.route("/admin/feedback/<feedback_id>")
def admin_feedback_detail(feedback_id):
    feedback = next((f for f in feedback_data if f['id'] == feedback_id), None)
    if not feedback:
        return jsonify({"error": "フィードバックが見つかりません"}), 404
    return jsonify(feedback)

if __name__ == "__main__":
    print("従業員フィードバックシステムを起動中...")
    if client:
        print(f"使用モデル: {global_model}")
    else:
        print("デモモードで起動中（OpenAI APIなし）")
    app.run(debug=True, host='0.0.0.0', port=5001)
