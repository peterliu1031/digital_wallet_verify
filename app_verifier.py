import os
import requests
import random
import string
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

ACCESS_TOKEN = os.getenv("VERIFIER_ACCESS_TOKEN")
VERIFIER_REF = os.getenv("VERIFIER_REF")
API_QRCODE = "https://verifier-sandbox.wallet.gov.tw/api/oidvp/qrcode"
API_POLL   = "https://verifier-sandbox.wallet.gov.tw/api/oidvp/transaction"

def generate_nonce(length=30):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

@app.route('/api/generate-vp-qrcode', methods=['POST'])
def generate_vp_qrcode():
    nonce = generate_nonce(30)
    headers = {
        'Access-Token': ACCESS_TOKEN,
        'Content-Type': 'application/json',
        'accept': 'application/json'
    }
    payload = {
        "ref": VERIFIER_REF,
        "nonce": nonce
    }
    resp = requests.post(API_QRCODE, headers=headers, json=payload)
    if not str(resp.status_code).startswith("2"):
        return jsonify({'error': f'API錯誤: {resp.status_code}, {resp.text}'}), 500
    result = resp.json()
    return jsonify({
        'qrcode': result.get('qrcodeImage'),
        'authUri': result.get('authUri'),
        'transactionId': result.get('transactionId')
    })

@app.route('/api/generate-vp-qrcode', methods=['GET'])
def generate_vp_qrcode():
    nonce = generate_nonce(30)
    headers = {
        'Access-Token': ACCESS_TOKEN,
        'accept': 'application/json'
    }
    params = {
        "ref": VERIFIER_REF,
        "nonce": nonce
    }
    resp = requests.get(API_QRCODE, headers=headers, params=params)
    if not str(resp.status_code).startswith("2"):
        return jsonify({'error': f'API錯誤: {resp.status_code}, {resp.text}'}), 500
    result = resp.json()
    return jsonify({
        'qrcode': result.get('qrcodeImage'),
        'authUri': result.get('authUri'),
        'transactionId': result.get('transactionId')
    })


@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory('.', 'verify.html')

@app.route('/health', methods=['GET', 'HEAD'])
def health_check():
    return {'status': 'OK'}, 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
