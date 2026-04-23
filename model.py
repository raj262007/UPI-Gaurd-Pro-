

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, classification_report, 
                              confusion_matrix, roc_auc_score)
import pickle
import os
import sys

# Dataset generate karo agar exist nahi karta
if not os.path.exists('dataset.csv'):
    print("Dataset nahi mila, generate kar rahe hain...")
    # Import and run generator
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen", "generate_dataset.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    gen.generate_dataset()


def load_and_preprocess():
    """
    Data load karo aur preprocess karo.
    
    Preprocessing kyun?
    - ML models numbers samajhte hain, raw data nahi
    - Scaling se model better learn karta hai
    - Missing values handle karne padte hain
    """
    print("\n📂 Step 1: Data Load kar rahe hain...")
    df = pd.read_csv('dataset.csv')
    print(f"   Shape: {df.shape}")
    
    # Missing values check karo
    print(f"\n🔍 Step 2: Missing values check kar rahe hain...")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("   ✅ Koi missing value nahi!")
    else:
        print(f"   Missing values:\n{missing}")
        df.fillna(df.median(), inplace=True)
        print("   ✅ Missing values fill kar diye median se")
    
    # Features aur Target alag karo
    # X = input features (jo model dekhega)
    # y = output (fraud ya safe)
    feature_columns = ['amount', 'hour', 'location_code', 
                       'device_type', 'transaction_type', 'prev_txn_count']
    
    X = df[feature_columns]
    y = df['fraud']
    
    print(f"\n📊 Step 3: Data Distribution:")
    print(f"   Safe transactions: {(y==0).sum()}")
    print(f"   Fraud transactions: {(y==1).sum()}")
    
    return X, y, feature_columns


def train_model():
    """
    Model train karo aur save karo.
    """
    X, y, feature_columns = load_and_preprocess()
    
    # Train/Test Split - 80% training, 20% testing
    # Kyun? - Model jo data dekhega, uspe toh accha perform karega hi
    # Isliye unseen data (test set) pe test karte hain
    print("\n✂️  Step 4: Train/Test Split kar rahe hain (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
        # stratify=y ensures fraud/safe ratio same rahe dono mein
    )
    print(f"   Training samples: {len(X_train)}")
    print(f"   Testing samples: {len(X_test)}")
    
    # Feature Scaling - amounts 50000 tak hain, hour 0-23 hai
    # Scaling ensure karta hai ki large values dominate na karein
    print("\n⚖️  Step 5: Feature Scaling kar rahe hain...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    # Note: test data pe sirf transform, fit nahi - data leakage avoid karne ke liye
    print("   ✅ StandardScaler applied")
    
    # Random Forest Model train karo
    print("\n🌲 Step 6: Random Forest Model train kar rahe hain...")
    print("   (Ye thoda time lega...)")
    
    model = RandomForestClassifier(
        n_estimators=100,    # 100 decision trees banao
        max_depth=10,         # Tree ki max depth
        min_samples_split=5,  # Node split ke liye min samples
        random_state=42,
        class_weight='balanced'  # Fraud cases kam hain, isliye weight balance karo
    )
    
    model.fit(X_train_scaled, y_train)
    print("   ✅ Model training complete!")
    
    # Model Evaluation
    print("\n📈 Step 7: Model Evaluation...")
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    auc_score = roc_auc_score(y_test, y_pred_proba)
    
    print(f"\n{'='*50}")
    print(f"   🎯 ACCURACY: {accuracy*100:.2f}%")
    print(f"   📊 AUC-ROC Score: {auc_score:.4f}")
    print(f"{'='*50}")
    
    print("\n📋 Detailed Classification Report:")
    print(classification_report(y_test, y_pred, 
                                 target_names=['Safe', 'Fraud']))
    
    print("\n🔢 Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"   True Safe: {cm[0][0]}  |  False Fraud: {cm[0][1]}")
    print(f"   Missed:    {cm[1][0]}  |  True Fraud:  {cm[1][1]}")
    
    # Feature Importance - Explainable AI ke liye
    print("\n🔍 Feature Importance (Explainable AI):")
    importances = model.feature_importances_
    for feat, imp in sorted(zip(feature_columns, importances), 
                             key=lambda x: -x[1]):
        bar = "█" * int(imp * 50)
        print(f"   {feat:20s}: {bar} {imp:.4f}")
    
    # Model aur Scaler save karo
    print("\nStep 8: Model save kar rahe hain...")
    with open('model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    with open('features.pkl', 'wb') as f:
        pickle.dump(feature_columns, f)
    
    print("model.pkl saved")
    print("scaler.pkl saved")
    print("features.pkl saved")
    
    return model, scaler, feature_columns, accuracy


def predict_transaction(transaction_data):
    """
    Naya transaction predict karo.
    
    Args:
        transaction_data: dict with transaction details
    
    Returns:
        dict with prediction, probability, risk_score, explanation
    """
    # Model load karo
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    with open('features.pkl', 'rb') as f:
        feature_columns = pickle.load(f)
    
    # Input prepare karo
    input_data = pd.DataFrame([{
        'amount': float(transaction_data['amount']),
        'hour': int(transaction_data['hour']),
        'location_code': int(transaction_data['location_code']),
        'device_type': int(transaction_data['device_type']),
        'transaction_type': int(transaction_data['transaction_type']),
        'prev_txn_count': int(transaction_data['prev_txn_count'])
    }])
    
    # Scale karo
    input_scaled = scaler.transform(input_data)
    
    # Predict karo
    prediction = model.predict(input_scaled)[0]
    probability = model.predict_proba(input_scaled)[0][1]  # Fraud probability
    
    # Risk Score calculate karo (ML + Rules combined)
    risk_score = calculate_risk_score(transaction_data, probability)
    
    # Explanation generate karo (Explainable AI)
    explanation = generate_explanation(transaction_data, risk_score)
    
    return {
        'is_fraud': bool(prediction),
        'fraud_probability': round(float(probability) * 100, 2),
        'risk_score': risk_score,
        'explanation': explanation,
        'final_verdict': get_final_verdict(risk_score)
    }


def calculate_risk_score(txn, ml_probability):
    """
    Multi-layer risk scoring system (0-100).
    
    Score 0-30: Safe ✅
    Score 31-60: Suspicious ⚠️
    Score 61-100: Fraud 🚨
    
    3 layers:
    1. ML Model score (60% weight)
    2. Rule-based score (30% weight)  
    3. Pattern score (10% weight)
    """
    
    # Layer 1: ML Score (0-60 points)
    ml_score = ml_probability * 60
    
    # Layer 2: Rule-based Engine (0-30 points)
    rule_score = 0
    
    # Rule 1: High amount
    amount = float(txn['amount'])
    if amount > 10000:
        rule_score += 15
    elif amount > 5000:
        rule_score += 8
    
    # Rule 2: Raat ka time (11pm - 4am)
    hour = int(txn['hour'])
    if hour >= 23 or hour <= 3:
        rule_score += 10
    elif hour >= 22 or hour <= 5:
        rule_score += 5
    
    # Rule 3: Location change
    location = int(txn['location_code'])
    if location == 2:  # Foreign
        rule_score += 15
    elif location == 1:  # Different city
        rule_score += 7
    
    rule_score = min(rule_score, 30)  # Max 30 points
    
    # Layer 3: Pattern Score (0-10 points)
    pattern_score = 0
    prev_txn = int(txn['prev_txn_count'])
    if prev_txn > 10:
        pattern_score += 10
    elif prev_txn > 7:
        pattern_score += 5
    
    # Final Score
    total_score = ml_score + rule_score + pattern_score
    return min(int(total_score), 100)


def generate_explanation(txn, risk_score):
    """
    Explainable AI - Kyun fraud detect hua, ye batao.
    """
    reasons = []
    
    amount = float(txn['amount'])
    hour = int(txn['hour'])
    location = int(txn['location_code'])
    prev_txn = int(txn['prev_txn_count'])
    
    if amount > 10000:
        reasons.append(f"⚠️ Very high amount ₹{amount:,.0f} detected")
    elif amount > 5000:
        reasons.append(f"⚠️ High amount ₹{amount:,.0f} detected")
    
    if hour >= 23 or hour <= 3:
        reasons.append(f"🌙 Transaction at unusual hour ({hour}:00 - late night)")
    
    if location == 2:
        reasons.append("🌍 Transaction from foreign location")
    elif location == 1:
        reasons.append("📍 Transaction from different city")
    
    if prev_txn > 10:
        reasons.append(f"📊 Too many transactions ({prev_txn}) in last 24 hours")
    
    if not reasons:
        reasons.append("✅ No suspicious patterns found")
    
    return reasons


def get_final_verdict(risk_score):
    if risk_score >= 61:
        return "FRAUD"
    elif risk_score >= 31:
        return "SUSPICIOUS"
    else:
        return "SAFE"


if __name__ == "__main__":
    print("🚀 UPI Guard Pro+ - Model Training Starting...")
    print("=" * 60)
    model, scaler, features, accuracy = train_model()
    print("\n" + "=" * 60)
    print("✅ Training Complete!")
    print(f"✅ Model Accuracy: {accuracy*100:.2f}%")
    print("\n🧪 Test prediction kar rahe hain:")
    test_txn = {
        'amount': 15000,
        'hour': 2,
        'location_code': 2,
        'device_type': 0,
        'transaction_type': 1,
        'prev_txn_count': 12
    }
    result = predict_transaction(test_txn)
    print(f"   Verdict: {result['final_verdict']}")
    print(f"   Risk Score: {result['risk_score']}/100")
    print(f"   Fraud Probability: {result['fraud_probability']}%")
    print(f"   Reasons: {result['explanation']}")
