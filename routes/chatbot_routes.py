from flask import Blueprint, request, jsonify
from core.chatbot_data import RESPONSES
from duckduckgo_search import DDGS

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    data = request.json or {}
    user_message = data.get('message', '').lower().strip()
    
    for pattern, response in RESPONSES.items():
        if pattern in user_message or user_message in pattern:
            return jsonify({'success': True, 'response': response, 'source': 'security_database'})
    
    security_keywords = ['scam', 'fraud', 'phishing', 'cyber', 'otp', 'bank']
    if any(k in user_message for k in security_keywords):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{user_message} scam fraud prevention", max_results=2))
                if results:
                    text = f"📊 **Security Insights:**\n\n" + "\n".join([f"🔹 **{r['title']}**\n   {r['body'][:250]}..." for r in results])
                    return jsonify({'success': True, 'response': text, 'source': 'duckduckgo'})
        except Exception:
            pass
            
    return jsonify({'success': True, 'response': RESPONSES['default'], 'source': 'assistant'})
