from linebot import LineBotApi
from linebot.models import TextSendMessage, ImageSendMessage
from linebot.exceptions import LineBotApiError
from utility import *

reminder_db = timetable()

# see https://xiaosean.github.io/chatbot/2018-04-19-LineChatbot_usage/
# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     # get user id when reply
#     user_id = event.source.user_id
#     print("user_id =", user_id)