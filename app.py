from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import sys
import re
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from model import predict_transaction
from werkzeug.utils import secure_filename
import uuid

# OCR Libraries
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    OCR_AVAILABLE = True
    print("✅ OCR (pytesseract) available hai - Image analysis ON")
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️  pytesseract install nahi hai - Image analysis OFF")
    print("   Install karo: pip install pytesseract pillow")

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

transaction_history = []


# ============================================================
# OCR - IMAGE SE DATA EXTRACT KARO
# ============================================================

def preprocess_image(img):
    """Image quality improve karo taaki OCR better kaam kare."""
    img = img.convert('L')  # Grayscale
    width, height = img.size
    if width < 800:
        scale = 800 / width
        img = img.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)
    img = img.filter(ImageFilter.MedianFilter(size=1))
    return img


def extract_text_from_image(filepath):
    """Image se raw text extract karo using Tesseract OCR."""
    if not OCR_AVAILABLE:
        return None, "OCR library install nahi hai"
    try:
        img = Image.open(filepath)
        processed_img = preprocess_image(img)
        config = '--oem 3 --psm 6'
        text = pytesseract.image_to_string(processed_img, config=config)
        return text.strip(), None
    except Exception as e:
        return None, f"Image read error: {str(e)}"


def parse_amount(text):
    """
    OCR text se transaction amount nikalo.
    Supports: Rs.1500 / INR 1500 / Amount: 1500 / 1,50,000
    """
    if not text:
        return None
    patterns = [
        r'(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)',
        r'(?:amount|total|paid|debited|sent|transferred|deducted)[:\s]+(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d{1,2})?)',
        r'\b([\d]{1,3}(?:,[\d]{2,3})+(?:\.\d{1,2})?)\b',
        r'\b([\d]{4,}(?:\.\d{1,2})?)\b',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                clean = match.replace(',', '')
                try:
                    val = float(clean)
                    if 1 <= val <= 1000000:
                        return val
                except:
                    continue
    return None


def parse_time(text):
    """OCR text se transaction time nikalo. Supports HH:MM AM/PM and 24hr format."""
    if not text:
        return None
    patterns = [
        r'\b(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)\b',
        r'\b([01]?\d|2[0-3]):([0-5]\d)\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            hour = int(groups[0])
            if len(groups) == 3 and groups[2]:
                meridiem = groups[2].upper()
                if meridiem == 'PM' and hour != 12:
                    hour += 12
                elif meridiem == 'AM' and hour == 12:
                    hour = 0
            if 0 <= hour <= 23:
                return hour
    return None


def parse_location_hint(text):
    """Foreign keywords dhundo."""
    if not text:
        return None
    text_lower = text.lower()
    foreign_keywords = ['usd', 'eur', 'gbp', 'foreign', 'international',
                        'overseas', 'abroad', 'outside india']
    for kw in foreign_keywords:
        if kw in text_lower:
            return 2
    return None


def analyze_screenshot(filepath):
    """Main OCR function - screenshot se transaction data extract karo."""
    result = {
        'ocr_success': False,
        'raw_text': '',
        'extracted': {'amount': None, 'hour': None, 'location_code': None},
        'confidence': {},
        'ocr_error': None
    }
    raw_text, error = extract_text_from_image(filepath)
    if error:
        result['ocr_error'] = error
        return result
    result['raw_text'] = raw_text
    result['ocr_success'] = True
    amount = parse_amount(raw_text)
    if amount:
        result['extracted']['amount'] = amount
        result['confidence']['amount'] = 'high' if ('₹' in raw_text or 'Rs' in raw_text) else 'medium'
    hour = parse_time(raw_text)
    if hour is not None:
        result['extracted']['hour'] = hour
        result['confidence']['hour'] = 'high'
    location = parse_location_hint(raw_text)
    if location is not None:
        result['extracted']['location_code'] = location
        result['confidence']['location_code'] = 'medium'
    return result


# ============================================================
# EMAIL ALERT SYSTEM
# ============================================================
def send_fraud_alert(transaction_data, result):
    EMAIL_USER = os.environ.get('EMAIL_USER', '')
    EMAIL_PASS = os.environ.get('EMAIL_PASS', '')
    ALERT_TO = os.environ.get('ALERT_EMAIL', EMAIL_USER)
    if not EMAIL_USER or not EMAIL_PASS:
        print("\nFRAUD ALERT! (Email not configured - showing in console)")
        print(f"   Amount: Rupee {transaction_data.get('amount')}")
        print(f"   Risk Score: {result['risk_score']}/100")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"UPI Guard Pro+ - FRAUD ALERT! Risk Score: {result['risk_score']}/100"
        msg['From'] = EMAIL_USER
        msg['To'] = ALERT_TO
        html_body = f"""
        <html><body style="font-family: Arial; padding: 20px;">
            <h2 style="color: red;">FRAUD TRANSACTION DETECTED!</h2>
            <table border="1" cellpadding="10" style="border-collapse: collapse;">
                <tr><td><b>Amount</b></td><td>Rs.{transaction_data.get('amount')}</td></tr>
                <tr><td><b>Risk Score</b></td><td style="color:red;">{result['risk_score']}/100</td></tr>
                <tr><td><b>Fraud Probability</b></td><td>{result['fraud_probability']}%</td></tr>
                <tr><td><b>Time</b></td><td>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
            </table>
        </body></html>
        """
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, ALERT_TO, msg.as_string())
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        transaction_data = {
            'amount': request.form.get('amount', 0),
            'hour': request.form.get('hour', 12),
            'location_code': request.form.get('location_code', 0),
            'device_type': request.form.get('device_type', 0),
            'transaction_type': request.form.get('transaction_type', 0),
            'prev_txn_count': request.form.get('prev_txn_count', 0)
        }

        screenshot_filename = None
        ocr_data = None
        ocr_fields_used = []

        if 'screenshot' in request.files:
            file = request.files['screenshot']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                unique_name = f"{uuid.uuid4().hex}.{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                file.save(filepath)
                screenshot_filename = unique_name

                if OCR_AVAILABLE:
                    print(f"\n OCR Analysis: {unique_name}")
                    ocr_data = analyze_screenshot(filepath)

                    if ocr_data['ocr_success']:
                        extracted = ocr_data['extracted']

                        form_amount = request.form.get('amount', '').strip()
                        if extracted['amount'] and (not form_amount or float(form_amount) == 0):
                            transaction_data['amount'] = extracted['amount']
                            ocr_fields_used.append(f"Amount: Rs.{extracted['amount']:,.0f}")
                            print(f"   OCR Amount: Rs.{extracted['amount']}")

                        if extracted['hour'] is not None:
                            transaction_data['hour'] = extracted['hour']
                            ocr_fields_used.append(f"Time: {extracted['hour']}:00")
                            print(f"   OCR Hour: {extracted['hour']}")

                        if extracted['location_code'] is not None:
                            transaction_data['location_code'] = extracted['location_code']
                            ocr_fields_used.append("Location: Foreign detected")
                            print(f"   OCR Location: {extracted['location_code']}")

        if not transaction_data['amount'] or float(transaction_data['amount']) <= 0:
            return render_template('result.html',
                                   error="Amount enter karo ya valid screenshot upload karo")

        result = predict_transaction(transaction_data)

        history_entry = {
            'id': len(transaction_history) + 1,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'amount': float(transaction_data['amount']),
            'verdict': result['final_verdict'],
            'risk_score': result['risk_score'],
            'screenshot': screenshot_filename,
            'ocr_used': len(ocr_fields_used) > 0,
            'ocr_fields': ocr_fields_used
        }
        transaction_history.append(history_entry)

        if result['final_verdict'] == 'FRAUD':
            send_fraud_alert(transaction_data, result)

        return render_template('result.html',
                               result=result,
                               transaction=transaction_data,
                               screenshot=screenshot_filename,
                               ocr_data=ocr_data,
                               ocr_fields_used=ocr_fields_used)

    except Exception as e:
        return render_template('result.html', error=f"Error: {str(e)}")


@app.route('/dashboard')
def dashboard():
    total = len(transaction_history)
    fraud_count = sum(1 for t in transaction_history if t['verdict'] == 'FRAUD')
    suspicious_count = sum(1 for t in transaction_history if t['verdict'] == 'SUSPICIOUS')
    safe_count = sum(1 for t in transaction_history if t['verdict'] == 'SAFE')
    ocr_used_count = sum(1 for t in transaction_history if t.get('ocr_used', False))

    stats = {
        'total': total,
        'fraud': fraud_count,
        'suspicious': suspicious_count,
        'safe': safe_count,
        'fraud_rate': round((fraud_count / total * 100), 1) if total > 0 else 0,
        'ocr_used': ocr_used_count
    }
    return render_template('dashboard.html', stats=stats, history=transaction_history[-10:])


@app.route('/api/history')
def api_history():
    return jsonify(transaction_history)


@app.route('/api/stats')
def api_stats():
    total = len(transaction_history)
    fraud_count = sum(1 for t in transaction_history if t['verdict'] == 'FRAUD')
    return jsonify({
        'total': total,
        'fraud': fraud_count,
        'safe': total - fraud_count,
        'fraud_rate': round((fraud_count / total * 100), 1) if total > 0 else 0
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("UPI Guard Pro+ - Starting Server")
    print("="*60)
    if not os.path.exists('model.pkl'):
        print("Model nahi mila! Training kar rahe hain...")
        from model import train_model
        train_model()
    print("Model loaded successfully")
    if OCR_AVAILABLE:
        print("OCR: ACTIVE - Screenshot se auto-extract ON")
    else:
        print("OCR: INACTIVE - pip install pytesseract pillow karo")
    print("Server starting at: http://localhost:5000")
    print("Dashboard at: http://localhost:5000/dashboard")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=5000)