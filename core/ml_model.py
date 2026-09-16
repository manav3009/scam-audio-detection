import os
import math
import re
import pickle

class ScamClassifierML:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(self.base_dir, 'scam_ml_model.pkl')
        self.vectorizer_path = os.path.join(self.base_dir, 'tfidf_vectorizer.pkl')
        
        # Built-in TF-IDF Naive Bayes Vocabulary & Feature Weights
        self.scam_vocab = {
            'otp': 4.5, 'bank': 3.8, 'account': 3.2, 'compromised': 4.2, 'unblock': 4.0,
            'pin': 4.5, 'cvv': 4.8, 'card': 3.5, 'urgent': 3.0, 'immediate': 3.2,
            'police': 3.8, 'warrant': 4.5, 'arrest': 4.5, 'fine': 3.2, 'tax': 3.5,
            'lottery': 4.5, 'prize': 4.2, 'won': 4.0, 'reward': 3.5, 'processing fee': 4.8,
            'security deposit': 4.2, 'transfer': 3.5, 'gpay': 3.8, 'paytm': 3.5, 'upi': 3.8,
            'customs': 4.0, 'parcel': 3.5, 'kyc': 4.2, 'expired': 3.2, 'bail': 4.5,
            'anydesk': 4.8, 'teamviewer': 4.8, 'refund': 3.5, 'secret code': 4.5
        }
        self.legit_vocab = {
            'appointment': -2.5, 'dinner': -3.0, 'home': -2.0, 'delivered': -2.2,
            'library': -2.5, 'project': -1.8, 'doctor': -2.0, 'meeting': -1.5,
            'birthday': -3.0, 'groceries': -2.5, 'flight': -2.0, 'broadband': -1.5
        }
        
        self.sklearn_model = None
        self.sklearn_vectorizer = None
        self.load_sklearn_model()

    def load_sklearn_model(self):
        """Attempts to load Scikit-Learn trained model if available."""
        try:
            import joblib
            if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
                self.sklearn_vectorizer = joblib.load(self.vectorizer_path)
                self.sklearn_model = joblib.load(self.model_path)
                print("[+] Scikit-Learn Serialized Model Loaded.")
        except Exception:
            pass

    def predict(self, text):
        """Predicts scam probability percentage (0.0 to 100.0%) and risk classification."""
        if not text or not text.strip():
            return {
                'ml_score': 0.0,
                'ml_risk': 'Safe',
                'confidence': '100%',
                'top_features': [],
                'is_scam': False
            }

        text_clean = text.lower().strip()
        
        # Scikit-Learn Inference if loaded
        if self.sklearn_model is not None and self.sklearn_vectorizer is not None:
            try:
                vec = self.sklearn_vectorizer.transform([text_clean])
                proba = self.sklearn_model.predict_proba(vec)[0][1]
                score = round(proba * 100, 1)
                
                feature_names = self.sklearn_vectorizer.get_feature_names_out()
                dense_vec = vec.toarray()[0]
                top_indices = dense_vec.argsort()[-4:][::-1]
                top_features = [feature_names[i] for i in top_indices if dense_vec[i] > 0]
                
                return self._format_result(score, top_features)
            except Exception:
                pass

        # Standalone TF-IDF Naive Bayes Log-Likelihood Engine
        log_odds = 0.0
        matched_features = []
        words = re.findall(r'\w+', text_clean)
        
        # Check N-grams (1-gram, 2-gram)
        for term, weight in self.scam_vocab.items():
            if term in text_clean:
                log_odds += weight
                matched_features.append(term)

        for term, weight in self.legit_vocab.items():
            if term in text_clean:
                log_odds += weight

        # Sigmoid calibration: P(scam) = 1 / (1 + e^(-log_odds + bias))
        sigmoid_score = 1.0 / (1.0 + math.exp(-1.0 * (log_odds - 2.5)))
        score = round(sigmoid_score * 100, 1)

        # Baseline check if specific trigger words are present
        if any(w in text_clean for w in ['otp', 'cvv', 'pin', 'bank account', 'arrest warrant', 'lottery prize']):
            score = max(score, 78.5)

        return self._format_result(score, matched_features[:4])

    def _format_result(self, score, top_features):
        if score >= 80.0:
            risk = 'Critical'
        elif score >= 60.0:
            risk = 'High'
        elif score >= 40.0:
            risk = 'Medium-High'
        elif score >= 25.0:
            risk = 'Medium'
        elif score >= 12.0:
            risk = 'Low'
        else:
            risk = 'Safe'

        return {
            'ml_score': score,
            'ml_risk': risk,
            'confidence': f"{min(99, int(85 + score * 0.14))}%",
            'top_features': top_features,
            'is_scam': score >= 35.0
        }
