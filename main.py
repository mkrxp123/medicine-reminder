from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ImageSendMessage
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from flask import Flask, request, abort
from utility import getKey, timetable

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


# see https://xiaosean.github.io/chatbot/2018-04-19-LineChatbot_usage/
# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     # get user id when reply
#     user_id = event.source.user_id
#     print("user_id =", user_id)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)