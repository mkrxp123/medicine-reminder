from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ImageSendMessage, MessageEvent, TextMessage
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from flask import Flask, request, abort, render_template
from utility import getKey, timetable
import re

config = getKey()
reminder_db = timetable()

line_bot_api = LineBotApi(config["Channel access token"])
handler = WebhookHandler(config["Channel secret"])
app = Flask(__name__)


# 接收 LINE 的資訊
@app.route("/callback", methods=['POST'])
def callback():
	signature = request.headers['X-Line-Signature']

	body = request.get_data(as_text=True)
	app.logger.info("Request body: " + body)

	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		abort(400)

	return 'OK'


@app.route("/nav")
def nav():
	liff_id = config["Liff ID"]
	return render_template("nav.html", liff_id=liff_id)


# see https://xiaosean.github.io/chatbot/2018-04-19-LineChatbot_usage/
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	# get user id when reply
	user_id = event.source.user_id
	print("user_id =", user_id)
	msg = TextSendMessage(text=f'https://liff.line.me/{config["Liff ID"]}')
	line_bot_api.reply_message(event.reply_token, msg)
    
    
if __name__ == '__main__':
  	app.run(host='0.0.0.0', port=8080, debug=True)