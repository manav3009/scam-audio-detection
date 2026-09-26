# CallShield AI — Real-Time Scam Voice Detector & Truecaller Smart Dialer

> **Final Year Engineering Capstone & Research Publication Project**  
> **System Accuracy**: **95.92%** | **ROC-AUC Score**: **0.9983** | **F1-Score**: **95.45%**  
> **Live Web Application**: [https://scam-audio-full-project.vercel.app](https://scam-audio-full-project.vercel.app)

---

## 📌 Project Overview

**CallShield AI** is an end-to-end cyber-security solution designed to detect fraudulent voice calls, scam audio recordings, and phishing attempts in real-time. Built with a **Truecaller-style Smart Dialer interface**, the system provides automatic caller ID lookup, phone contact synchronization, zero-click live call auto-recording, instant speech-to-text transcript analysis, and machine learning scam probability scoring.

---

## 🚀 Key Features

1. **Truecaller Smart Dialer & Caller ID**:
   - Integrated Truecaller-style 3x4 tactile keypad with instant trust badges (`🟢 Verified Safe`, `🟡 Suspicious Flag`, `🔴 Spam/Scam Warning`).
   - Global spam database lookup (`/api/caller_lookup`) and community spam reporting (`/api/report_spam`).
   - Seamless access to device phone contacts and recents call history log.

2. **Zero-Click Auto-Dial & Real-Time Voice Recording**:
   - Single-tap phone call placement (`tel:` protocol & native Android `Intent.ACTION_CALL`).
   - Auto-triggers the Live Call Voice Scanner (`/modules/live-call?autostart=true`) with continuous background audio recording.
   - Robust continuous speech-recognition auto-restart handling during live call pauses or network glitches.

3. **Hybrid Machine Learning & Rule-Based Scam Detection**:
   - **TF-IDF N-Gram Vectorization**: Extracts term frequencies from 1-gram to 3-gram speech features.
   - **Calibrated Classifier**: Calibrated Logistic Regression model producing probabilistic risk scores.
   - **Ensemble Risk Scoring**: Combines rule-based keyword heuristics with ML probability values.

4. **Academic Research Evaluation & Documentation**:
   - Rigorously evaluated on 49 real-world call recordings and speech transcripts.
   - Built-in PDF report generator (`generate_research_pdf.py`) producing academic publication metrics.

---

## 📊 Machine Learning Model Evaluation

| Metric | Formula | Value | Research Significance |
| :--- | :--- | :---: | :--- |
| **Accuracy** | $\frac{TP + TN}{TP + TN + FP + FN}$ | **95.92%** | High overall classification precision across real-world call samples |
| **Precision** | $\frac{TP}{TP + FP}$ | **95.45%** | Low false-positive rate; legitimate calls rarely misflagged |
| **Recall (Sensitivity)** | $\frac{TP}{TP + FN}$ | **95.45%** | High sensitivity; effectively detects active scam attempts |
| **Specificity (TNR)** | $\frac{TN}{TN + FP}$ | **96.30%** | Accurately validates safe, non-threatening conversations |
| **F1-Score** | $2 \times \frac{P \times R}{P + R}$ | **95.45%** | Balanced trade-off between precision and recall |
| **ROC-AUC** | Area Under ROC Curve | **0.9983** | Superior discriminatory power between scam & clean audio |

### Confusion Matrix ($N = 49$ Samples):
$$\begin{bmatrix} \text{TN} = 26 & \text{FP} = 1 \\ \text{FN} = 1 & \text{TP} = 21 \end{bmatrix}$$

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, Flask, SQLite / MySQL, Scikit-Learn, Joblib
- **Frontend**: HTML5, Tailwind CSS, JavaScript (ES6+), Web Speech API
- **Android App**: Java, Android SDK, WebView JS Bridge, WebChromeClient Audio Permission Handler
- **Deployment**: Vercel Serverless Functions (`vercel.json`)

---

## 💻 Installation & Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/manav3009/scam-audio-detection.git
   cd scam-audio-detection
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Train & Evaluate ML Model**:
   ```bash
   python train_model.py
   python evaluate_model.py
   ```

4. **Run Local Server**:
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your web browser.

---

## 📁 Repository Structure

```text
├── app.py                      # Flask Application Entrypoint
├── train_model.py              # ML Model Training Script
├── evaluate_model.py           # Research Model Evaluation Script
├── schema.sql                  # Database Schema Definition
├── dataset/
│   └── scam_dataset.csv        # 49 Speech Transcript Samples
├── core/
│   ├── database.py             # SQLite/MySQL DB Abstraction & Lookup Logic
│   ├── detector.py             # Hybrid Scam Detection Algorithm
│   ├── ml_model.py             # ML Model Vectorizer & Classifier Inference
│   ├── scam_ml_model.pkl       # Trained Model Asset
│   └── tfidf_vectorizer.pkl    # Serialized TF-IDF Asset
├── routes/
│   ├── analysis_routes.py      # Audio Analysis, Lookup & Spam Endpoints
│   ├── views_routes.py         # Page Routing Logic
│   └── auth_routes.py          # User Authentication
├── templates/
│   ├── base.html               # Main App Layout
│   └── modules/
│       ├── dialer.html         # Truecaller Smart Dialer & Caller ID
│       ├── live_call.html      # Real-Time Voice Scanner
│       ├── recorded.html       # Recorded File Analyzer
│       ├── awareness.html      # Scam Prevention Guide
│       └── chatbot.html        # AI Security Assistant
└── vercel.json                 # Vercel Deployment Config
```
