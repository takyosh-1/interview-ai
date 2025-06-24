from config.settings import client, global_model

def generate_summary_with_ai(feedback_list):
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
            for f in feedback_list[-20:]
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
