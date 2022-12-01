from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ImageSendMessage, MessageEvent, TextMessage
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from flask import Flask, request, abort, render_template, redirect, url_for, jsonify
from utility import getKey, ajaxResponse, timetable, setup
from rich_menu import rich_menu
import re
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import select, and_

config = getKey()
# uncomment after you finish database connection
# reminder_db = timetable()

line_bot_api = LineBotApi(config["Channel access token"])
handler = WebhookHandler(config["Channel secret"])
app = Flask(__name__)
db, Users, RemindTimes, Reminders, RemindGroups = setup()


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
    print(form)

    # 看有幾個timepicker
    num = len(form.keys())
    num -= 3
    num -= 1
    # print("NUM: ", num)
    # insert data into database based on data given

    # insert UserID and UserName into Users
    select_statement = Users.select().where(Users.c.LineID == form['user_id'])
    check_exist = db.execute(select_statement).fetchall()
    if len(check_exist) == 0:
        insert_statement = Users.insert().values(LineID=form['user_id'],
                                                 UserName=form['user_id'])
        db.execute(insert_statement)

    # insert general info into Reminders
    insert_statement = Reminders.insert().values(Title='title_test6',
                                                 UserName='test6',
                                                 Picture=None,
                                                 Hospital='hospital_test6',
                                                 GroupID='Group_test6',
                                                 GetMedicine=True)
    db.execute(insert_statement)

    # # obtain attributes(mainly ReminderID) from the action above
    select_statement = Reminders.select().where(
        and_(Reminders.c.Title == 'title_test6',
             Reminders.c.UserName == 'test6'))
    result_set = db.execute(select_statement).fetchall()
    Current_Reminder = []
    for row in result_set:
        Current_Reminder.append(dict(row))

    # # insert into RemindTimes based on enddate, timpicker
    for x in range(num):
        insert_statement = RemindTimes.insert().values(
            ReminderID=Current_Reminder[0]['ReminderID'],
            RemindTime=form['timepicker' + str(x)],
            RemindDate=form['enddate'])
        db.execute(insert_statement)

    '''
    implement insert time table sql here
    form structure:
    {
        "user_id"    : "<string>"
        "begindate"  : "<string>",
        "enddate"    : "<string>",
        "timepicker0": "<string>",
        "timepicker1": "<string>",
        ...
    }
    '''

    return ajaxResponse({'msg': 'fill form successfully'})


@app.route("/search-routine", methods=["POST"])
def search_routine():
    '''
        tell html guys what to chage if you need extra input
        implement search routine function here
        then we will handle ajax things
    '''
    user_id = request.form["user_id"]
    
    return ajaxResponse({"foo": "bar"})


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
