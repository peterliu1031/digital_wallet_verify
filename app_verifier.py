import os
import uuid
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

ACCESS_TOKEN = os.getenv("VERIFIER_ACCESS_TOKEN")
VERIFIER_REF = os.getenv("VERIFIER_REF")
API_QRCODE = "https://verifier-sandbox.wallet.gov.tw/api/oidvp/qrcode"

@app.route('/api/generate-vp-qrcode', methods=['GET'])
def generate_vp_qrcode():
    # 生成 UUID v4，作為 transactionId，長度36字元，符合官方建議且 < 50
    transaction_id = str(uuid.uuid4())

    headers = {
        'Access-Token': ACCESS_TOKEN,
        'accept': 'application/json'
    }
    params = {
        'ref': VERIFIER_REF,
        'transactionId': transaction_id
    }
    # 呼叫官方 GET API，帶 ref 與 transactionId
    resp = requests.get(API_QRCODE, headers=headers, params=params)

    if not str(resp.status_code).startswith("2"):
        return jsonify({'error': f'API錯誤: {resp.status_code}, {resp.text}'}), 500

    result = resp.json()
    # 回傳前端：QR code 圖片，啟動位址，交易序號
    return jsonify({
        'qrcode': result.get('qrcodeImage'),
        'authUri': result.get('authUri'),
        'transactionId': transaction_id  # 用自己產生的 transaction_id 傳回前端
    })

@app.route('/', methods=['GET'])
def serve_index():
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(BASE_DIR, 'verify.html')  # 依GitHub專案改成 verify.html

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
