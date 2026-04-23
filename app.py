

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import sys
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Model functions import karo
from model import predict_transaction
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)

# Upload configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if not exists
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create upload folder (possibly read-only FS): {e}")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Transaction history store karne ke liye (in-memory - production mein database use karo)
transaction_history = []

# ============================================================
# EMAIL ALERT SYSTEM
# ============================================================
def send_fraud_alert(transaction_data, result):
    """
    Fraud detect hone par email alert bhejo.
    
    Note: Ye function sirf tab kaam karega jab aapne
    EMAIL_USER aur EMAIL_PASS environment variables set ki hon.
    Demo ke liye console mein print kar dete hain.
    """
    
    # Email credentials (environment variables se lo - security ke liye)
    EMAIL_USER = os.environ.get('EMAIL_USER', '')
    EMAIL_PASS = os.environ.get('EMAIL_PASS', '')
    ALERT_TO = os.environ.get('ALERT_EMAIL', EMAIL_USER)
    
    if not EMAIL_USER or not EMAIL_PASS:
        # Demo mode - console mein print karo
        print("\nFRAUD ALERT! (Email not configured - showing in console)")
        print(f"   Amount: Rupee {transaction_data.get('amount')}")
        print(f"   Risk Score: {result['risk_score']}/100")
        print(f"   Reasons: {result['explanation']}")
        return False
    
    try:
        # Email message banao
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"UPI Guard Pro+ - FRAUD ALERT! Risk Score: {result['risk_score']}/100"
        msg['From'] = EMAIL_USER
        msg['To'] = ALERT_TO
        
        html_body = f"""
        <html><body style="font-family: Arial; padding: 20px;">
            <h2 style="color: red;">🚨 FRAUD TRANSACTION DETECTED!</h2>
            <table border="1" cellpadding="10" style="border-collapse: collapse;">
                <tr><td><b>Amount</b></td><td>₹{transaction_data.get('amount')}</td></tr>
                <tr><td><b>Risk Score</b></td><td style="color:red;">{result['risk_score']}/100</td></tr>
                <tr><td><b>Fraud Probability</b></td><td>{result['fraud_probability']}%</td></tr>
                <tr><td><b>Time</b></td><td>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
            </table>
            <h3>Reasons:</h3>
            <ul>
                {"".join([f"<li>{r}</li>" for r in result['explanation']])}
            </ul>
            <p><i>UPI Guard Pro+ Automated Alert System</i></p>
        </body></html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Gmail SMTP se bhejo
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, ALERT_TO, msg.as_string())
        
        print(f"Fraud alert email sent to {ALERT_TO}")
        return True
        
    except Exception as e:
        print(f"Email send failed: {e}")
        return False


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def home():
    """
    Home page - transaction input form dikhao.
    """
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """
    Transaction data receive karo aur fraud check karo.
    
    POST request mein aayega:
    - amount, hour, location_code, device_type, 
      transaction_type, prev_txn_count
    """
    try:
        # Form data lo
        transaction_data = {
            'amount': request.form.get('amount', 0),
            'hour': request.form.get('hour', 12),
            'location_code': request.form.get('location_code', 0),
            'device_type': request.form.get('device_type', 0),
            'transaction_type': request.form.get('transaction_type', 0),
            'prev_txn_count': request.form.get('prev_txn_count', 0)
        }
        
        # Validation
        if not transaction_data['amount'] or float(transaction_data['amount']) <= 0:
            return render_template('result.html', 
                                   error="Please enter a valid amount")
        
        # Handle Screenshot Upload
        screenshot_filename = None
        if 'screenshot' in request.files:
            file = request.files['screenshot']
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate unique filename
                ext = file.filename.rsplit('.', 1)[1].lower()
                unique_name = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
                screenshot_filename = unique_name

        # ML Model se predict karo
        result = predict_transaction(transaction_data)
        
        # History mein add karo
        history_entry = {
            'id': len(transaction_history) + 1,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'amount': float(transaction_data['amount']),
            'verdict': result['final_verdict'],
            'risk_score': result['risk_score'],
            'screenshot': screenshot_filename
        }
        transaction_history.append(history_entry)
        
        # Fraud hai toh email alert bhejo
        if result['final_verdict'] == 'FRAUD':
            send_fraud_alert(transaction_data, result)
        
        return render_template('result.html', 
                               result=result, 
                               transaction=transaction_data,
                               screenshot=screenshot_filename)
    
    except Exception as e:
        return render_template('result.html', error=f"Error: {str(e)}")


@app.route('/dashboard')
def dashboard():
    """
    Dashboard - statistics aur graphs dikhao.
    """
    # Statistics calculate karo
    total = len(transaction_history)
    fraud_count = sum(1 for t in transaction_history if t['verdict'] == 'FRAUD')
    suspicious_count = sum(1 for t in transaction_history if t['verdict'] == 'SUSPICIOUS')
    safe_count = sum(1 for t in transaction_history if t['verdict'] == 'SAFE')
    
    stats = {
        'total': total,
        'fraud': fraud_count,
        'suspicious': suspicious_count,
        'safe': safe_count,
        'fraud_rate': round((fraud_count / total * 100), 1) if total > 0 else 0
    }
    
    return render_template('dashboard.html', 
                           stats=stats, 
                           history=transaction_history[-10:])  # Last 10 transactions


@app.route('/api/history')
def api_history():
    """
    JSON format mein history return karo (Dashboard charts ke liye).
    """
    return jsonify(transaction_history)


@app.route('/api/stats')
def api_stats():
    """
    Real-time statistics API.
    """
    total = len(transaction_history)
    fraud_count = sum(1 for t in transaction_history if t['verdict'] == 'FRAUD')
    
    return jsonify({
        'total': total,
        'fraud': fraud_count,
        'safe': total - fraud_count,
        'fraud_rate': round((fraud_count / total * 100), 1) if total > 0 else 0
    })


# ============================================================
# MAIN - SERVER SHURU KARO
# ============================================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("UPI Guard Pro+ - Starting Server")
    print("="*60)
    
    # Model files exist karte hain kya?
    if not os.path.exists('model.pkl'):
        print("Model nahi mila! Training kar rahe hain...")
        from model import train_model
        train_model()
    
    print("Model loaded successfully")
    print("Server starting at: http://localhost:5000")
    print("Dashboard at: http://localhost:5000/dashboard")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
