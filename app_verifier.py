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
VERIFIER_REF = os.getenv("VERIFIER_REF")  # 你的 VP 授權服務代碼 ex: 00000000_yes123123
API_QRCODE = "https://verifier-sandbox.wallet.gov.tw/api/oidvp/qrcode"
API_POLL = "https://verifier-sandbox.wallet.gov.tw/api/oidvp/transaction"

def generate_nonce(length=30):
    # 產生長度不超過50的隨機字串
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

@app.route('/api/generate-vp-qrcode', methods=['POST'])
def generate_vp_qrcode():
    nonce = generate_nonce(30)  
    headers = {
        'Access-Token': ACCESS_TOKEN,
        'accept': 'application/json'
    }
    params = {
        'ref': VERIFIER_REF,
        'nonce': nonce
    }
    resp = requests.get(API_QRCODE, headers=headers, params=params)
    if not str(resp.status_code).startswith("2"):
        return jsonify({'error': f'API錯誤: {resp.status_code}, {resp.text}'}), 500
    result = resp.json()
    print("產生驗證QRCode API回傳：", result)
    return jsonify({
        'qrcode': result.get('qrcodeImage'),
        'authUri': result.get('authUri'),
        'transactionId': result.get('transactionId')
    })

@app.route('/api/poll-verify-result', methods=['GET'])
def poll_verify_result():
    transaction_id = request.args.get('transactionId')
    if not transaction_id:
        return jsonify({'error': '缺少 transactionId'}), 400
    url = f"{API_POLL}/{transaction_id}"
    headers = {
        'Access-Token': ACCESS_TOKEN,
        'accept': 'application/json'
    }
    resp = requests.get(url, headers=headers)
    try:
        result = resp.json()
    except Exception:
        print("Polling raw:", resp.text)
        return jsonify({'error': 'API response not JSON', 'raw': resp.text}), 500
    print("Polling驗證結果:", result)
    status = result.get('status', '')
    success = (status == 'completed' or status == 'verified' or status == 'issued')
    return jsonify({
        'success': success,
        'status': status,
        'detail': result
    })

@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory('.', 'verify.html')

@app.route('/health', methods=['GET', 'HEAD'])
def health_check():
    return {'status': 'OK'}, 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
