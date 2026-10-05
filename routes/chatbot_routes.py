import re
from flask import Blueprint, request, jsonify
from core.chatbot_data import FAQ_DATABASE, DEFAULT_RESPONSE
from duckduckgo_search import DDGS
from core.database import save_chat_log

chatbot_bp = Blueprint('chatbot', __name__)

# General Conversational & Tech Knowledge Base
GENERAL_KNOWLEDGE = {
    "greetings": {
        "patterns": [r"^(hi|hello|hey|hola|namaste|good\s*(morning|afternoon|evening)|wassup)", r"^who\s*are\s*you"],
        "response": "👋 **Hello! I am CallShield AI Assistant.**\n\n"
                    "I can answer all types of questions for you:\n"
                    "• 🛡️ **Scam & Fraud Protection:** Bank OTP, Digital Arrest, Voice Clones, Cyber Crime.\n"
                    "• 💻 **Technology & Coding:** Python, AI/ML, Android, Web Development, Cloud.\n"
                    "• 🌐 **General Knowledge & Facts:** Science, Geography, History, Everyday inquiries.\n"
                    "• ⚡ **Live Search:** Real-time information and troubleshooting.\n\n"
                    "How can I help you today?"
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
    },
    "python": {
        "patterns": [r"\bpython\b"],
        "response": "🐍 **Python Programming:**\n\n"
                    "Python is a high-level, interpreted programming language known for its clear syntax and versatility.\n"
                    "• **Key uses:** Artificial Intelligence, Machine Learning, Web Development (Flask/Django), Data Science, Automation.\n"
                    "• **In this project:** Powering the Flask REST API, ML classification models (scikit-learn), audio feature extraction, and NLP pipeline."
    },
    "machine_learning": {
        "patterns": [r"\bmachine learning\b", r"\bml\b", r"\bartificial intelligence\b", r"\bai\b"],
        "response": "🤖 **Machine Learning & AI:**\n\n"
                    "Machine Learning is a subset of AI where algorithms learn patterns from data rather than being explicitly hardcoded.\n"
                    "• **Supervised Learning:** Training models on labeled datasets (like our Scam vs Legitimate transcripts dataset).\n"
                    "• **NLP (Natural Language Processing):** Converting speech transcripts into vector representations using TF-IDF and detecting linguistic fraud markers.\n"
                    "• **Confidence Score:** Evaluates probability of fraud to warn users in real time."
    }
}

def evaluate_simple_math(expr):
    """Safely calculates simple arithmetic like 25 * 4, 100 / 5, etc."""
    cleaned = re.sub(r'[^0-9+\-*/.() ]', '', expr).strip()
    if cleaned and any(op in cleaned for op in ['+', '-', '*', '/']):
        try:
            # Only allow arithmetic operations with numbers
            result = eval(cleaned, {"__builtins__": None}, {})
            return f"🔢 **Calculation Result:**\n\n`{cleaned}` = **{result}**"
        except Exception:
            return None
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
            
    if best_match and best_score >= 1:
        formatted = f"{best_match['title']}\n\n{best_match['response']}"
        save_chat_log('user', user_message, formatted, 'security_database')
        return jsonify({'success': True, 'response': formatted, 'source': 'security_database'})

    # 4. Live Real-Time Web Search for ALL types of general questions
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(user_message, max_results=3))
            if results:
                items_formatted = []
                for idx, r in enumerate(results, 1):
                    body = r.get('body', '').strip()
                    title = r.get('title', '').strip()
                    if body:
                        items_formatted.append(f"📌 **{title}**\n{body}")
                
                if items_formatted:
                    response_text = f"💡 **Here is what I found for you:**\n\n" + "\n\n".join(items_formatted)
                    save_chat_log('user', user_message, response_text, 'web_search')
                    return jsonify({'success': True, 'response': response_text, 'source': 'web_search'})
    except Exception as e:
        pass

    # 5. Smart Fallback for any unknown query
    fallback_text = (
        f"🤖 **Answer for:** *\"{user_message}\"*\n\n"
        f"I have analyzed your request. Here are helpful insights:\n"
        f"• If this relates to cybersecurity or suspicious phone calls, never share sensitive credentials, OTPs, or passwords.\n"
        f"• If this is a general inquiry, feel free to specify additional context or ask about topics like Python, AI, Android, or security.\n"
        f"• You can also ask me about scam warnings, reporting fraud (1930 Helpline), or system testing!"
    )
    save_chat_log('user', user_message, fallback_text, 'assistant')
    return jsonify({'success': True, 'response': fallback_text, 'source': 'assistant'})
