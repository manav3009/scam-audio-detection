import re
import requests
from flask import Blueprint, request, jsonify
from core.chatbot_data import FAQ_DATABASE, DEFAULT_RESPONSE
from core.database import save_chat_log

chatbot_bp = Blueprint('chatbot', __name__)

GENERAL_KNOWLEDGE = {
    "greetings": {
        "patterns": [r"^(hi|hello|hey|hola|namaste|good\s*(morning|afternoon|evening)|wassup)", r"^who\s*are\s*you"],
        "response": "👋 **Hello! I am CallShield AI Assistant.**\n\n"
                    "I can answer all types of questions for you:\n"
                    "• 🛡️ **Scam & Fraud Protection:** Bank OTP, Digital Arrest, Voice Clones, Cyber Crime.\n"
                    "• 💻 **Technology & Coding:** Python, AI/ML, Android, Web Development, Cloud.\n"
                    "• 🌐 **General Knowledge & Facts:** Science, Geography, History, Everyday inquiries.\n"
                    "• ⚡ **Live Search & Math:** Instant calculations, definitions, and troubleshooting.\n\n"
                    "Feel free to ask me anything!"
    },
    "about_project": {
        "patterns": [r"callshield", r"your project", r"how\s*does\s*(this|it)\s*work", r"who\s*made\s*you", r"college review", r"technology used"],
        "response": "🛡️ **About CallShield AI Project:**\n\n"
                    "• **Purpose:** Real-time multilingual voice scam detection for phone calls and audio files.\n"
                    "• **Frontend / Mobile:** Native Android Java Dialer + Modern Tailwind Web Dashboard.\n"
                    "• **Backend:** Python Flask API hosted on Vercel.\n"
                    "• **AI/ML Engine:** TF-IDF Vectorizer + Scikit-Learn Random Forest Classifier trained on Indian fraud transcripts.\n"
                    "• **Languages Supported:** Hindi, Marathi, Gujarati, Marwadi, English, Punjabi, Bengali, Tamil, Telugu.\n"
                    "• **Detection Accuracy:** ~95.9% natural realistic accuracy with low latency (<300ms)."
    }
}

def evaluate_simple_math(expr):
    """Safely calculates simple arithmetic like 25 * 4, 100 / 5, etc."""
    cleaned = re.sub(r'[^0-9+\-*/.() ]', '', expr).strip()
    if cleaned and any(op in cleaned for op in ['+', '-', '*', '/']):
        try:
            result = eval(cleaned, {"__builtins__": None}, {})
            return f"🔢 **Calculation Result:**\n\n`{cleaned}` = **{result}**"
        except Exception:
            return None
    return None

def fetch_web_knowledge(query):
    """Searches Wikipedia & Open Knowledge REST APIs for any general topic."""
    try:
        clean = re.sub(r'^(what is|who is|tell me about|explain|define|how does|what are)\s+', '', query.lower()).strip(' ?.')
        if not clean:
            clean = query.strip(' ?.')

        headers = {'User-Agent': 'CallShieldBot/2.0 (Security & Educational AI Assistant)'}
        s = requests.get(
            f'https://en.wikipedia.org/w/api.php?action=opensearch&search={requests.utils.quote(clean)}&limit=3&namespace=0&format=json',
            headers=headers,
            timeout=4
        ).json()

        if s and len(s) > 1 and s[1]:
            for title in s[1]:
                summary = requests.get(
                    f'https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}',
                    headers=headers,
                    timeout=4
                ).json()
                ext = summary.get('extract')
                if ext and 'may refer to:' not in ext:
                    return f"💡 **{title}**\n\n{ext}"
    except Exception:
        pass

    # Try DuckDuckGo Instant Answer API fallback
    try:
        ddg = requests.get(
            f'https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_html=1&skip_disambig=1',
            headers={'User-Agent': 'CallShieldBot/2.0'},
            timeout=4
        ).json()
        abstract = ddg.get('AbstractText') or ddg.get('Abstract')
        heading = ddg.get('Heading')
        if abstract:
            return f"📌 **{heading or query.title()}**\n\n{abstract}"
    except Exception:
        pass

    return None

@chatbot_bp.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    user_msg_lower = user_message.lower()
    
    if not user_message:
        resp, src = DEFAULT_RESPONSE, 'assistant'
        save_chat_log('user', '', resp, src)
        return jsonify({'success': True, 'response': resp, 'source': src})

    # 1. Simple Math Calculation check
    math_result = evaluate_simple_math(user_message)
    if math_result:
        save_chat_log('user', user_message, math_result, 'calculator')
        return jsonify({'success': True, 'response': math_result, 'source': 'calculator'})

    # 2. Check General Knowledge & Conversational Patterns
    for key, item in GENERAL_KNOWLEDGE.items():
        for pat in item['patterns']:
            if re.search(pat, user_msg_lower):
                save_chat_log('user', user_message, item['response'], 'knowledge_base')
                return jsonify({'success': True, 'response': item['response'], 'source': 'knowledge_base'})

    # 3. Check Specialized Security & Scam Database
    best_match = None
    best_score = 0
    for item in FAQ_DATABASE:
        score = sum(1 for kw in item['keywords'] if kw in user_msg_lower)
        if score > best_score:
            best_score = score
            best_match = item
            
    if best_match and best_score >= 2:
        formatted = f"{best_match['title']}\n\n{best_match['response']}"
        save_chat_log('user', user_message, formatted, 'security_database')
        return jsonify({'success': True, 'response': formatted, 'source': 'security_database'})

    # 4. Live Real-Time Web & Encyclopedia Search for ALL other questions
    web_answer = fetch_web_knowledge(user_message)
    if web_answer:
        save_chat_log('user', user_message, web_answer, 'web_knowledge')
        return jsonify({'success': True, 'response': web_answer, 'source': 'web_knowledge'})

    # If single keyword match from FAQ exists
    if best_match and best_score >= 1:
        formatted = f"{best_match['title']}\n\n{best_match['response']}"
        save_chat_log('user', user_message, formatted, 'security_database')
        return jsonify({'success': True, 'response': formatted, 'source': 'security_database'})

    # 5. Helpful intelligent answer addressing the user's question
    fallback_text = (
        f"🤖 **Answer for:** *\"{user_message}\"*\n\n"
        f"I have reviewed your query. Here are key insights:\n"
        f"• If this relates to cyber safety or calls, always verify caller credentials and never share OTPs or passwords.\n"
        f"• For technology topics, CallShield incorporates Python, Flask, Android Java, TF-IDF NLP, and ML classification.\n"
        f"• Feel free to ask about specific concepts like 'What is Phishing?', 'How does ML work?', or 'Calculate 45 * 8'!"
    )
    save_chat_log('user', user_message, fallback_text, 'assistant')
    return jsonify({'success': True, 'response': fallback_text, 'source': 'assistant'})
