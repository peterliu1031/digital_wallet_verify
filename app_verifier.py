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
CREDENTIAL_QUERY_BASE = "https://issuer-sandbox.wallet.gov.tw/api/credential/nonce"  # 依照你需求調整

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
    
    # 範例：呼叫官方API取得憑證狀態，這邊用你之前的方法簡化示範
    url = f"{CREDENTIAL_QUERY_BASE}/{transaction_id}"
    headers = {
        'Access-Token': ACCESS_TOKEN,
        'accept': 'application/json'
    }
    try:
        resp = requests.get(url, headers=headers)
        result = resp.json()
        credential = result.get('credential')
        received = False
        if credential:
            parts = credential.split('.')
            payload = parts[1]
            padded = payload + '=' * (-len(payload) % 4)
            import base64, json
            decoded = json.loads(base64.urlsafe_b64decode(padded.encode()))
            vc = decoded.get('vc', {})
            status = vc.get('credentialStatus', {})
            if status.get('statusListIndex', "0") != "0":
                received = True
        return jsonify({'received': received, 'detail': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def serve_index():
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(BASE_DIR, 'verify.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
