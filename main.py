from flask import Flask, request, jsonify
import requests
import os
import random

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
    print(f"TELEGRAM_BOT_TOKEN set: {TELEGRAM_BOT_TOKEN is not None}")
    print(f"TELEGRAM_CHAT_ID set: {TELEGRAM_CHAT_ID is not None}")
    print(f"GOOGLE_SHEET_URL set: {GOOGLE_SHEET_URL is not None}")
    print(f"LINEAR_BASE_URL set: {LINEAR_BASE_URL is not None}")
    print(f"GOOGLE_DRIVE_URL set: {GOOGLE_DRIVE_URL is not None}")

APPRECIATION_PHRASES = [
    "เยี่ยมมากกกก! ✨",
    "สุดยอดไปเลย! 🎉",
    "ยอดเยี่ยมกระเทียมเจียว! 💡",
    "โคตรเจ๋งงง! 🔥",
    "เก่งมาก ๆ ๆ ๆ ๆ!",
    "Awesome work! 🔥",
    "Fantastic job! 🙌",
    "So proud of you! 🎊",
    "You nailed it! 🔨",
    "You crushed it! 💥",
    "Bravo! 👏",
    "100% Approved! ✅",
    "Keep being amazing! 💫"
]

@app.route('/')
def home():
    return "TEDx Linear Telegram Bot is running kub!! 3+3=6"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method != 'POST':
        return jsonify({"status": "method not allowed"}), 405

    data = request.json
    print(f"Received Linear webhook: {data}")

    if data.get('type') != 'Issue' or data.get('action') not in ['update', 'create']:
        return jsonify({"status": "ignored_non_issue"}), 200

    issue_data = data.get('data', {})

    labels = issue_data.get('labels', [])
    if any(label.get('name') == 'Special' for label in labels):
        print(f"Issue {issue_data.get('identifier', 'N/A')} has 'Special' tag — skipping Telegram notification.")
        return jsonify({"status": "ignored_special"}), 200

    project_text = ""
    project_name = None
    if issue_data.get('projectId') is not None or issue_data.get('project') is not None:
        if issue_data.get('project') and issue_data['project'].get('name'):
            project_name = issue_data['project']['name']
        else:
            project_name = "an unnamed project"
        if project_name:
            project_text = f"\n\n🚨 งานนี้เป็นส่วนหนึ่งของ Project: <b>{project_name}</b>"
            print(f"Issue {issue_data.get('identifier', 'N/A')} is associated with Project: {project_name}.")
        else:
            project_text = "\n\n🚨 งานนี้เป็นส่วนหนึ่งของ Project (ไม่สามารถระบุชื่อได้)"
            print(f"Issue {issue_data.get('identifier', 'N/A')} is associated with a project, but name not found.")

    new_state_info = issue_data.get('state', {}) or {}
    new_state_name = new_state_info.get('name')
    new_state_id = new_state_info.get('id')

    updated_from = data.get('updatedFrom', {}) or {}
    old_state_id = updated_from.get('stateId')

    has_state_change = (
        old_state_id is not None and
        new_state_id is not None and
        old_state_id != new_state_id
    )

    issue_title = issue_data.get('title', 'N/A')
    issue_identifier = issue_data.get('identifier', 'N/A')
    assignee_name = issue_data.get('assignee', {}).get('name', 'Unassigned')
    linear_issue_url = f"{LINEAR_BASE_URL}{issue_identifier}"

    if new_state_name == 'In Approval' and has_state_change:
        telegram_message = (
            f"งาน <b>{issue_title} ({issue_identifier})</b> ของ {assignee_name} ถูกย้ายไปที่สถานะ <b>In Approval</b> แล้วนะครับ ✨ \n\n"
            "📌 ฝากทีม Marketing ช่วยตรวจสอบด้วยนะครับ \n"
            "✅ ถ้างานผ่านแล้ว รบกวนย้ายไปที่ Done \n"
            f"📝 ถ้ายังไม่ผ่าน รบกวนคอมเมนต์บนงาน <b>{issue_identifier}</b> เพื่อให้ผู้รับงานนำไปปรับแก้ครับ"
        )
        telegram_message += project_text
        send_telegram_message(
            telegram_message,
            linear_issue_url,
            GOOGLE_SHEET_URL,
            GOOGLE_DRIVE_URL,
            include_inline_keyboard=True
        )
        print(f"Sent Telegram notification for 'In Approval' transition for {issue_identifier}.")
    else:
        if new_state_name == 'In Approval':
            print(f"Skipped 'In Approval' notify for {issue_identifier}: no actual state change detected.")

    if new_state_name == 'Done' and has_state_change:
        random_appreciation = random.choice(APPRECIATION_PHRASES)
        telegram_message = (
            f"🎉 งาน <b>{issue_title} ({issue_identifier})</b> ของ {assignee_name} ถูก <b>Approved</b> เป็นเรียบร้อยแล้ว!\n"
            f"{random_appreciation}"
        )
        telegram_message += project_text
        send_telegram_message(
            telegram_message,
            linear_issue_url,
            GOOGLE_SHEET_URL,
            GOOGLE_DRIVE_URL,
            include_inline_keyboard=False
        )
        print(f"Sent Telegram notification for 'Done' transition for {issue_identifier}.")
    else:
        if new_state_name == 'Done':
            print(f"Skipped 'Done' notify for {issue_identifier}: no actual state change detected.")

    return jsonify({"status": "success"}), 200

def send_telegram_message(message, linear_url, content_sheet_url, google_drive_url, include_inline_keyboard=True):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
    }
    if include_inline_keyboard:
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
        payload['reply_markup'] = inline_keyboard
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram message sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")
        if 'response' in locals():
            print(f"Telegram API Response content: {response.text}")
        else:
            print("No response object available.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))