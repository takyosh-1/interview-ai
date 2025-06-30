import logging
from config.settings import client, global_model

logger = logging.getLogger(__name__)

def get_chatbot_system_prompt(chatbot_type):
    logger.info(f"Generating system prompt for chatbot type: {chatbot_type}")
    
    base_prompt = """あなたは、社員の声を聴き、会社の改善に活かすための「AI面談アシスタント」です。
この面談は匿名で行われ、社員が安心して本音を話せる場であることを大切にしてください。
共感的でやさしい口調で、話しやすい雰囲気をつくってください。"""
    
    if chatbot_type == "業務":
        return f"""{base_prompt}
        
あなたは【業務】に関する相談を専門とするアシスタントです。
以下の点について丁寧に聞いてください：
• 現在の業務内容や作業量について
• 業務効率や生産性の課題
• 必要なツールやリソースの不足
• 業務プロセスの改善提案
• スキルアップや研修のニーズ"""
        
    elif chatbot_type == "人間関係":
        return f"""{base_prompt}
        
あなたは【人間関係】に関する相談を専門とするアシスタントです。
以下の点について丁寧に聞いてください：
• 同僚や上司との関係性
• チーム内のコミュニケーション
• 職場の雰囲気や人間関係の悩み
• ハラスメントや不適切な行動の有無
• チームワーク改善のアイデア"""
        
    elif chatbot_type == "会社の方向性":
        return f"""{base_prompt}
        
あなたは【会社の方向性】に関する相談を専門とするアシスタントです。
以下の点について丁寧に聞いてください：
• 会社の戦略や方針への理解度
• 組織変更や合併への感想
• 会社の将来性への不安や期待
• 経営陣への要望や提案
• 企業文化や価値観について"""
        
    elif chatbot_type == "キャリア":
        return f"""{base_prompt}
        
あなたは【キャリア】に関する相談を専門とするアシスタントです。
以下の点について丁寧に聞いてください：
• 現在の職位や役割への満足度
• キャリアアップの希望や計画
• 異動や昇進への期待
• スキル開発や成長機会
• 長期的なキャリアビジョン"""
    
    else:
        logger.warning(f"Unknown chatbot type: {chatbot_type}, using default prompt")
        return base_prompt

def generate_summary_with_ai(feedback_list):
    logger.info(f"Generating AI summary for {len(feedback_list)} feedback entries")
    
    if not feedback_list:
        logger.info("No feedback data available for summary generation")
        return "フィードバックがまだありません。"
    
    if client is None:
        logger.warning("AI client not available, returning demo summary")
        return """**全体要約（デモモード）**

現在のフィードバック状況：
- 従業員からの貴重な意見が収集されています
- 各チャットボットタイプからの多様な視点が含まれています
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
        logger.info(f"Processing {min(20, len(feedback_list))} most recent feedback entries for AI analysis")
        feedback_text = "\n\n".join([
            f"チャットボット種類: {f.get('chatbot_type', '不明')} ({f.get('session_name', '不明')})\n"
            f"日時: {f['timestamp']}\n"
            f"内容: {f['user_message']}\n"
            f"AI応答: {f['ai_response'][:200]}..."
            for f in feedback_list[-20:]
        ])
        
        summary_prompt = f"""以下の従業員フィードバックデータを分析し、包括的な要約を作成してください：

{feedback_text}

以下の観点で分析してください：
1. 全体的な傾向と共通テーマ
2. チャットボット種類別の特徴的な課題
3. 緊急度の高い問題
4. 改善提案
5. 従業員満足度の状況
6. 経営陣への推奨アクション

日本語で、管理者が理解しやすい形式で要約してください。"""
        
        logger.info(f"Sending summary request to Azure OpenAI using model: {global_model}")
        response = client.chat.completions.create(
            model=global_model,
            messages=[
                {"role": "system", "content": "あなたは人事・組織分析の専門家です。従業員フィードバックを分析し、経営陣向けの洞察に富んだ要約を作成します。"},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        summary_content = response.choices[0].message.content
        logger.info(f"Successfully generated AI summary ({len(summary_content)} characters)")
        return summary_content
        
    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return f"要約生成中にエラーが発生しました: {str(e)}"
