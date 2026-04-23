# UPI Guard Pro+
 
A fraud detection web app built on top of a Random Forest classifier that analyzes UPI transactions and flags them as **Safe**, **Suspicious**, or **Fraud** — with an explanation for every decision.
 
The idea came from a simple frustration: UPI fraud is increasingly common in India, but most people have no way to quickly check whether a transaction looks legitimate before acting on it. This project is a step toward making that kind of check accessible.
 
---
 
## What it does
 
You enter details about a transaction — amount, time, location, device, type, and how many transactions happened in the last 24 hours — and the system runs it through three layers of analysis:
 
1. **ML Model** — A Random Forest trained on transaction data that outputs a fraud probability
2. **Rule Engine** — Hand-crafted rules covering known fraud signals (late-night transfers, foreign locations, unusually high amounts)
3. **Pattern Check** — Flags accounts with abnormally high transaction frequency
These three scores are combined into a single **Risk Score (0–100)**, and a final verdict is returned with the specific reasons behind it.
 
You can also upload a screenshot of the payment for audit purposes, and if a transaction is marked as fraud, an email alert fires automatically.
 
---
 
## Risk Score Breakdown
 
| Score | Verdict | What it means |
|-------|---------|---------------|
| 0 – 30 | ✅ Safe | Transaction looks normal |
| 31 – 60 | ⚠️ Suspicious | Some unusual patterns detected |
| 61 – 100 | 🚨 Fraud | High risk — likely fraudulent |
 
---
 
## Tech Stack
 
- **Flask** — Backend and routing
- **Scikit-learn** — Random Forest model
- **Pandas / NumPy** — Data handling and preprocessing
- **Chart.js** — Dashboard visualizations
- **SMTP (Gmail)** — Fraud alert emails
---
 
## Project Structure
 
```
upi_guard_pro/
├── app.py                 # Flask server, routes, email alerts
├── model.py               # Model training, risk scoring, explainability
├── generate_dataset.py    # Synthetic dataset generator
├── requirements.txt       # Python dependencies
├── dataset.csv            # Generated training data
├── model.pkl              # Saved trained model
├── scaler.pkl             # StandardScaler for feature normalization
├── features.pkl           # Feature column names
└── templates/
    ├── index.html         # Transaction input form
    ├── result.html        # Prediction result page
    └── dashboard.html     # Live analytics dashboard
```
 
---
 
## Getting Started
 
**1. Clone the repo**
```bash
git clone https://github.com/yourusername/upi-guard-pro.git
cd upi-guard-pro
```
 
**2. Install dependencies**
```bash
pip install -r requirements.txt
```
 
**3. Generate the dataset**
```bash
python generate_dataset.py
```
 
**4. Train the model**
```bash
python model.py
```
This saves `model.pkl`, `scaler.pkl`, and `features.pkl` to disk.
 
**5. Start the server**
```bash
python app.py
```
 
**6. Open in browser**
```
Main app  →  http://localhost:5000
Dashboard →  http://localhost:5000/dashboard
```
 
---
 
## Email Alerts (Optional)
 
When a transaction is flagged as fraud, the app can send an automatic email alert. To enable this, set these environment variables before starting the server:
 
```bash
# Windows
set EMAIL_USER=your@gmail.com
set EMAIL_PASS=your_app_password
set ALERT_EMAIL=receiver@gmail.com
 
# Mac / Linux
export EMAIL_USER=your@gmail.com
export EMAIL_PASS=your_app_password
export ALERT_EMAIL=receiver@gmail.com
```
 
Use a Gmail App Password, not your regular account password. You can generate one under **Google Account → Security → 2-Step Verification → App Passwords**.
 
---
 
## Features Used by the Model
 
| Feature | Description |
|---------|-------------|
| `amount` | Transaction amount in INR |
| `hour` | Hour of the day (0–23) |
| `location_code` | 0 = same city, 1 = different city, 2 = foreign |
| `device_type` | 0 = mobile, 1 = tablet, 2 = desktop |
| `transaction_type` | 0 = payment, 1 = transfer, 2 = withdrawal |
| `prev_txn_count` | Number of transactions in the last 24 hours |
 
---
 
## Planned Improvements
 
- OCR integration to auto-extract transaction details from uploaded screenshots
- Persistent storage with a proper database instead of in-memory history
- SMS alerts via Twilio
- Integration with real UPI transaction APIs
---
 
## License
 
