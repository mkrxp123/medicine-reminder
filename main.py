from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ImageSendMessage, MessageEvent, TextMessage, TemplateSendMessage, ButtonsTemplate, PostbackAction, MessageTemplateAction, PostbackEvent
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from flask import Flask, request, abort, render_template, redirect, url_for, jsonify
from utility import getKey, ajaxResponse, timetable, Database, pushremindMsg
from rich_menu import rich_menu
import re
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import select, and_
from connection import *
import schedule
import time
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

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
    for d in data:
        print(d)
    return ajaxResponse(data)


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


# see https://xiaosean.github.io/chatbot/2018-04-19-LineChatbot_usage/
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # get user id when reply
    user_id = event.source.user_id
    print("user_id =", user_id)
    msg = TextSendMessage(text=f'https://liff.line.me/{config["Liff ID"]}')
    line_bot_api.reply_message(event.reply_token, msg)


@handler.add(PostbackEvent)
def handle_postback(event):  #吃藥提醒按鈕回傳值
    if event.postback.data == 'ateMedicine':
        msg = TextSendMessage(text="您已服用藥物!\n又是個健康的一天:D")
        line_bot_api.reply_message(event.reply_token, msg)


if __name__ == '__main__':
    postgres_manager = PostgresBaseManager()
    postgres_manager.runServerPostgresdb()
    remindList = postgres_manager.checkRemindTime()  #確認當前時間的提醒數量
    pushremindMsg()  #傳送吃藥提醒
    app.debug = True
    app.run(host='0.0.0.0', port=8080, use_reloader=False)
