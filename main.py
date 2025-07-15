from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
LINEAR_WEBHOOK_SECRET = os.environ.get('LINEAR_WEBHOOK_SECRET')

GOOGLE_SHEET_URL = os.environ.get('GOOGLE_SHEET_URL')
LINEAR_BASE_URL = os.environ.get('LINEAR_BASE_URL')
GOOGLE_DRIVE_URL = os.environ.get('GOOGLE_DRIVE_URL')

if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GOOGLE_SHEET_URL, LINEAR_BASE_URL, GOOGLE_DRIVE_URL]):
    print("Error: One or more critical environment variables are not set.")
    print(f"TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN is not None}")
    print(f"TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID is not None}")
    print(f"GOOGLE_SHEET_URL: {GOOGLE_SHEET_URL is not None}")
    print(f"LINEAR_BASE_URL: {LINEAR_BASE_URL is not None}")
    print(f"GOOGLE_DRIVE_URL: {GOOGLE_DRIVE_URL is not None}")

@app.route('/')
def home():
    return "TEDx Linear Telegram Bot is running kub!!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.json
        print(f"Received Linear webhook: {data}")

        if data.get('type') == 'Issue' and data.get('action') == 'update':
            issue_data = data.get('data', {})
            old_data = data.get('oldData', {})

            if issue_data.get('state') and old_data.get('state'):
                new_state_id = issue_data['state']['id']
                old_state_id = old_data['state']['id']
                new_state_name = issue_data['state']['name']
                old_state_name = old_data['state'].get('name', 'Unknown')

                if new_state_name == 'In Approval' and old_state_name != 'In Approval': # Ensure it just moved to In Approval
                    issue_title = issue_data.get('title', 'N/A')
                    issue_identifier = issue_data.get('identifier', 'N/A')
                    assignee_name = issue_data.get('assignee', {}).get('name', 'Unassigned')
                    
                    telegram_message = (
                        f"งาน <b>{issue_title} ({issue_identifier})</b> ของ {assignee_name} ถูกย้ายไปที่สถานะ <b>In Approval</b> แล้วนะครับ ✨ \n\n"
                        "📌 ฝากทีม Marketing ช่วยตรวจสอบด้วยนะครับ \n"
                        "✅ ถ้างานผ่านแล้ว รบกวนย้ายไปที่ Done \n"
                        f"📝 ถ้ายังไม่ผ่าน รบกวนคอมเมนต์บนงาน <b>{issue_identifier}</b> เพื่อให้ผู้รับงานนำไปปรับแก้ครับ"
                    )

                    linear_issue_url = f"{LINEAR_BASE_URL}{issue_identifier}"
                    
                    send_telegram_message(telegram_message, linear_issue_url, GOOGLE_SHEET_URL, GOOGLE_DRIVE_URL)

        return jsonify({"status": "success"}), 200
    return jsonify({"status": "method not allowed"}), 405

def send_telegram_message(message, linear_url, content_sheet_url, google_drive_url):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "🚀 Open Linear", "url": linear_url},
                {"text": "📝 Content Sheet", "url": content_sheet_url}
            ],
            [
                {"text": "📁 Google Drive", "url": google_drive_url}
            ]
        ]
    }

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'reply_markup': inline_keyboard
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram message with inline keyboard sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")
        print(f"Response content: {response.text if 'response' in locals() else 'No response'}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))