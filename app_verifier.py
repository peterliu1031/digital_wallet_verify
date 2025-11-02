from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

ACCESS_TOKEN  = os.getenv("VERIFIER_ACCESS_TOKEN")
API_QRCODE    = "https://verifier-sandbox.wallet.gov.tw/api/oidvp/qrcode"
API_POLL      = "https://verifier-sandbox.wallet.gov.tw/api/oidvp/transaction"

@app.route('/api/generate-vp-qrcode', methods=['POST'])
def generate_vp_qrcode():
    # issuer設計：有些驗證端創建qrcode還需要帶入vpId/vp範本id等參數。根據你的API需求可自定義
    payload = request.get_json(force=True)
    vp_template_id = payload.get('vpTemplateId', '')  # 若API需求
    headers = {
        'Access-Token': ACCESS_TOKEN,
        'Content-Type': 'application/json',
        'accept': 'application/json'
    }
    # 如API要求 vpTemplateId
    data = {"vpTemplateId": vp_template_id} if vp_template_id else {}
    resp = requests.post(API_QRCODE, headers=headers, json=data)
    if not str(resp.status_code).startswith("2"):
        return jsonify({'error': f'API錯誤: {resp.status_code}, {resp.text}'}), 500
    result = resp.json()
    print("驗證端產生qrcode:", result)
    # 回傳 qrcodeImage, authUri, transactionId
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
    # 根據 result 內容判斷是否驗證通過
    status = result.get('status', '')
    success = (status == 'completed' or status == 'verified' or status == 'issued')  # 根據你API設計調整
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
