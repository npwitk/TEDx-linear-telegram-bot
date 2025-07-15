from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
LINEAR_WEBHOOK_SECRET = os.environ.get('LINEAR_WEBHOOK_SECRET')

# Hardcoded URLs
GOOGLE_SHEET_URL_HARDCODED = "https://docs.google.com/spreadsheets/d/1Kqf3FMwnvb3zZunxLhRyJaRKVOvGR_f46ZtbawVvh1s/"
LINEAR_BASE_URL = "https://linear.app/tedxthammasatu/issue/"

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
                old_state_name = old_data['state'].get('name', 'Unknown') # Get old state name for comparison

                if new_state_name == 'In Approval' and old_state_name != 'In Approval': # Ensure it just moved to In Approval
                    issue_title = issue_data.get('title', 'N/A')
                    issue_identifier = issue_data.get('identifier', 'N/A')
                    assignee_name = issue_data.get('assignee', {}).get('name', 'Unassigned')
                    
                    telegram_message = (
                        "งาน <b>{issue_title} ({issue_identifier})</b> ของ {assignee_name} ถูกย้ายไปที่สถานะ <b>In Approval</b> แล้วนะครับ ✨ \n"
                        "📌 ฝากทีม Marketing ช่วยตรวจสอบด้วยนะครับ \n"
                        "✅ ถ้างานผ่านแล้ว รบกวนย้ายไปที่ Done \n"
                        f"📝 ถ้ายังไม่ผ่าน รบกวนคอมเมนต์บนงาน <b>{issue_identifier}</b> เพื่อให้ผู้รับงานนำไปปรับแก้ครับ"
                    )

                    linear_issue_url = f"{LINEAR_BASE_URL}{issue_identifier}"
                    
                    send_telegram_message(telegram_message, linear_issue_url, GOOGLE_SHEET_URL_HARDCODED)

        return jsonify({"status": "success"}), 200
    return jsonify({"status": "method not allowed"}), 405


def send_telegram_message(message, linear_url, content_sheet_url):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "🚀 Open Linear Issue", "url": linear_url},
                {"text": "📝 Content Sheet", "url": content_sheet_url}
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