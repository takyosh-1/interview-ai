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
        
        system_prompt = f"""あなたは、社員の声を聴き、会社の改善に活かすための「AI面談アシスタント」です。  
        この面談は匿名で行われ、社員が安心して本音を話せる場であることを大切にしてください。  
        目的は、社員の【感情面】と【業務面】の現状と課題を把握し、改善のヒントを集めることです。

        以下の3つの質問を、順番に丁寧に聞いてください。  
        共感的でやさしい口調で、話しやすい雰囲気をつくってください。  
        回答があいまいな場合は、「たとえばどんなとき？」「具体的に言うとどういうことですか？」とやさしく深掘りしてください。

        ---

        ■ 質問①（感情面）：  
        最近の仕事について、どんな気持ちになることが多いですか？  
        （例：「やりがいが減った」「やる気が出ない」「前より落ち着いている」など）

        ---

        ■ 質問②（業務面）：  
        合併後の働き方やルールで、「やりづらい」「困っている」と感じることはありますか？  
        具体的な作業や変化を教えてください。

        ---

        ■ 質問③（改善希望）：  
        今の職場がもっと働きやすくなるために、「こうなったら嬉しい」と思うことはありますか？

        ---

        最後にこう伝えてください：  
        「今日は話してくださってありがとうございました。内容は整理して会社の改善に活かします。すべて匿名で扱われますので、安心してください。」
        """

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
                        stream=True
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
