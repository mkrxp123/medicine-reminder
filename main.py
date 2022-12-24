from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ImageSendMessage, MessageEvent, TextMessage, TemplateSendMessage, ButtonsTemplate, PostbackAction, MessageTemplateAction, PostbackEvent, JoinEvent, FlexSendMessage
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from flask import Flask, request, abort, render_template, redirect, url_for, jsonify
from utility import getKey, ajaxResponse, timetable, Database, pushremindMsg, pushGetMedicineFlexMsg, pushTomorrowGetMedicineTextMsg, pushTodayGetMedicineTextMsg, pushOntimeTakeMedicine
from rich_menu import rich_menu
import re
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import select, and_
from connection import *
import schedule
import time
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import base64 as b64

config = getKey()
# uncomment after you finish database connection
# reminder_db = timetable()

line_bot_api = LineBotApi(config["Channel access token"])
handler = WebhookHandler(config["Channel secret"])
app = Flask(__name__)
database = Database()

sche = BackgroundScheduler(daemon=True)
sche.add_job(pushremindMsg, 'interval', minutes=5)
sche.start()


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


@app.route("/")
def home():
  '''
    redirect user to nav.html
    '''
  return redirect(url_for('nav'))


@app.route("/nav")
def nav():
  liff_id = config["Liff ID"]
  return render_template("nav.html", liff_id=liff_id)


@app.route("/fill-form", methods=["POST"])
def fill_form():
  form = request.json
  #print(form)
  '''
    implement insert time table sql here
    form structure:
    {
        "user_id"    : "<string>",
        'med'        : "<string>",
        'hospital'   : "<string>",
        'img'        : "not yet implemented",
        'title'      : "<string>",
        "begindate"  : "<string>",
        "enddate"    : "<string>",
        "timepickers": ["<string>", "<string>", ...]
    }
    '''

  database.InsertForm(form)
  return ajaxResponse({'msg': 'fill form successfully'})


@app.route("/search-img", methods=["GET"])
def search_img():
  reminder_id = int(request.args.get('ReminderID'))
  print(reminder_id)
  base64 = ''
  form = ''
  base64, form = database.GetRemindPicture(reminder_id)
  # print("base64: ", base64)
  print("Format: ", form)
  # pic = b64.b64decode(base64.encode("ascii"))
  '''
        Search images in the database by reminder_id
        Should return imgae data(base64) and format
    '''
  return f'<img src="data:image/{form};base64,{base64}">'
  # return ajaxResponse({'msg': reminder_id})


@app.route("/search-routine", methods=["POST"])
def search_routine():
  '''
        tell html guys what to chage if you need extra input
        implement search routine function here
        then we will handle ajax things
    '''
  # 拿特定User的Reminds
  user_id = request.json["user_id"]
  #print(f'user id: {user_id}')
  user_data = database.GetUserAllReminds(user_id)
  data = [{
    key: item if item is not None else ''
    for key, item in d.items()
    if key not in ["GroupID", "GroupName", "UserName", "LineID"]
  } for d in user_data]
  return ajaxResponse(data)


@app.route("/change-routine", methods=["POST"])
def change_routine():
  routine = request.json
  '''
        update routine
        the sturcture should be similar to the retrun value of function search_routine
        routine example (cuz I am lazy to write sturcture detail ;) )
        [ { "Checked": "", "GetMedicine": true, "Hospital": "hospital_test6", "PhoneNumber": "", "Picture": "", "RemindDate": "2022-11-30", "RemindTime": [ "16:04", "16:00", "14:00", "03:00", "17:00", "00:00", "00:59", "00:01", "00:02", "00:03", "21:45" ], "ReminderID": 5, "Title": "title_test6", "begindate": "2022-11-29", "enddate": "2022-12-30" } ]
    '''
  
  database.UpdateReminder(routine)

  return ajaxResponse({'msg': 'update routine successfully'})


@app.route("/remove-routine", methods=["POST"])
def remove_routine():
  reminder_id = request.json["ReminderID"]
  '''
        remove routine
    '''

  database.RemoveByReminderID(reminder_id)
  
  return ajaxResponse({'msg': 'remove routine successfully'})


@app.route("/user-init", methods=["POST"])
def user_init():
  user_info = request.json
  #print(user_info)
  '''
        check whether the user info is in the database,
        if not, insert the user info
        user_info structure:
        {
            "user_id"        : "<string>",
            'display_name'   : "<string>",
            'picture_url'    : "<string>",
            'status_msg'     : "<string>",
        }
    '''
  select_statement = database.Users.select().where(
    database.Users.c.LineID == user_info['user_id'])
  check_exist = database.db.execute(select_statement).fetchall()
  if len(check_exist) == 0:
    insert_statement = database.Users.insert().values(
      LineID=user_info['user_id'], UserName=user_info['display_name'])
    database.db.execute(insert_statement)

  return ajaxResponse({'msg': 'user init successfully'})


@handler.add(JoinEvent)
def handle_join(event):
  group_id = event.source.group_id
  msg = TextSendMessage(text='使用說明:\n若要填寫提醒請輸入【網址】\n查看使用說明請輸入【說明】\n修改客製化訊息請輸入【客製化訊息】')
  line_bot_api.push_message(group_id, msg)
  line_bot_api.push_message(
      group_id,
      FlexSendMessage(alt_text='請問您使用這個line bot的原因?',
                      contents={
                        "type": "bubble",
                        "body": {
                          "type":
                          "box",
                          "layout":
                          "vertical",
                          "contents": [{
                            "type": "text",
                            "text": "請問您使用這個line bot的原因?",
                            "weight": "bold",
                            "size": "md"
                          }]
                        },
                        "footer": {
                          "type":
                          "box",
                          "layout":
                          "vertical",
                          "spacing":
                          "sm",
                          "contents": [{
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                              "type": "message",
                              "label": "1.身體健康",
                              "text": "1.身體健康"
                            }
                          }, {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                              "type": "message",
                              "label": "2.怕家人擔心",
                              "text": "2.怕家人擔心"
                            }
                          }, {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                              "type": "message",
                              "label": "3.需要他人關心",
                              "text": "3.需要他人關心"
                            }
                          }],
                          "flex":
                          0
                        }
                      }))
  line_bot_api.push_message(
      group_id,
      FlexSendMessage(alt_text='請問您是否要使用手機號碼來進行提醒?',
                      contents={
                      "type": "bubble",
                      "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "text",
                            "text": "請問您是否要使用手機號碼來進行提醒?",
                            "weight": "bold",
                            "size": "md",
                            "flex": 0,
                            "margin": "none"
                          },
                          {
                            "type": "text",
                            "text": "(群組內的其他人可以打電話給您)",
                            "weight": "bold",
                            "size": "md",
                            "flex": 0,
                            "margin": "none"
                          }
                        ]
                      },
                      "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                          {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                              "type": "postback",
                              "label": "是",
                              "data": "phone_yes",
                              "wrap": "true",
                              "displayText": "我要使用手機號碼進行提醒"
                            }
                          },
                          {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                              "type": "postback",
                              "label": "否",
                              "data": "phone_no",
                              "wrap": "true",
                              "displayText": "我不需要使用手機號碼進行提醒"
                            }
                          },
                          {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [],
                            "margin": "sm"
                          }
                        ],
                        "flex": 0
                      }
                    }))
  
# see https://xiaosean.github.io/chatbot/2018-04-19-LineChatbot_usage/
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  # get user id when reply
  user_id = event.source.user_id
  print("user_id =", user_id)
  text = event.message.text
  if text == '網址':
    msg = TextSendMessage(text=f'https://liff.line.me/{config["Liff ID"]}')
    line_bot_api.reply_message(event.reply_token, msg)
  elif text == '說明':
    msg = TextSendMessage(text='使用說明:\n若要填寫提醒請輸入【網址】\n查看使用說明請輸入【說明】')
    line_bot_api.reply_message(event.reply_token, msg)
  elif text == "客製化訊息":
    line_bot_api.reply_message(
      event.reply_token,
      FlexSendMessage(alt_text='請問您使用這個line bot的原因?',
                     contents={
                        "type": "bubble",
                        "body": {
                          "type":
                          "box",
                          "layout":
                          "vertical",
                          "contents": [{
                            "type": "text",
                            "text": "請問您使用這個line bot的原因?",
                            "weight": "bold",
                            "size": "md"
                          }]
                        },
                        "footer": {
                          "type":
                          "box",
                          "layout":
                          "vertical",
                          "spacing":
                          "sm",
                          "contents": [{
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                              "type": "message",
                              "label": "1.身體健康",
                              "text": "1.身體健康"
                            }
                          }, {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                              "type": "message",
                              "label": "2.怕家人擔心",
                              "text": "2.怕家人擔心"
                            }
                          }, {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                              "type": "message",
                              "label": "3.需要他人關心",
                              "text": "3.需要他人關心"
                            }
                          }],
                          "flex":
                          0
                        }
                      }))  
  elif text == "1":
    postgres_manager = PostgresBaseManager()
    ontime_times = postgres_manager.getCheck(user_id)
    msg = '恭喜您~今天準時吃藥' + str(ontime_times) + '次\n'+'請繼續保持!'
    line_bot_api.reply_message(event.reply_token, msg)
  #更新資料庫Users的ReplyMsgType
  elif text == "1.身體健康":
    postgres_manager = PostgresBaseManager()
    postgres_manager.updateReplyMsgType(1, user_id)
  elif text == "2.怕家人擔心":
    postgres_manager = PostgresBaseManager()
    postgres_manager.updateReplyMsgType(2, user_id)
  elif text == "3.需要他人關心":
    postgres_manager = PostgresBaseManager()
    postgres_manager.updateReplyMsgType(3, user_id)
  else:
    postgres_manager = PostgresBaseManager()
    postgres_manager.updateReplyMsgType(0, user_id)

@handler.add(PostbackEvent)
def handle_postback(event):  #吃藥提醒按鈕回傳值
  if 'ateMedicine' in event.postback.data:
    reminder_id = int(event.postback.data[11:])
    postgres_manager = PostgresBaseManager()
    postgres_manager.updateRemindTimeChecked(True, reminder_id)
    msg = TextSendMessage(text="您已服用藥物!\n又是個健康的一天:D")
    line_bot_api.reply_message(event.reply_token, msg)
  elif 'phone_yes' in event.postback.data:
    postgres_manager = PostgresBaseManager()
    msg = TextSendMessage(text='請輸入您的手機號碼【Ex. 0987654321】')
    line_bot_api.reply_message(event.reply_token, msg)
    #postgres_manager.updatePhoneNumber(user_id, phoneNumber)
  elif 'phone_no' in event.postback.data:
    msg = TextSendMessage(text='好的，謝謝您的回覆!')
    line_bot_api.reply_message(event.reply_token, msg)

if __name__ == '__main__':
  postgres_manager = PostgresBaseManager()
  postgres_manager.runServerPostgresdb()
  pushremindMsg()  #傳送吃藥提醒
  pushTomorrowGetMedicineTextMsg()  #傳送明天的領藥提醒
  pushTodayGetMedicineTextMsg()  #傳送30分鐘前的領藥提醒
  pushGetMedicineFlexMsg()  #傳送領藥提醒check box
  #pushOntimeTakeMedicine() #傳送本日準時吃藥的次數
  app.debug = True
  app.run(host='0.0.0.0', port=8080, use_reloader=False)
