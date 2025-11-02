import os
import uuid
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

ACCESS_TOKEN = os.getenv("VERIFIER_ACCESS_TOKEN")
VERIFIER_REF = os.getenv("VERIFIER_REF")
API_QRCODE = "https://verifier-sandbox.wallet.gov.tw/api/oidvp/qrcode"
API_RESULT = "https://verifier-sandbox.wallet.gov.tw/api/oidvp/result"

@app.route('/api/generate-vp-qrcode', methods=['GET'])
def generate_vp_qrcode():
    transaction_id = str(uuid.uuid4())
    headers = {
        'Access-Token': ACCESS_TOKEN,
        'accept': 'application/json'
    }
    params = {
        'ref': VERIFIER_REF,
        'transactionId': transaction_id
    }
    resp = requests.get(API_QRCODE, headers=headers, params=params)

    if not str(resp.status_code).startswith("2"):
        return jsonify({'error': f'API錯誤: {resp.status_code}, {resp.text}'}), 500

    result = resp.json()
    return jsonify({
        'qrcode': result.get('qrcodeImage'),
        'authUri': result.get('authUri'),
        'transactionId': transaction_id
    })

@app.route('/api/poll-transaction', methods=['GET'])
def poll_transaction():
    transaction_id = request.args.get('transactionId')
    if not transaction_id:
        return jsonify({'error': '缺少 transactionId'}), 400

    headers = {
        'Access-Token': ACCESS_TOKEN,
        'accept': 'application/json'
    }
    params = {
        'transactionId': transaction_id
    }
    resp = requests.get(API_RESULT, headers=headers, params=params)

    if resp.status_code == 200:
        # 使用者已成功上傳資料，驗證通過
        return jsonify({'received': True, 'data': resp.json()})
    elif resp.status_code == 400:
        # 尚未上傳資料，等待中
        return jsonify({'received': False})
    else:
        return jsonify({'error': f'伺服器錯誤: {resp.status_code}'}), resp.status_code

@app.route('/', methods=['GET'])
def serve_index():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(BASE_DIR, 'verify.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
