from flask import Blueprint, request, jsonify
from core.chatbot_data import FAQ_DATABASE, DEFAULT_RESPONSE
from duckduckgo_search import DDGS

from core.database import save_chat_log

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    data = request.json or {}
    user_message = data.get('message', '').lower().strip()
    
    if not user_message:
        resp, src = DEFAULT_RESPONSE, 'assistant'
        save_chat_log('user', '', resp, src)
        return jsonify({'success': True, 'response': resp, 'source': src})
        
    best_match = None
    best_score = 0
    
    for item in FAQ_DATABASE:
        score = sum(1 for kw in item['keywords'] if kw in user_message)
        if score > best_score:
            best_score = score
            best_match = item
            
    if best_match and best_score > 0:
        formatted = f"{best_match['title']}\n\n{best_match['response']}"
        save_chat_log('user', user_message, formatted, 'security_database')
        return jsonify({'success': True, 'response': formatted, 'source': 'security_database'})
        
    security_keywords = ['scam', 'fraud', 'phishing', 'cyber', 'otp', 'bank', 'call', 'money', 'safe', 'phone']
    if any(k in user_message for k in security_keywords):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{user_message} scam cyber security advisory", max_results=2))
                if results:
                    text = f"📊 **Live Security Advisory:**\n\n" + "\n".join([f"🔹 **{r['title']}**\n   {r['body'][:250]}..." for r in results])
                    save_chat_log('user', user_message, text, 'duckduckgo')
                    return jsonify({'success': True, 'response': text, 'source': 'duckduckgo'})
        except Exception:
            pass
            
    save_chat_log('user', user_message, DEFAULT_RESPONSE, 'assistant')
    return jsonify({'success': True, 'response': DEFAULT_RESPONSE, 'source': 'assistant'})
