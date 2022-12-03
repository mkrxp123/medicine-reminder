from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ImageSendMessage, MessageEvent, TextMessage
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from flask import Flask, request, abort, render_template, redirect, url_for, jsonify
from utility import getKey, ajaxResponse, timetable, Database
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
database = Database()


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

    # 看有幾個timepicker
    num = len(form.keys())
    num -= 3
    num -= 1
    # print("NUM: ", num)
    # insert data into database based on data given

    # insert UserID and UserName into Users
    # select_statement = database.Users.select().where(database.Users.c.LineID == form['user_id'])
    # check_exist = database.db.execute(select_statement).fetchall()
    # if len(check_exist) == 0:
    #     insert_statement = database.Users.insert().values(LineID=form['user_id'],
    #                                              UserName='test6')
    #    database.db.execute(insert_statement)


    # insert to group
    #database.InsertGroup('this parameter has 33 characters.', 'finally done')

    # find username from lineID
    result_set = database.GetUserNamefromLineID('32')
    print(result_set)

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
