# 🛡️ UPI Guard Pro+ — AI-Based UPI Fraud Detection System

## 📌 Project Overview
UPI Guard Pro+ ek AI-powered real-time fraud detection system hai jo UPI transactions ko 3-layer security se analyze karta hai.

---

## 🚀 Quick Start (Step by Step)

### Step 1: Project folder mein jao
```bash
cd upi_guard_pro
```

### Step 2: Libraries install karo
```bash
pip install -r requirements.txt
```

### Step 3: Dataset generate karo
```bash
python generate_dataset.py
```

### Step 4: ML Model train karo
```bash
python model.py
```
**Expected Output:** Accuracy ~100% (simulated data pe), model.pkl save hoga

### Step 5: Flask server start karo
```bash
python app.py
```

### Step 6: Browser mein open karo
- Home: http://localhost:5000
- Dashboard: http://localhost:5000/dashboard

---

## 📁 Project Structure
```
upi_guard_pro/
├── app.py              ← Flask web application (main server)
├── model.py            ← ML model + risk scoring + explainable AI
├── generate_dataset.py ← Dataset creation
├── requirements.txt    ← Python dependencies
├── dataset.csv         ← Generated dataset (after step 3)
├── model.pkl           ← Trained model (after step 4)
├── scaler.pkl          ← Feature scaler (after step 4)
├── features.pkl        ← Feature names (after step 4)
└── templates/
    ├── index.html      ← Home page (transaction form)
    ├── result.html     ← Prediction result page
    └── dashboard.html  ← Analytics dashboard
```

---

## 🧠 How It Works

### Layer 1: ML Model (Random Forest)
- 5000 transactions pe trained
- Features: amount, hour, location, device, transaction type, frequency
- Output: Fraud probability (0-100%)

### Layer 2: Rule-Based Engine
- Amount > ₹5000 → High risk
- Night time (10pm-4am) → Suspicious
- Foreign location → High risk
- 10+ transactions/day → Suspicious

### Layer 3: Risk Score (0-100)
- 0-30: SAFE ✅
- 31-60: SUSPICIOUS ⚠️
- 61-100: FRAUD 🚨

---

## 📧 Email Alerts Setup (Optional)

Email alerts ke liye environment variables set karo:
```bash
# Windows
set EMAIL_USER=your-gmail@gmail.com
set EMAIL_PASS=your-app-password
set ALERT_EMAIL=alert-receiver@gmail.com

# Mac/Linux
export EMAIL_USER=your-gmail@gmail.com
export EMAIL_PASS=your-app-password
export ALERT_EMAIL=alert-receiver@gmail.com
```

**Note:** Gmail App Password use karo (not your regular password)
Settings → Security → 2-Step Verification → App Passwords

---

## 🛠️ Tech Stack
- **Python 3.8+**
- **Flask** — Web framework
- **Scikit-learn** — Machine Learning (Random Forest)
- **Pandas + NumPy** — Data processing
- **HTML/CSS/JS** — Frontend
- **Chart.js** — Dashboard charts

---

## 📊 Dataset Features
| Feature | Description | Values |
|---------|-------------|--------|
| amount | Transaction amount | ₹10 - ₹50,000 |
| hour | Time of transaction | 0-23 |
| location_code | Location type | 0=Same, 1=Diff City, 2=Foreign |
| device_type | Device used | 0=Mobile, 1=Tablet, 2=Desktop |
| transaction_type | Type | 0=Payment, 1=Transfer, 2=Withdrawal |
| prev_txn_count | Transactions in last 24h | 0-20 |
| fraud | Target (1=Fraud) | 0 or 1 |

---

*Made with ❤️ for Final Year Project*
