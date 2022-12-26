import json, sqlite3
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, String, MetaData, Integer, LargeBinary, VARCHAR, DateTime, Time, Date, Boolean

sqlite3.enable_callback_tracebacks(True)
from connection import *
from linebot import LineBotApi
from linebot.models import TextSendMessage, ImageSendMessage, MessageEvent, TextMessage, TemplateSendMessage, ButtonsTemplate, PostbackAction, MessageTemplateAction, PostbackEvent, FlexSendMessage
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta, datetime

group_id = "Cd77b64937d80d148c9e1f2ccbf947eee"

class Database:

    user = 'postgres'
    password = '12345678'
    host = 'database-1.cbixtilkjhc6.ap-northeast-1.rds.amazonaws.com'
    port = 5432
    dbname = 'HCI database'
    session = None

    def __init__(self):

        try:
            # GET THE CONNECTION OBJECT (ENGINE) FOR THE DATABASE
            self.db = create_engine(
                url="postgresql://{0}:{1}@{2}:{3}/{4}".format(
                    self.user, self.password, self.host, self.port,
                    self.dbname))
            print(
                f"Connection to the {self.host} for user {self.user} created successfully."
            )
            #setup schema of table
            self.meta = MetaData(self.db)
            self.Users = Table('Users', self.meta, Column('LineID', String),
                               Column('UserName', String),
                               Column('ReplyMsgType', Integer),
                               Column('PhoneNumber', String))
            self.RemindTimes = Table('RemindTimes', self.meta,
                                     Column('ReminderID', Integer),
                                     Column('RemindTime', Time),
                                     Column('RemindDate', Date),
                                     Column('Checked', Boolean),
                                     Column('RemindTimeID', Integer),
                                     Column('SendTimes', Integer))
            self.Reminders = Table('Reminders', self.meta,
                                   Column('Title', String),
                                   Column('ReminderID', Integer),
                                   Column('UserName', String),
                                   Column('Hospital', String),
                                   Column('GroupID', String),
                                   Column('GetMedicine', Boolean),
                                   Column('PhoneNumber', String),
                                   Column('Format', String),
                                   Column('Picture', String))
            self.RemindGroups = Table('RemindGroups', self.meta,
                                      Column('GroupID', String),
                                      Column('LineID', String))
            Session = sessionmaker(bind=self.db)
            self.session = Session()
            self.reminder_id = self.GetLargestReminderID() + 1

        except Exception as ex:
            print(
                "Connection could not be made due to the following error: \n",
                ex)

    def InsertGroup(self, id, name):
        insert_statement = self.RemindGroups.insert().values(GroupID=id,
                                                             GroupName=name)
        self.db.execute(insert_statement)

    def GetGroupNameFromGroupID(self, id):
        select_statement = self.RemindGroups.select().where(
            self.RemindGroups.c.GroupID == id)
        return self.db.execute(select_statement).fetchall()[0][1]

    def InsertUser(self, id, name):
        insert_statement = self.Users.insert().values(LineID=id, UserName=name)
        self.db.execute(insert_statement)

    def GetUserNamefromLineID(self, id):
        select_statement = self.Users.select().where(self.Users.c.LineID == id)
        temp = self.db.execute(select_statement).fetchall()
        return temp[0][1]

    def InsertReminder(self, title, rid, name, pic, hospital, gid, type,
                       formatt):
        insert_statement = self.Reminders.insert().values(Title=title,
                                                          ReminderID=rid,
                                                          UserName=name,
                                                          Picture=pic,
                                                          Hospital=hospital,
                                                          GroupID=gid,
                                                          GetMedicine=type,
                                                          Format=formatt)
        self.db.execute(insert_statement)

    def GetReminderFromReminderID(self, id):
        select_statement = self.Reminders.select().where(
            self.Reminders.c.ReminderID == id)
        return self.db.execute(select_statement).fetchall()[0]

    def InsertRemindTime(self, id, time, date):
        insert_statement = self.RemindTimes.insert().values(ReminderID=id,
                                                            RemindTime=time,
                                                            RemindDate=date)
        self.db.execute(insert_statement)

    def GetRemindTimesFromReminderID(self, id):
        select_statement = self.RemindTimes.select().where(
            self.RemindTimes.c.ReminderID == id)
        return self.db.execute(select_statement).fetchall()

    def GetLargestReminderID(self):
        return self.session.query(func.max(
            self.Reminders.c.ReminderID)).scalar()

    def InsertForm(self, form):
        # 統整參數
        get_med = True
        title = ''
        pic = ''
        formatt = ''
        begin_date_str = ''
        end_date_str = ''
        user_name = ''
        hospital = ''
        group_id = None
        phone_number = ''
        reminder_id = self.GetLargestReminderID() + 1

        # 取得給reminder的實際數值
        if form['med'] == 'take':
            get_med = False
        title = form['title']
        begin_date_str = form['begindate']
        end_date_str = form['enddate']
        user_name = self.GetUserNamefromLineID(form['user_id'])
        hospital = form['hospital']
        pic = form['img']
        formatt = form['format']

        # insert至reminder
        insert_statement = self.Reminders.insert().values(
            Title=title,
            ReminderID=reminder_id,
            UserName=user_name,
            Picture=pic,
            Hospital=hospital,
            GroupID=group_id,
            GetMedicine=get_med,
            #PhoneNumber=phone_number,
            Format=formatt)
        self.db.execute(insert_statement)

        # 取得給remindTime的數值
        ## date的部分
        begin_date_list = [int(num) for num in begin_date_str.split('-')]
        begin_date = date(begin_date_list[0], begin_date_list[1],
                          begin_date_list[2])
        end_date_list = [int(num) for num in end_date_str.split('-')]
        end_date = date(end_date_list[0], end_date_list[1], end_date_list[2])
        delta = end_date - begin_date

        ## time的部分
        time_list = form['timepickers']

        ## 依序insert
        for i in range(delta.days + 1):
            day = begin_date + timedelta(days=i)
            for current_time in time_list:
                insert_statement = self.RemindTimes.insert().values(
                    ReminderID=reminder_id,
                    RemindTime=current_time,
                    RemindDate=day)
                self.db.execute(insert_statement)

    # 查詢今日所有的提醒的全部資料並存入一個list of dictionary 大概長這樣[{}, {}, {}]
    def GetTodayReminds(self):
        today = datetime.today().strftime('%Y-%m-%d')
        select_statement = '''select * from (select * from "RemindTimes" where "RemindDate" = '{0}'::date) as RemindTime natural join "Reminders" natural join "Users"'''.format(
            today)
        result = self.db.execute(select_statement).fetchall()
        Today_Reminds = []
        for row in result:
            Today_Reminds.append(dict(row))
        return Today_Reminds

    # 查詢特定使用者的全部資料
    def GetUserAllReminds(self, user_id):
        select_statement = '''select * from (select * from "Users" where "LineID" = '{0}') as users natural join "Reminders" natural join "RemindTimes"'''.format(
            user_id)
        result = self.db.execute(select_statement).fetchall()
        user_data = []
        dates = []
        for row in result:
            user_data.append(dict(row))
        select_statement = '''with date_calc as (select "ReminderID", min("RemindDate") as begindate, max("RemindDate") as enddate from "RemindTimes" Group by "ReminderID" order by "ReminderID" asc) select distinct "ReminderID", begindate, enddate from (select * from "Users" where "LineID" = '{0}') as users natural join "Reminders" natural join "RemindTimes" natural join "date_calc"'''.format(
            user_id)
        result = self.db.execute(select_statement).fetchall()
        for row in result:
            dates.append(dict(row))
        final = []
        for dic in user_data:
            dic["RemindDate"] = dic["RemindDate"].strftime("%Y-%m-%d")
            dic["RemindTime"] = dic["RemindTime"].strftime("%H:%M")
        for dic in dates:
            dic["begindate"] = dic["begindate"].strftime("%Y-%m-%d")
            dic["enddate"] = dic["enddate"].strftime("%Y-%m-%d")
        for IDs in dates:
            temp = []
            for times in user_data:
                if IDs["ReminderID"] == times["ReminderID"]:
                    temp.append(dict(times))
            final.append(dict(temp[0]))
        for records in final:
            for datas in dates:
                if records["ReminderID"] == datas["ReminderID"]:
                    records.update({'begindate': datas["begindate"]})
                    records.update({'enddate': datas["enddate"]})
                    records["RemindTime"] = []
            for datas in user_data:
                if records["ReminderID"] == datas["ReminderID"] and datas[
                        "RemindTime"] not in records["RemindTime"]:
                    records["RemindTime"].append(datas["RemindTime"])
        return final

    #查詢特定ReminderID的圖片
    def GetRemindPicture(self, ID):
        select_statement = '''select "Picture", "Format" from "Reminders" where "ReminderID" = {0}'''.format(
            ID)
        pictures = []
        base64 = ''
        form = ''
        result = self.db.execute(select_statement).fetchall()
        for row in result:
            pictures.append(dict(row))
        base64 = pictures[0]["Picture"]
        form = pictures[0]["Format"]
        return base64, form

    def RemoveByReminderID(self, id):
        self.session.query(
            self.Reminders).filter(self.Reminders.c.ReminderID == id).delete()
        self.session.commit()
        self.session.query(self.RemindTimes).filter(
            self.RemindTimes.c.ReminderID == id).delete()
        self.session.commit()

    def UpdateReminder(self, form):
        origin_remind_id = form['ReminderID']
        if form['GetMedicine']:
            hospital = form['Hospital']
            title = form['Title']
            begin_date_str = form['begindate']
            end_date_str = form['enddate']
            time_list = form['RemindTime']
            self.session.query(self.Reminders).filter(
                self.Reminders.c.ReminderID == origin_remind_id).update({
                    'Title':
                    title,
                    'Hospital':
                    hospital
                })
            self.session.commit()
        else:
            title = form['Title']
            begin_date_str = form['begindate']
            end_date_str = form['enddate']
            time_list = form['RemindTime']
            self.session.query(self.Reminders).filter(
                self.Reminders.c.ReminderID == origin_remind_id).update(
                    {'Title': title})
            self.session.commit()

        self.session.query(self.RemindTimes).filter(
            self.RemindTimes.c.ReminderID == origin_remind_id).delete()
        self.session.commit()

        begin_date_list = [int(num) for num in begin_date_str.split('-')]
        begin_date = date(begin_date_list[0], begin_date_list[1],
                          begin_date_list[2])
        end_date_list = [int(num) for num in end_date_str.split('-')]
        end_date = date(end_date_list[0], end_date_list[1], end_date_list[2])
        delta = end_date - begin_date

        ## 依序insert
        for i in range(delta.days + 1):
            day = begin_date + timedelta(days=i)
            for current_time in time_list:
                insert_statement = self.RemindTimes.insert().values(
                    ReminderID=origin_remind_id,
                    RemindTime=current_time,
                    RemindDate=day)
                self.db.execute(insert_statement)


def getKey():
    with open("setting/key.json", 'r') as f:
        config = json.load(f)
    return config


def ajaxResponse(dict):
    response = jsonify(dict)
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.status_code = 200
    return response


class timetable:

    def __init__(self):
        self.db = sqlite3.connect("./database/timetable.db")
        self.db.row_factory = sqlite3.Row
        with open('./database/schema.sql', 'r') as f:
            self.db.cursor().executescript(f.read())
        self.db.cursor().execute("PRAGMA foreign_keys=ON")
        self.db.commit()


def pushremindMsg():
    config = getKey()
    line_bot_api = LineBotApi(config["Channel access token"])
    postgres_manager = PostgresBaseManager()
    remindList = postgres_manager.checkRemindTime()
    # send remind message
    print(len(remindList))
    if len(remindList):
        while (len(remindList)):
            #msg = postgres_manager.getPostgresdbData()
            reminderID = remindList[0][0]
            reminderTitle = remindList[0][1]
            remindLineID = group_id
            #remindLineID = remindList[0][2]  #要傳送提醒的使用者Line ID
            remindTimeID = remindList[0][3]
            #客製化訊息
            type_number = postgres_manager.getReplyMsgType(remindLineID)
            msg = replyMsg(type_number)
            #print("msg:", msg)
            url = "https://medicine-reminder.r890910.repl.co/search-img?ReminderID=" + reminderID
            print(url)

            buttons_template = ButtonsTemplate(
                title=reminderTitle,
                thumbnail_image_url=url,
                text=msg,
                actions=[
                    PostbackAction(label='確認',
                                   data='ateMedicine' + str(remindTimeID),
                                   display_text='已吃藥!')
                ])
            template_message = TemplateSendMessage(alt_text='吃藥提醒',
                                                   template=buttons_template)
            
            #line_bot_api.push_message(remindLineID, ImageSendMessage(original_content_url = url, preview_image_url = url))
            line_bot_api.push_message(remindLineID, template_message)
            remindList.pop(0)
    return True


#push明天的領藥提醒
def pushTomorrowGetMedicineTextMsg():
    config = getKey()
    line_bot_api = LineBotApi(config["Channel access token"])
    postgres_manager = PostgresBaseManager()
    List = postgres_manager.getTomorrowList()

    if len(List):
        for r in List:
            reLineID = group_id
            #reLineID = r[5]
            #msg = '明日請記得領藥!\n' + '提醒領藥者 : ' + str(
            #r[0]) + '\n' + '領取藥品名稱 : ' + str(
            #r[2]) + '\n' + '領取時間 : ' + str(r[3]) + ' ' + str(
            #r[4]) + '\n' + '領取地點 : ' + str(r[6]) + '\n' + '祝您身體健康!'
            #line_bot_api.push_message(reLineID, TextSendMessage(text=msg))
            line_bot_api.push_message(
                reLineID,
                FlexSendMessage(alt_text='明日請記得領藥!',
                                contents={
                                    "type": "bubble",
                                    "body": {
                                        "type":
                                        "box",
                                        "layout":
                                        "vertical",
                                        "contents": [{
                                            "type":
                                            "text",
                                            "text":
                                            "明日(" + str(r[3]) + ")領藥提醒!",
                                            "weight":
                                            "bold",
                                            "size":
                                            "md"
                                        }, {
                                            "type":
                                            "box",
                                            "layout":
                                            "vertical",
                                            "margin":
                                            "lg",
                                            "spacing":
                                            "sm",
                                            "contents": [{
                                                "type":
                                                "box",
                                                "layout":
                                                "baseline",
                                                "spacing":
                                                "sm",
                                                "contents": [{
                                                    "type": "text",
                                                    "text": "提醒領藥者 : ",
                                                    "color": "#aaaaaa",
                                                    "size": "sm",
                                                    "flex": 0
                                                }, {
                                                    "type": "text",
                                                    "text": str(r[0]),
                                                    "color": "#666666",
                                                    "size": "sm",
                                                    "flex": 2
                                                }]
                                            }, {
                                                "type":
                                                "box",
                                                "layout":
                                                "baseline",
                                                "spacing":
                                                "sm",
                                                "contents": [{
                                                    "type": "text",
                                                    "text": "領取藥品名稱 :",
                                                    "color": "#aaaaaa",
                                                    "size": "sm",
                                                    "flex": 0
                                                }, {
                                                    "type": "text",
                                                    "text": str(r[2]),
                                                    "color": "#666666",
                                                    "size": "sm",
                                                    "flex": 5
                                                }]
                                            }, {
                                                "type":
                                                "box",
                                                "layout":
                                                "baseline",
                                                "spacing":
                                                "sm",
                                                "contents": [{
                                                    "type": "text",
                                                    "text": "領取時間 :",
                                                    "color": "#aaaaaa",
                                                    "size": "sm",
                                                    "flex": 0
                                                }, {
                                                    "type":
                                                    "text",
                                                    "text":
                                                    str(r[3]) + " " +
                                                    str(r[4]),
                                                    "color":
                                                    "#666666",
                                                    "size":
                                                    "sm",
                                                    "flex":
                                                    5
                                                }]
                                            }, {
                                                "type":
                                                "box",
                                                "layout":
                                                "baseline",
                                                "spacing":
                                                "sm",
                                                "contents": [{
                                                    "type": "text",
                                                    "text": "領取地點 : ",
                                                    "color": "#aaaaaa",
                                                    "size": "sm",
                                                    "flex": 0
                                                }, {
                                                    "type": "text",
                                                    "text": str(r[6]),
                                                    "color": "#666666",
                                                    "size": "sm",
                                                    "flex": 5
                                                }]
                                            }, {
                                                "type": "text",
                                                "text": "祝您身體健康!"
                                            }]
                                        }]
                                    }
                                }))

    return True


#push今天的領藥提醒
def pushTodayGetMedicineTextMsg():
    config = getKey()
    line_bot_api = LineBotApi(config["Channel access token"])
    postgres_manager = PostgresBaseManager()
    List = postgres_manager.getTodayList()

    if len(List):
        for r in List:
            #取得日期
            dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
            dt2 = dt1.astimezone(timezone(timedelta(hours=8)))  # 轉換時區 -> 東八區
            #輸出比現在時間早半小時
            remindTime = (dt2 +
                          timedelta(minutes=-30)).strftime("%Y-%m-%d %H:%M:00")
            #print("remind time : ", remindTime)
            #reLineID = r[5]
            reLineID = group_id

            if str(r[3]) + " " + str(r[4]) == str(remindTime):
                #msg = '請記得於30分鐘後至診所/醫院領藥!\n' + '提醒領藥者 : ' + str(
                #r[0]) + '\n' + '領取藥品名稱 : ' + str(
                #r[2]) + '\n' + '領取時間 : ' + str(r[3]) + ' ' + str(
                #r[4]) + '\n' + '領取地點 : ' + str(
                #r[6]) + '\n' + '祝您身體健康!'
                #line_bot_api.push_message(reLineID, TextSendMessage(text=msg))
                line_bot_api.push_message(
                    reLineID,
                    FlexSendMessage(alt_text='請記得於30分鐘後至診所/醫院領藥!',
                                    contents={
                                        "type": "bubble",
                                        "body": {
                                            "type":
                                            "box",
                                            "layout":
                                            "vertical",
                                            "contents": [{
                                                "type": "text",
                                                "text": "請記得於30分鐘後至診所/醫院領藥!",
                                                "weight": "bold",
                                                "size": "md"
                                            }, {
                                                "type":
                                                "box",
                                                "layout":
                                                "vertical",
                                                "margin":
                                                "lg",
                                                "spacing":
                                                "sm",
                                                "contents": [{
                                                    "type":
                                                    "box",
                                                    "layout":
                                                    "baseline",
                                                    "spacing":
                                                    "sm",
                                                    "contents": [{
                                                        "type": "text",
                                                        "text": "提醒領藥者 : ",
                                                        "color": "#aaaaaa",
                                                        "size": "sm",
                                                        "flex": 0
                                                    }, {
                                                        "type":
                                                        "text",
                                                        "text":
                                                        str(r[0]),
                                                        "color":
                                                        "#666666",
                                                        "size":
                                                        "sm",
                                                        "flex":
                                                        2
                                                    }]
                                                }, {
                                                    "type":
                                                    "box",
                                                    "layout":
                                                    "baseline",
                                                    "spacing":
                                                    "sm",
                                                    "contents": [{
                                                        "type": "text",
                                                        "text": "領取藥品名稱 :",
                                                        "color": "#aaaaaa",
                                                        "size": "sm",
                                                        "flex": 0
                                                    }, {
                                                        "type":
                                                        "text",
                                                        "text":
                                                        str(r[2]),
                                                        "color":
                                                        "#666666",
                                                        "size":
                                                        "sm",
                                                        "flex":
                                                        5
                                                    }]
                                                }, {
                                                    "type":
                                                    "box",
                                                    "layout":
                                                    "baseline",
                                                    "spacing":
                                                    "sm",
                                                    "contents": [{
                                                        "type": "text",
                                                        "text": "領取時間 :",
                                                        "color": "#aaaaaa",
                                                        "size": "sm",
                                                        "flex": 0
                                                    }, {
                                                        "type":
                                                        "text",
                                                        "text":
                                                        str(r[3]) + " " +
                                                        str(r[4]),
                                                        "color":
                                                        "#666666",
                                                        "size":
                                                        "sm",
                                                        "flex":
                                                        5
                                                    }]
                                                }, {
                                                    "type":
                                                    "box",
                                                    "layout":
                                                    "baseline",
                                                    "spacing":
                                                    "sm",
                                                    "contents": [{
                                                        "type": "text",
                                                        "text": "領取地點 : ",
                                                        "color": "#aaaaaa",
                                                        "size": "sm",
                                                        "flex": 0
                                                    }, {
                                                        "type":
                                                        "text",
                                                        "text":
                                                        str(r[6]),
                                                        "color":
                                                        "#666666",
                                                        "size":
                                                        "sm",
                                                        "flex":
                                                        5
                                                    }]
                                                }, {
                                                    "type": "text",
                                                    "text": "祝您身體健康!"
                                                }]
                                            }]
                                        }
                                    }))

    return True


#push今天領要提醒的check box
def pushGetMedicineFlexMsg():
    config = getKey()
    line_bot_api = LineBotApi(config["Channel access token"])
    postgres_manager = PostgresBaseManager()
    List = postgres_manager.getTodayList()
    # send remind message
    #print("List length: ", len(List))
    #for r in List:
    #print(str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]))

    if len(List):
        for r in List:
            #取得日期
            dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
            dt2 = dt1.astimezone(timezone(timedelta(hours=8)))  # 轉換時區 -> 東八區
            now = dt2.strftime("%Y-%m-%d %H:%M:00")
            #print("now : ", now)

            reLineID = group_id
            #reLineID = r[5]  #要傳送提醒的使用者Line ID
            #客製化訊息
            #type_number = postgres_manager.getReplyMsgType(reLineID)
            #msg = replyMsg(type_number)
            #print("msg:", msg)
            #'記得至診所/醫院領取藥品~'
            if str(r[3]) + " " + str(r[4]) == str(now):
                line_bot_api.push_message(
                    reLineID,
                    FlexSendMessage(alt_text='記得至診所/醫院領取藥品~',
                                    contents={
                                        "type": "bubble",
                                        "body": {
                                            "type":
                                            "box",
                                            "layout":
                                            "vertical",
                                            "contents": [{
                                                "type": "text",
                                                "text": "今日領藥提醒",
                                                "weight": "bold",
                                                "size": "xl"
                                            }, {
                                                "type":
                                                "box",
                                                "layout":
                                                "vertical",
                                                "margin":
                                                "lg",
                                                "spacing":
                                                "sm",
                                                "contents": [{
                                                    "type":
                                                    "box",
                                                    "layout":
                                                    "baseline",
                                                    "spacing":
                                                    "sm",
                                                    "contents": [{
                                                        "type": "text",
                                                        "text": "提醒領藥者 : ",
                                                        "color": "#aaaaaa",
                                                        "size": "sm",
                                                        "flex": 0
                                                    }, {
                                                        "type":
                                                        "text",
                                                        "text":
                                                        str(r[0]),
                                                        "color":
                                                        "#666666",
                                                        "size":
                                                        "sm",
                                                        "flex":
                                                        2
                                                    }]
                                                }, {
                                                    "type":
                                                    "box",
                                                    "layout":
                                                    "baseline",
                                                    "spacing":
                                                    "sm",
                                                    "contents": [{
                                                        "type": "text",
                                                        "text": "領取藥品名稱 :",
                                                        "color": "#aaaaaa",
                                                        "size": "sm",
                                                        "flex": 0
                                                    }, {
                                                        "type":
                                                        "text",
                                                        "text":
                                                        str(r[2]),
                                                        "color":
                                                        "#666666",
                                                        "size":
                                                        "sm",
                                                        "flex":
                                                        5
                                                    }]
                                                }, {
                                                    "type":
                                                    "box",
                                                    "layout":
                                                    "baseline",
                                                    "spacing":
                                                    "sm",
                                                    "contents": [{
                                                        "type": "text",
                                                        "text": "領取時間 :",
                                                        "color": "#aaaaaa",
                                                        "size": "sm",
                                                        "flex": 0
                                                    }, {
                                                        "type":
                                                        "text",
                                                        "text":
                                                        str(r[3]) + " " +
                                                        str(r[4]),
                                                        "color":
                                                        "#666666",
                                                        "size":
                                                        "sm",
                                                        "flex":
                                                        5
                                                    }]
                                                }, {
                                                    "type":
                                                    "box",
                                                    "layout":
                                                    "baseline",
                                                    "spacing":
                                                    "sm",
                                                    "contents": [{
                                                        "type": "text",
                                                        "text": "領取地點 : ",
                                                        "color": "#aaaaaa",
                                                        "size": "sm",
                                                        "flex": 0
                                                    }, {
                                                        "type":
                                                        "text",
                                                        "text":
                                                        str(r[6]),
                                                        "color":
                                                        "#666666",
                                                        "size":
                                                        "sm",
                                                        "flex":
                                                        5
                                                    }]
                                                }, {
                                                    "type": "text",
                                                    "text": "祝您身體健康!"
                                                }]
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
                                                    "label": "已領取!",
                                                    "text": "已領取" + str(r[2])
                                                }
                                            }],
                                            "flex":
                                            0
                                        }
                                    }))
    return True


#push本日準時吃幾次藥
def pushOntimeTakeMedicine():
    config = getKey()
    line_bot_api = LineBotApi(config["Channel access token"])
    postgres_manager = PostgresBaseManager()
    List = postgres_manager.getLineID()

    if len(List):
        for r in List:
            reLineID = group_id
            #reLineID = r[0]
            #print("LineID: ", reLineID)
            ontime_times = postgres_manager.getCheck(reLineID)
            msg = '恭喜您~今天準時吃藥' + str(ontime_times) + '次\n' + '請繼續保持!'
            #print("msg: ", msg)
            if ontime_times > 0:
                line_bot_api.push_message(reLineID, TextSendMessage(text=msg))
            #else:
            #msg = '恭喜您~今天準時吃藥0次\n'+'請繼續保持!'
            #line_bot_api.push_message(reLineID, TextSendMessage(text=msg))
    return True


#依照type_number找相對應的reply message
def replyMsg(type_number):
    reply_str = ""
    if type_number == 1:
        reply_str = "您好~為了身體健康，請記得準時吃藥!"
    elif type_number == 2:
        reply_str = "您好~為了不讓家人擔心，請記得準時吃藥!"
    elif type_number == 3:
        reply_str = "欸!吃藥了沒?記得準時吃藥!!!!!!!"
    else:
        reply_str = "請準時吃藥ㄚㄚㄚㄚㄚㄚ"
    return reply_str
