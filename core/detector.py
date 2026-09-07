import re
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

class FraudDetector:
    def __init__(self):
        self.scam_patterns = {
            'urgent_action': [
                r'\burgen(t|cy)\b', r'\bimmediate(ly)?\b', r'\bright now\b', r'\bemergency\b',
                r'\blast chance\b', r'\bwithin.*hour\b', r'\bact now\b', r'\bquick action\b',
                r'\bhurry\b', r'\brush\b', r'\binstant\b', r'\bdeadline\b', r'\bquickly\b',
                r'\blimited time\b', r'\bsoon\b', r'\bfast\b', r'\bnow\b', r'\basap\b'
            ],
            'financial_info': [
                r'\bbank\b.*\baccount\b', r'\bpassword\b', r'\bpin\b', r'\botp\b', r'\bcvv\b',
                r'\bcredit card\b', r'\bdebit card\b', r'\baccount number\b', r'\bifsc\b',
                r'\bupi\b', r'\bgoogle pay\b', r'\bphonepe\b', r'\bpaytm\b', r'\batm card\b',
                r'\bcard details\b', r'\baccount details\b', r'\bbanking information\b',
                r'\bsecret code\b', r'\bsecurity code\b', r'\bverification code\b'
            ],
            'threat_impersonation': [
                r'\bblock.*account\b', r'\bsuspend.*account\b', r'\bclose.*account\b',
                r'\blegal action\b', r'\bpolice\b', r'\bcourt\b', r'\bgovernment\b',
                r'\bincome tax\b', r'\bcustomer care\b', r'\bbank officer\b',
                r'\btech support\b', r'\bservice executive\b', r'\bofficial\b',
                r'\bauthority\b', r'\bfrom bank\b', r'\bfrom government\b',
                r'\btraffic police\b', r'\bcbi\b', r'\bed\b', r'\bit department\b'
            ],
            'emotional_manipulation': [
                r'\baccident\b', r'\bhospital\b', r'\bsick\b', r'\bemergency\b',
                r'\bfamily emergency\b', r'\bhelp me\b', r'\bsave me\b', r'\btrouble\b',
                r'\bdanger\b', r'\bpleading\b', r'\bbegging\b', r'\bcrying\b',
                r'\bpoor\b', r'\bneed money\b', r'\bdesperate\b', r'\bdying\b',
                r'\bcritical\b', r'\bhelp needed\b', r'\bplease help\b'
            ],
            'fake_rewards': [
                r'\bprize\b', r'\bwon\b', r'\blower\b', r'\blottery\b', r'\breward\b',
                r'\bwinner\b', r'\bfree gift\b', r'\bfree money\b', r'\bjackpot\b',
                r'\bbonus\b', r'\bcongratulations\b', r'\byou won\b', r'\byou have won\b',
                r'\bselected\b', r'\blucky draw\b', r'\bcash prize\b', r'\blucky winner\b',
                r'\bmillionaire\b', r'\bcrore\b', r'\blakh\b'
            ],
            'payment_demands': [
                r'\bsend money\b', r'\btransfer.*amount\b', r'\bpay now\b', r'\bdeposit\b',
                r'\bprocessing fee\b', r'\btax payment\b', r'\bsecurity deposit\b',
                r'\badvance payment\b', r'\bfee\b', r'\bcharges\b', r'\bpayment\b',
                r'\bmoney transfer\b', r'\bwire transfer\b', r'\bgift card\b',
                r'\bcryptocurrency\b', r'\bbitcoin\b', r'\bgpay\b', r'\bpaytm\b',
                r'\bphonepe\b', r'\bupi\b'
            ],
            'sensitive_info': [
                r'\baadhaar\b', r'\bpan card\b', r'\bvoter id\b', r'\bdriving license\b',
                r'\bpersonal details\b', r'\bidentity proof\b', r'\baddress proof\b',
                r'\bdate of birth\b', r'\bmother name\b', r'\bfather name\b',
                r'\bpersonal information\b', r'\bconfidential\b', r'\bdob\b'
            ],
            'verification_requests': [
                r'\bverify\b', r'\bconfirmation\b', r'\bauthentication\b', r'\bvalidation\b',
                r'\bcheck\b', r'\bconfirm\b', r'\bverify account\b', r'\bconfirm details\b',
                r'\bupdate kyc\b', r'\bkyc verification\b', r'\baccount verification\b'
            ]
        }
        
        self.keyword_weights = {
            'urgent_action': 15,
            'financial_info': 35,
            'threat_impersonation': 30,
            'emotional_manipulation': 20,
            'fake_rewards': 25,
            'payment_demands': 30,
            'sensitive_info': 25,
            'verification_requests': 15
        }
        
        self.red_flag_phrases = [
            "don't tell anyone", "keep this secret", "delete messages", "no police",
            "trust me", "i am from bank", "your account is hacked", "update kyc",
            "link expired", "click link", "share otp", "verify account", "share details",
            "bank details", "confidential information", "immediate action", "last opportunity",
            "limited time", "secret offer", "special offer", "processing fee", "security deposit",
            "advance payment", "kindly share", "please share", "unblock now", "share immediately"
        ]
        
        self.scam_patterns_full = [
            (r'(won|winner|prize|lottery).*(bank|account|details|information)', 45),
            (r'(bank|account).*(details|number|information).*(share|send|provide)', 40),
            (r'(otp|pin|cvv|password).*(share|send|provide|tell)', 50),
            (r'(urgent|immediate|emergency).*(action|response|payment)', 30),
            (r'(bank|government|official).*(calling|speaking)', 25),
            (r'(suspend|block|close).*account.*(immediate|now)', 35),
            (r'(processing fee|tax|security|advance).*(pay|payment)', 30),
            (r'(verify|confirm|update).*(account|kyc|details)', 20),
            (r'(won.*lottery|prize.*won|winner.*selected)', 40),
            (r'(accident|hospital|emergency).*(money|payment|send)', 35),
            (r'(bangkok|dubai|foreign|international).*(bank|account)', 35),
            (r'(share.*otp|otp.*share|send.*otp|otp.*send)', 50)
        ]

    def analyze_text(self, text: str) -> Dict:
        """Analyze text for fraud patterns with weighted scoring"""
        try:
            text_lower = text.lower()
            fraud_score = 0
            keywords_found = []
            patterns_detected = []
            warnings = []
            red_flags = []
            
            for pattern, weight in self.scam_patterns_full:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    fraud_score += weight
                    if 'full_scam_pattern' not in patterns_detected:
                        patterns_detected.append('full_scam_pattern')
                    warnings.append("🚨 Major scam pattern detected!")
                    match = re.search(pattern, text_lower, re.IGNORECASE)
                    if match:
                        keywords_found.append(match.group(0))
            
            for pattern_type, regex_list in self.scam_patterns.items():
                pattern_found = False
                for regex in regex_list:
                    matches = re.findall(regex, text_lower, re.IGNORECASE)
                    if matches:
                        weight = self.keyword_weights[pattern_type]
                        fraud_score += weight
                        keywords_found.extend(matches)
                        if not pattern_found:
                            patterns_detected.append(pattern_type)
                            pattern_found = True
                        
                        if pattern_type == 'financial_info':
                            warnings.append("💰 Financial information request detected!")
                        elif pattern_type == 'threat_impersonation':
                            warnings.append("👮 Possible impersonation or threat detected!")
                        elif pattern_type == 'urgent_action':
                            warnings.append("⏰ Urgency tactics detected - be careful!")
                        elif pattern_type == 'fake_rewards':
                            warnings.append("🎁 Fake reward/lottery scam detected!")
                        elif pattern_type == 'payment_demands':
                            warnings.append("💸 Payment demand detected!")
                        elif pattern_type == 'emotional_manipulation':
                            warnings.append("😢 Emotional manipulation detected!")
                        elif pattern_type == 'sensitive_info':
                            warnings.append("🔒 Sensitive information request detected!")
                        elif pattern_type == 'verification_requests':
                            warnings.append("⚠️ Verification request detected!")
            
            for phrase in self.red_flag_phrases:
                if phrase in text_lower:
                    red_flags.append(phrase)
                    fraud_score += 20
            
            if red_flags:
                warnings.append(f"🚨 Red flag phrases detected: {', '.join(red_flags[:3])}")
            
            unique_patterns = len(set(patterns_detected))
            if unique_patterns >= 3:
                bonus = min(unique_patterns * 8, 25)
                fraud_score += bonus
                warnings.append(f"⚠️ {unique_patterns} scam indicators detected simultaneously!")
            
            if 'fake_rewards' in patterns_detected and 'payment_demands' in patterns_detected:
                fraud_score += 35
                warnings.append("🚨 Classic scam pattern: Fake reward + Payment demand")
            
            if 'threat_impersonation' in patterns_detected and 'urgent_action' in patterns_detected:
                fraud_score += 30
                warnings.append("⚠️ Threat + Urgency combination detected - High risk!")
            
            if 'financial_info' in patterns_detected and 'sensitive_info' in patterns_detected:
                fraud_score += 30
                warnings.append("🔒 Financial + Sensitive information request - Identity theft risk!")
            
            word_count = len(text_lower.split())
            if word_count > 15 and fraud_score > 30:
                fraud_score += 15
            
            if 'bank' in text_lower and 'otp' in text_lower:
                fraud_score += 45
                if 'bank_otp_scam' not in patterns_detected:
                    patterns_detected.append('bank_otp_scam')
                warnings.append("🚨🚨 BANK OTP SCAM DETECTED! NEVER SHARE OTP!")
            
            if ('won' in text_lower or 'prize' in text_lower or 'lottery' in text_lower) and \
               ('bank' in text_lower or 'otp' in text_lower or 'account' in text_lower or 'fee' in text_lower):
                fraud_score += 50
                if 'lottery_scam' not in patterns_detected:
                    patterns_detected.append('lottery_scam')
                warnings.append("🎯 LOTTERY SCAM PATTERN DETECTED!")
            
            fraud_score = min(fraud_score, 100)
            
            if fraud_score < 30 and any(word in text_lower for word in 
                ['bank', 'money', 'otp', 'password', 'win', 'prize', 'lottery', 'payment', 'urgent', 'share', 'send']):
                fraud_score = 35
                warnings.append("🔍 Suspicious keywords detected - Potential scam attempt")
            
            risk_level = self.get_risk_level(fraud_score)
            warning_message = self.generate_warning_message(fraud_score, patterns_detected, red_flags)
            detailed_advice = self.get_detailed_advice(patterns_detected, red_flags)
            
            return {
                'fraud_score': round(fraud_score, 2),
                'risk_level': risk_level,
                'keywords_found': list(set(keywords_found))[:15],
                'patterns_detected': list(set(patterns_detected)),
                'red_flags': red_flags[:5],
                'warnings': list(set(warnings))[:5],
                'warning_message': warning_message,
                'detailed_advice': detailed_advice,
                'word_count': word_count,
                'analysis_time': datetime.now().strftime("%H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Error in fraud detection: {str(e)}")
            return {
                'fraud_score': 0,
                'risk_level': 'Safe',
                'keywords_found': [],
                'patterns_detected': [],
                'red_flags': [],
                'warnings': ['Analysis error'],
                'warning_message': 'Could not analyze text properly',
                'detailed_advice': 'Please try again'
            }

    def get_risk_level(self, score: float) -> str:
        if score >= 80: return 'Critical'
        elif score >= 70: return 'High'
        elif score >= 55: return 'Medium-High'
        elif score >= 40: return 'Medium'
        elif score >= 25: return 'Low'
        else: return 'Safe'

    def generate_warning_message(self, score: float, patterns: List[str], red_flags: List[str]) -> str:
        if score >= 90: return "🚨🚨 CRITICAL RISK: DEFINITE SCAM! Disconnect immediately!"
        elif score >= 80: return "🚨 CRITICAL RISK: Definitely a scam call! Do NOT share info."
        elif score >= 70: return "🚨 HIGH RISK: Appears to be a scam call! Hang up."
        elif score >= 60: return "⚠️ MEDIUM-HIGH RISK: Strong scam indicators. Verify independently."
        elif score >= 45: return "⚠️ MEDIUM RISK: Suspicious patterns. Do not share details."
        elif score >= 30: return "🔍 MODERATE RISK: Suspicious elements detected."
        elif score >= 20: return "📝 LOW RISK: Minor suspicious elements."
        else: return "✅ SAFE: No major scam patterns detected."

    def get_detailed_advice(self, patterns: List[str], red_flags: List[str]) -> str:
        advice = []
        if 'financial_info' in patterns or any('bank' in flag or 'otp' in flag for flag in red_flags):
            advice.append("🔒 NEVER share bank details, OTP, PIN, or CVV over phone")
            advice.append("🏦 Banks NEVER ask for sensitive information via call")
        if 'threat_impersonation' in patterns:
            advice.append("👮 Verify caller identity with official channels")
            advice.append("⚠️ Government officials don't demand immediate payment via phone")
        if 'urgent_action' in patterns:
            advice.append("⏰ Scammers create false urgency - take your time to verify")
        if 'fake_rewards' in patterns:
            advice.append("🎯 You can't win a lottery you didn't enter - prizes never require upfront fees")
        if not advice:
            advice.append("🛡️ Stay alert and verify before trusting unsolicited callers")
        return "`n".replace("`", "\n").join(advice)
