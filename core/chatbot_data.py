FAQ_DATABASE = [
    {
        "keywords": ["otp", "pin", "cvv", "bank", "password", "unblock", "bank account", "account blocked", "banking", "card"],
        "title": "🏦 Bank & OTP Scam Prevention",
        "response": "🔴 **BANK & OTP FRAUD WARNING**\n\n"
                    "• **How it works:** Scammers impersonate bank officials claiming your debit/credit card or account is blocked. They demand an OTP or PIN to 'unblock' it.\n"
                    "• **Golden Rule:** NO BANK will EVER ask for your OTP, Card PIN, CVV, or Internet Banking password over phone or SMS.\n"
                    "• **Immediate Action:** If you shared details, block your cards immediately via your official banking app or call your bank's 24/7 customer care number."
    },
    {
        "keywords": ["irs", "tax", "police", "cbi", "arrest", "court", "warrant", "fine", "digital arrest", "customs", "police threat", "legal"],
        "title": "👮 Impersonation & Digital Arrest Threat Scam",
        "response": "🚨 **DIGITAL ARREST & LEGAL THREAT SCAM**\n\n"
                    "• **How it works:** Scammers claim to be from IRS, Police, CBI, Cyber Crime, or Customs. They allege an illegal package, unpaid tax fine, or money laundering warrant, forcing you into a 'Digital Arrest' via video/voice call.\n"
                    "• **Protection Tip:** Law enforcement officers NEVER demand money or gift cards over phone calls or conduct 'online arrest'.\n"
                    "• **Immediate Action:** Hang up immediately. Report to National Cyber Crime Portal at 1930."
    },
    {
        "keywords": ["lottery", "prize", "winner", "reward", "cash", "gift", "lucky draw", "claim", "won"],
        "title": "🎁 Fake Lottery & Prize Reward Scam",
        "response": "🎁 **LOTTERY & PRIZE FRAUD**\n\n"
                    "• **How it works:** You receive a call or message claiming you won $1,000,000 or a luxury car, but must pay a 'small processing tax' or 'registration fee' first.\n"
                    "• **Protection Tip:** Genuine lotteries NEVER ask winners to pay money upfront to claim prizes.\n"
                    "• **Immediate Action:** Do not pay any processing fee. Block the caller."
    },
    {
        "keywords": ["deepfake", "voice clone", "ai voice", "ai scam", "voice cloning", "fake voice", "family emergency", "clone"],
        "title": "🎭 Deepfake AI Voice Cloning Scam",
        "response": "🎭 **AI VOICE CLONING & DEEPFAKE CALLS**\n\n"
                    "• **How it works:** AI tools clone a relative or friend's voice using short social media clips. The scammer calls pretending your family member had an accident or emergency and urgently needs funds.\n"
                    "• **Protection Tip:** Always hang up and call your family member directly on their trusted phone number or ask a personal secret question only they would know."
    },
    {
        "keywords": ["whatsapp", "telegram", "part time", "job", "like youtube", "crypto", "investment", "task scam", "work from home"],
        "title": "💼 Part-Time Job & Crypto Investment Scam",
        "response": "💼 **PART-TIME TASK & CRYPTO INVEST SCAM**\n\n"
                    "• **How it works:** You get offered $100/day for liking YouTube videos or completing simple Telegram tasks. Later, they demand 'investment' in crypto or task deposits promising high returns, then steal your money.\n"
                    "• **Protection Tip:** Legitimate jobs do not require paying money to work.\n"
                    "• **Immediate Action:** Stop payments immediately."
    },
    {
        "keywords": ["log", "logs", "saved", "storage", "where logs", "recordings", "history", "view logs", "find logs"],
        "title": "📁 Where Are Logs & Recordings Saved?",
        "response": "📁 **CALLSHIELD LOG & RECORDING STORAGE**\n\n"
                    "1. **Live Call & Audio Recordings:** Saved directly in our secure database & accessible under **Audio Analysis / Recorded History** (`/modules/recorded`).\n"
                    "2. **Call Telemetry & Stats:** Displayed in real-time under Call Telemetry & Stats (Elapsed duration, engine latency, total words, risk score).\n"
                    "3. **Server & Trajectory Logs:** System trajectory logs are securely maintained at `~/.gemini/antigravity/brain/...` and Vercel cloud execution logs."
    },
    {
        "keywords": ["how callshield works", "live call", "automatic call", "two persons", "dual speaker", "incoming call", "speaker", "two people"],
        "title": "🎙️ Dual-Speaker Live Call Detection & Auto Connect",
        "response": "🎙️ **DUAL-SPEAKER LIVE CALL PROTECTION**\n\n"
                    "• **Automatic Incoming Call Connection:** On Android mobile devices, CallShield detects incoming phone calls and auto-launches Live Protection.\n"
                    "• **Dual-Speaker AI Listening:** Continuously listens to both Speaker 1 (Caller) and Speaker 2 (You), displaying alternating transcript turns in real-time.\n"
                    "• **Instant Risk Scoring:** Neural engine evaluates conversation patterns, calculates fraud risk score (0-100%), highlights red flags, and auto-records transcript to history!"
    },
    {
        "keywords": ["report", "helpline", "1930", "cyber crime", "complaint", "police number", "help"],
        "title": "📞 Official Scam Reporting Helplines",
        "response": "📞 **OFFICIAL FRAUD REPORTING DIRECTORY**\n\n"
                    "• **National Cyber Crime Helpline:** 1930 (India 24x7)\n"
                    "• **Official Portal:** https://cybercrime.gov.in\n"
                    "• **Bank Emergency:** Call number printed on back of your debit/credit card immediately.\n"
                    "• **US FTC Fraud Helpline:** 1-877-FTC-HELP (ftc.gov)"
    }
]

DEFAULT_RESPONSE = (
    "🤖 **CallShield Security Assistant**\n\n"
    "I can answer questions about cyber safety, scam calls, deepfake voice protection, dual-speaker live call detection, and call logs.\n\n"
    "**Try asking me:**\n"
    "• *What should I do if I shared an OTP?*\n"
    "• *How does digital arrest scam work?*\n"
    "• *How to detect AI deepfake voice calls?*\n"
    "• *Where are call logs saved?*\n"
    "• *How does dual-speaker live call detection work?*"
)
