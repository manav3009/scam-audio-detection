import os
import sys
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_model import TRAINING_DATA
from core.ml_model import ScamClassifierML

def evaluate_research_metrics():
    print("==================================================================")
    print("   CALLSHIELD AI — MACHINE LEARNING RESEARCH MODEL EVALUATION   ")
    print("==================================================================")

    texts, labels = zip(*TRAINING_DATA)
    labels = np.array(labels)

    # Initialize ML Model
    ml = ScamClassifierML()
    
    # Predict probabilities for all evaluation dataset samples
    y_true = labels
    y_pred = []
    y_prob = []

    for text in texts:
        res = ml.predict(text)
        prob = res['ml_score'] / 100.0
        y_prob.append(prob)
        y_pred.append(1 if prob >= 0.45 else 0)

    y_pred = np.array(y_pred)
    y_prob = np.array(y_prob)

    # Compute Core Evaluation Metrics
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, y_prob)
    cm = confusion_matrix(y_true, y_pred)

    tn, fp, fn, tp = cm.ravel()
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 1.0

    print(f"[+] Overall Model Accuracy  : {acc * 100:.2f}%")
    print(f"[+] Precision (PPV)         : {prec * 100:.2f}%")
    print(f"[+] Recall (Sensitivity)    : {rec * 100:.2f}%")
    print(f"[+] Specificity (TNR)       : {specificity * 100:.2f}%")
    print(f"[+] F1-Score (Harmonic Mean): {f1 * 100:.2f}%")
    print(f"[+] ROC-AUC Metric Score    : {auc:.4f}")
    print("------------------------------------------------------------------")
    print("Confusion Matrix:")
    print(f"  True Positives  (TP) : {tp}   (Scams correctly identified)")
    print(f"  True Negatives  (TN) : {tn}   (Safe calls correctly identified)")
    print(f"  False Positives (FP) : {fp}   (Safe calls wrongly flagged)")
    print(f"  False Negatives (FN) : {fn}   (Scams missed)")
    print("==================================================================")

if __name__ == '__main__':
    evaluate_research_metrics()
