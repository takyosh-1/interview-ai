import uuid
import time
import threading
import logging
from datetime import datetime
from flask import Flask, render_template, request, Response, stream_with_context, jsonify
from werkzeug.serving import make_server

from config.settings import client, global_model, running_servers, employee_data
from models.data_manager import load_shared_feedback_data, save_shared_feedback_data

logger = logging.getLogger(__name__)

def create_employee_app(employee_id, employee_name, department):
    logger.info(f"Creating employee app for {employee_name} ({department}) - ID: {employee_id}")
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
        
        logger.info(f"Received chat message from {employee_name} ({department}): {len(user_message)} characters")
        
        if not user_message:
            logger.warning(f"Empty message received from {employee_name}")
            return jsonify({"error": "メッセージが空です"}), 400
        
        feedback_entry = {
            'id': str(uuid.uuid4()),
            'employee_id': employee_id,
            'employee_name': employee_name,
            'department': department,
            'user_message': user_message,
            'timestamp': datetime.now().isoformat(),
            'ai_response': ''
        }
        
        system_prompt = f"""あなたは従業員フィードバック収集のための親しみやすいAIアシスタントです。
従業員名: {employee_name}
部署: {department}

以下の役割を果たしてください：
1. 従業員の話を親身に聞き、共感を示す
2. 業務上の課題や改善提案を自然に引き出す
3. ストレスや不満がある場合は、具体的な状況を聞く
4. 建設的な解決策を一緒に考える
5. 必要に応じて、管理者に伝えるべき重要な情報を整理する

共感的で親しみやすい口調で、従業員が話しやすい雰囲気を作ってください。
一度に多くの質問をせず、相手の話を聞いてから適切な質問や共感を示してください。"""

        def stream():
            try:
                if client is None:
                    logger.info(f"Generating demo response for {employee_name} (no AI client available)")
                    demo_response = f"""ありがとうございます、{employee_name}さん。

{user_message}について、お話しいただきありがとうございます。

現在はデモモードで動作しているため、実際のAI応答は提供できませんが、本番環境では以下のような機能を提供します：

• あなたの状況に応じた個別のアドバイス
• 業務改善のための具体的な提案
• ストレス軽減のためのサポート
• 管理者への建設的なフィードバック整理

何か他にお聞かせいただきたいことがあれば、お気軽にお話しください。"""
                    
                    feedback_entry['ai_response'] = demo_response
                    current_feedback = load_shared_feedback_data()
                    current_feedback.append(feedback_entry)
                    save_shared_feedback_data(current_feedback)
                    logger.info(f"Saved demo feedback entry for {employee_name}")
                    
                    for char in demo_response:
                        yield char
                        time.sleep(0.02)
                else:
                    logger.info(f"Generating AI response for {employee_name} using {global_model}")
                    response = client.chat.completions.create(
                        model=global_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        stream=True,
                        temperature=0.7,
                        max_tokens=500
                    )
                    
                    ai_response = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            ai_response += content
                            yield content
                    
                    feedback_entry['ai_response'] = ai_response
                    current_feedback = load_shared_feedback_data()
                    current_feedback.append(feedback_entry)
                    save_shared_feedback_data(current_feedback)
                    logger.info(f"Saved AI feedback entry for {employee_name} ({len(ai_response)} characters)")
                    
            except Exception as e:
                logger.error(f"Error in chat stream for {employee_name}: {e}")
                error_message = f"申し訳ございません。エラーが発生しました: {str(e)}"
                feedback_entry['ai_response'] = error_message
                current_feedback = load_shared_feedback_data()
                current_feedback.append(feedback_entry)
                save_shared_feedback_data(current_feedback)
                yield error_message
        
        return Response(stream_with_context(stream()), mimetype='text/plain')
    
    return employee_app

def start_employee_server(employee_id, port):
    logger.info(f"Starting employee server for ID: {employee_id} on port {port}")
    
    if employee_id not in employee_data:
        logger.error(f"Employee ID {employee_id} not found in employee data")
        return False
    
    employee_info = employee_data[employee_id]
    
    try:
        employee_app = create_employee_app(employee_id, employee_info['name'], employee_info['department'])
        
        server = make_server('0.0.0.0', port, employee_app, threaded=True)
        
        def run_server():
            try:
                logger.info(f"Employee server thread started for {employee_info['name']} on port {port}")
                server.serve_forever()
            except Exception as e:
                logger.error(f"Error running employee server on port {port}: {e}")
        
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
        
        logger.info(f"Employee server successfully started for {employee_info['name']} at http://localhost:{port}")
        return True
        
    except Exception as e:
        logger.error(f"Error starting server for employee {employee_id} on port {port}: {e}")
        return False
