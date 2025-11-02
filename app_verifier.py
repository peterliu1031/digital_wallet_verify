import os
import random
import string
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

# 環境變數名稱保持一致
ACCESS_TOKEN = os.getenv("VERIFIER_ACCESS_TOKEN")
VERIFIER_REF = os.getenv("VERIFIER_REF")
API_QRCODE = "https://verifier-sandbox.wallet.gov.tw/api/oidvp/qrcode"

def generate_nonce(length=30):
    # 產生不重複且長度不超過50的隨機字串
    chars = string.ascii_letters + string.digits
    length = min(length, 50)
    return ''.join(random.choices(chars, k=length))

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
