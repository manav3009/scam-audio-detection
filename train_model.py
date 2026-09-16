import os
import sys
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

TRAINING_DATA = [
    # --- SCAM CALL TRANSCRIPTS (Label 1) ---
    ("Your bank account has been compromised. Please kindly share the OTP immediately to unblock your debit card.", 1),
    ("This is official tax authority calling. Arrest warrant issued for unpaid tax fine. Pay $500 via Google Pay card immediately.", 1),
    ("Congratulations! You won grand lottery prize of $100000. Pay $200 processing fee to claim your cash reward.", 1),
    ("We detected virus on your computer. Download AnyDesk software and share your card PIN for technician inspection.", 1),
    ("Your credit card limit is doubled. Please verify your 16 digit card number and CVV on the phone call.", 1),
    ("Electricity bill payment overdue! Connection will be cut off in 30 minutes. Pay now via immediate UPI link.", 1),
    ("Hello sir, your parcel is stuck in customs duty. Transfer money to official clearance account now or face police action.", 1),
    ("Urgent account verification required. Provide your net banking password to prevent account termination.", 1),
    ("Your KYC is expired. Click the link sent to your phone or share the 6 digit secret verification code.", 1),
    ("Customer support calling from Amazon. A refund of $499 is approved. Share your bank credentials to process refund.", 1),
    ("Your son has been arrested in traffic accident. Pay bail money immediately via digital transfer to release him.", 1),
    ("Urgent security alert. Send OTP immediately or your SIM card will be deactivated within 1 hour.", 1),
    ("Free gift voucher worth $500! Confirm your bank account number and secret PIN to redeem voucher immediately.", 1),
    ("This is law enforcement department calling. Your national ID is involved in money laundering. Transfer funds for safety.", 1),
    ("Immediate action required. Update your bank mobile banking app password using secret code received on SMS.", 1),

    # --- LEGITIMATE CALL TRANSCRIPTS (Label 0) ---
    ("Hello, I am calling to confirm your dental appointment for tomorrow at 10 AM. Please let us know if you need to reschedule.", 0),
    ("Hi Mom, I will be reaching home by 7 PM today. Please keep dinner ready.", 0),
    ("Good morning sir, your Amazon delivery package has been delivered to your doorstep. Have a nice day.", 0),
    ("Hey John, let's meet at the library at 3 PM to work on our university group project presentation.", 0),
    ("Hello, this is Dr. Smith's office calling to remind you of your routine health checkup next Monday.", 0),
    ("Hi Alex, can you review the financial project spreadsheet I sent over email when you have time?", 0),
    ("Good afternoon, your car service is complete and ready for pickup at our service station.", 0),
    ("Hey, are we still meeting for lunch at the cafeteria today?", 0),
    ("Hello team, our weekly status meeting will start in 10 minutes on Google Meet.", 0),
    ("Hi dear, don't forget to buy milk and groceries on your way back from office.", 0),
    ("Hello, calling from ABC Telecom to inform you that your monthly broadband bill receipt has been emailed.", 0),
    ("Hi Sarah, happy birthday! Hope you have a fantastic day celebrating with family.", 0),
    ("Good morning, your flight booking confirmation has been processed. Have a safe trip.", 0),
    ("Hello, I am calling regarding your recent order inquiry. All items are in stock and ready to ship.", 0)
]

def train_and_export_model():
    texts, labels = zip(*TRAINING_DATA)
    
    print("[+] Building TF-IDF N-gram Vectorizer...")
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
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core')
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
