import os
import sys
import csv
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'dataset', 'scam_dataset.csv')

def load_dataset():
    texts, labels = [], []
    if os.path.exists(CSV_PATH):
        print(f"[+] Loading dataset from CSV: {CSV_PATH}")
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                texts.append(row['transcript'])
                labels.append(int(row['label']))
    else:
        print("[!] Warning: CSV not found, using embedded dataset.")
        # Fallback inline dataset
        texts = [
            "Your bank account has been compromised. Share OTP immediately.",
            "This is official tax authority calling. Arrest warrant issued.",
            "Hello, I am calling to confirm your dental appointment for tomorrow."
        ]
        labels = [1, 1, 0]
    return texts, labels

def train_and_export_model():
    texts, labels = load_dataset()
    print(f"[+] Total Dataset Samples: {len(texts)}")
    
    print("[+] Building TF-IDF N-gram Vectorizer (1-3 ngrams)...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        sublinear_tf=True,
        min_df=1,
        stop_words='english'
    )
    X = vectorizer.fit_transform(texts)
    
    print("[+] Training Calibrated Logistic Regression Classifier...")
    base_model = LogisticRegression(C=2.0, max_iter=1000, random_state=42)
    model = CalibratedClassifierCV(estimator=base_model, cv=3)
    model.fit(X, labels)
    
    output_dir = os.path.join(BASE_DIR, 'core')
    os.makedirs(output_dir, exist_ok=True)
    
    vec_path = os.path.join(output_dir, 'tfidf_vectorizer.pkl')
    model_path = os.path.join(output_dir, 'scam_ml_model.pkl')
    
    joblib.dump(vectorizer, vec_path)
    joblib.dump(model, model_path)
    
    print(f"[+] Model saved to: {model_path}")
    print(f"[+] Vectorizer saved to: {vec_path}")
    
    test_sample = "Your bank account has been compromised. Please kindly share the OTP immediately."
    vec_sample = vectorizer.transform([test_sample])
    prob = model.predict_proba(vec_sample)[0][1]
    print(f"[+] Test Sample Fraud Score: {prob * 100:.2f}%")

if __name__ == '__main__':
    train_and_export_model()
