import urllib.request
import urllib.parse
import json
import re
from flask import Blueprint, request, jsonify
from core.chatbot_data import FAQ_DATABASE
from core.database import save_chat_log

chatbot_bp = Blueprint('chatbot', __name__)

GREETINGS = {
    'hi', 'hello', 'hey', 'namaste', 'hola', 'good morning', 'good afternoon', 'good evening'
}

def clean_query(text):
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(text.split())

def query_duckduckgo(query):
    try:
        url = 'https://api.duckduckgo.com/?q=' + urllib.parse.quote(query) + '&format=json&no_html=1&skip_disambig=1'
        req = urllib.request.Request(url, headers={'User-Agent': 'CallShield-AI/2.0'})
        with urllib.request.urlopen(req, timeout=3) as res:
            data = json.loads(res.read().decode('utf-8'))
            if data.get('Answer'):
                return f"💡 **Direct Answer:**\n{data['Answer']}"
            if data.get('AbstractText'):
                src = f"\n\n🔗 *Source: {data.get('AbstractURL', 'DuckDuckGo')}*" if data.get('AbstractURL') else ""
                return f"💡 **Summary:**\n{data['AbstractText']}{src}"
    except Exception:
        pass
    return None

def query_wikipedia(query):
    try:
        wurl = 'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=' + urllib.parse.quote(query) + '&utf8=1&format=json'
        req = urllib.request.Request(wurl, headers={'User-Agent': 'CallShield-AI/2.0 (student-project)'})
        with urllib.request.urlopen(req, timeout=3) as res:
            wdata = json.loads(res.read().decode('utf-8'))
            search_results = wdata.get('query', {}).get('search', [])
            if search_results:
                title = search_results[0]['title']
                surl = 'https://en.wikipedia.org/api/rest_v1/page/summary/' + urllib.parse.quote(title)
                sreq = urllib.request.Request(surl, headers={'User-Agent': 'CallShield-AI/2.0 (student-project)'})
                with urllib.request.urlopen(sreq, timeout=3) as sres:
                    sdata = json.loads(sres.read().decode('utf-8'))
                    extract = sdata.get('extract')
                    if extract:
                        page_url = sdata.get('content_urls', {}).get('desktop', {}).get('page', '')
                        link = f"\n\n🔗 *Read more on Wikipedia:* {page_url}" if page_url else ""
                        return f"📚 **{title}**\n\n{extract}{link}"
    except Exception:
        pass
    return None

@chatbot_bp.route('/api/chatbot', methods=['POST'])
def chatbot_response():
    data = request.json or {}
    raw_message = data.get('message', '').strip()
    user_message = raw_message.lower()
    
    if not user_message:
        welcome = ("👋 **Hello! I am CallShield AI Assistant.**\n\n"
                   "I can answer all your questions about:\n"
                   "• 🛡️ Scam calls, OTP fraud, and digital arrest threats\n"
                   "• 💻 Technology, AI, coding, and mobile devices\n"
                   "• 🌍 General knowledge, science, history, and definitions\n"
                   "• 📞 How CallShield protects your calls in real-time\n\n"
                   "Feel free to ask me anything!")
        save_chat_log('user', '', welcome, 'assistant')
        return jsonify({'success': True, 'response': welcome, 'source': 'assistant'})

    # 1. Check Greetings
    if user_message in GREETINGS or user_message.startswith(('hi ', 'hello ', 'hey ')):
        greet_resp = ("👋 **Hello! How can I help you today?**\n\n"
                      "You can ask me about scam protection, cybersecurity, or any general question in tech, science, or daily topics!")
        save_chat_log('user', raw_message, greet_resp, 'assistant')
        return jsonify({'success': True, 'response': greet_resp, 'source': 'assistant'})

    # 2. Check "who are you" / "what is callshield"
    if any(p in user_message for p in ['who are you', 'what is callshield', 'what can you do', 'what are you']):
        about_resp = ("🛡️ **I am CallShield AI Assistant!**\n\n"
                      "I am an intelligent security and knowledge assistant designed to protect you from fraudulent calls, fake bank requests, and cyber threats.\n\n"
                      "**My Capabilities:**\n"
                      "1. 📞 Explain scam techniques (Bank OTP, Digital Arrest, Lottery, AI Voice Cloning)\n"
                      "2. 🎙️ Guide you on using Voice Scan & Live Call Interception\n"
                      "3. 🌐 Answer general questions on technology, science, everyday topics, and online safety.\n\n"
                      "Ask me any question and I'll find the answer for you!")
        save_chat_log('user', raw_message, about_resp, 'assistant')
        return jsonify({'success': True, 'response': about_resp, 'source': 'assistant'})

    # 3. Check Specialized Security FAQ Database
    best_match = None
    best_score = 0
    for item in FAQ_DATABASE:
        score = sum(1 for kw in item['keywords'] if kw in user_message)
        if score > best_score:
            best_score = score
            best_match = item
            
    if best_match and best_score >= 1:
        formatted = f"{best_match['title']}\n\n{best_match['response']}"
        save_chat_log('user', raw_message, formatted, 'security_database')
        return jsonify({'success': True, 'response': formatted, 'source': 'security_database'})

    # 4. Universal Live DuckDuckGo Query
    ddg_res = query_duckduckgo(raw_message)
    if ddg_res:
        save_chat_log('user', raw_message, ddg_res, 'duckduckgo')
        return jsonify({'success': True, 'response': ddg_res, 'source': 'duckduckgo'})

    # 5. Universal Live Wikipedia Search & Extract
    wiki_res = query_wikipedia(raw_message)
    if wiki_res:
        save_chat_log('user', raw_message, wiki_res, 'wikipedia')
        return jsonify({'success': True, 'response': wiki_res, 'source': 'wikipedia'})

    # 6. Intelligent General Knowledge & Safety Advice Fallback
    fallback_resp = (f"🤖 **Answer regarding \"{raw_message}\":**\n\n"
                     f"Here is helpful guidance on your topic:\n"
                     f"• Make sure to verify details using official channels and secure websites (https).\n"
                     f"• If this relates to a phone call or digital message, remember never to share passwords, OTPs, or financial info.\n"
                     f"• For cyber fraud or scam reporting in India, call National Helpline **1930** or visit `cybercrime.gov.in`.\n\n"
                     f"Feel free to ask more specific questions about this topic!")
    save_chat_log('user', raw_message, fallback_resp, 'knowledge_engine')
    return jsonify({'success': True, 'response': fallback_resp, 'source': 'knowledge_engine'})
