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

group_id = "C0814d7a66ea58a4af68f5111e809224f"

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
        # ????????????
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

        # ?????????reminder???????????????
        if form['med'] == 'take':
            get_med = False
        title = form['title']
        begin_date_str = form['begindate']
        end_date_str = form['enddate']
        user_name = self.GetUserNamefromLineID(form['user_id'])
        hospital = form['hospital']
        pic = form['img']
        formatt = form['format']

        # insert???reminder
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

        # ?????????remindTime?????????
        ## date?????????
        begin_date_list = [int(num) for num in begin_date_str.split('-')]
        begin_date = date(begin_date_list[0], begin_date_list[1],
                          begin_date_list[2])
        end_date_list = [int(num) for num in end_date_str.split('-')]
        end_date = date(end_date_list[0], end_date_list[1], end_date_list[2])
        delta = end_date - begin_date

        ## time?????????
        time_list = form['timepickers']

        ## ??????insert
        for i in range(delta.days + 1):
            day = begin_date + timedelta(days=i)
            for current_time in time_list:
                insert_statement = self.RemindTimes.insert().values(
                    ReminderID=reminder_id,
                    RemindTime=current_time,
                    RemindDate=day)
                self.db.execute(insert_statement)

    # ?????????????????????????????????????????????????????????list of dictionary ???????????????[{}, {}, {}]
    def GetTodayReminds(self):
        today = datetime.today().strftime('%Y-%m-%d')
        select_statement = '''select * from (select * from "RemindTimes" where "RemindDate" = '{0}'::date) as RemindTime natural join "Reminders" natural join "Users"'''.format(
            today)
        result = self.db.execute(select_statement).fetchall()
        Today_Reminds = []
        for row in result:
            Today_Reminds.append(dict(row))
        return Today_Reminds

    # ????????????????????????????????????
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

    #????????????ReminderID?????????
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

        ## ??????insert
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
    print("remindList length:"+str(len(remindList)))
    if len(remindList):
        while (len(remindList)):
            #msg = postgres_manager.getPostgresdbData()
            reminderID = remindList[0][0]
            reminderDate = remindList[0][1]
            reminderTime = remindList[0][2]
            reminderTitle = remindList[0][3]
            remindLineID = group_id
            #remindLineID = remindList[0][4]  #???????????????????????????Line ID
            remindTimeID = remindList[0][5]
            userName = remindList[0][6]
            phoneNumber = remindList[0][8]
            phoneNumber_url = "tel:+886-" + phoneNumber[1:]
            print(phoneNumber_url)
            #???????????????
            type_number = postgres_manager.getReplyMsgType(remindLineID)
            reply_msg = replyMsg(type_number)
            #print("msg:", msg)
            url = "https://medicine-reminder.r890910.repl.co/search-img?ReminderID=" + reminderID
            print(url)

            #??????sentTimes
            current_sendTimes = remindList[0][7]
            remindtimeID = remindTimeID

            if current_sendTimes == 0:
              line_bot_api.push_message(
                      remindLineID,
                      FlexSendMessage(alt_text='????????????!',
                                      contents={
                                          "type": "bubble",
                                          "hero": {
                                                  "type": "image",
                                                  "url": url,
                                                  "size": "full",
                                                  "aspectRatio": "20:13",
                                                  "aspectMode": "cover",
                                                  "action": {
                                                    "type": "uri",
                                                    "uri": url
                                                  }
                                              },
                                          "body": {
                                              "type":
                                              "box",
                                              "layout":
                                              "vertical",
                                              "contents": [{
                                                  "type": "text",
                                                  "text": str(userName)+"???????????????",
                                                  "weight": "bold",
                                                  "size": "xl",
                                                  "wrap": True
                                              },
                                          
                                              {
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
                                                      
                                                  }, {
                                                      "type":
                                                      "box",
                                                      "layout":
                                                      "baseline",
                                                      "spacing":
                                                      "sm",
                                                      "contents": [{
                                                          "type": "text",
                                                          "text": "???????????? :",
                                                          "color": "#aaaaaa",
                                                          "size": "sm",
                                                          "flex": 0
                                                      }, {
                                                          "type":
                                                          "text",
                                                          "text":
                                                          str(reminderTitle),
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
                                                          "text": "???????????? :",
                                                          "color": "#aaaaaa",
                                                          "size": "sm",
                                                          "flex": 0
                                                      }, {
                                                          "type":
                                                          "text",
                                                          "text":
                                                          str(reminderDate) + " " +
                                                          str(reminderTime),
                                                          "color":
                                                          "#666666",
                                                          "size":
                                                          "sm",
                                                          "flex":
                                                          5
                                                      }]
                                                  }, {
                                                      "type": "text",
                                                      "margin": "md",
                                                      "text": reply_msg
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
                                                  "action": {
                                                    "type": "postback",
                                                    "label": "?????????",
                                                    "data": "ateMedicine"+ str(remindTimeID),
                                                    "displayText": "?????????!"
                                                  }
                                                }],
                                              "flex":
                                              0
                                          }
                                      }))
              print("current times", current_sendTimes)
              postgres_manager = PostgresBaseManager()
              postgres_manager.updateSendTimes(current_sendTimes, remindtimeID)
            remindList.pop(0)

    remindTwiceList = postgres_manager.getRemindTwiceList()
    print("remindTwiceList length:"+str(len(remindTwiceList)))
    if len(remindTwiceList):
        while (len(remindTwiceList)):
            #msg = postgres_manager.getPostgresdbData()
            reminderID = remindTwiceList[0][0]
            reminderDate = remindTwiceList[0][1]
            reminderTime = remindTwiceList[0][2]
            reminderTitle = remindTwiceList[0][3]
            remindLineID = group_id
            #remindLineID = remindList[0][4]  #???????????????????????????Line ID
            remindTimeID = remindTwiceList[0][5]
            userName = remindTwiceList[0][6]
            phoneNumber = remindTwiceList[0][8]
            phoneNumber_url = "tel:+886-" + phoneNumber[1:]
            print(phoneNumber_url)
            #???????????????
            type_number = postgres_manager.getReplyMsgType(remindLineID)
            reply_msg = replyMsg(type_number)
            #print("msg:", msg)
            url = "https://medicine-reminder.r890910.repl.co/search-img?ReminderID=" + reminderID
            print(url)

            #??????sentTimes
            current_sendTimes = remindTwiceList[0][7]
            remindtimeID = remindTimeID
           
            if current_sendTimes == 1 and len(phoneNumber)>=10:
              line_bot_api.push_message(
                      remindLineID,
                      FlexSendMessage(alt_text='????????????!',
                                      contents={
                                          "type": "bubble",
                                          "hero": {
                                                  "type": "image",
                                                  "url": url,
                                                  "size": "full",
                                                  "aspectRatio": "20:13",
                                                  "aspectMode": "cover",
                                                  "action": {
                                                    "type": "uri",
                                                    "uri": url
                                                  }
                                              },
                                          "body": {
                                              "type":
                                              "box",
                                              "layout":
                                              "vertical",
                                              "contents": [{
                                                  "type": "text",
                                                  "text": str(userName) + "???????????????",
                                                  "weight": "bold",
                                                  "size": "xl",
                                                  "wrap": True
                                              },
                                          
                                              {
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
                                                      
                                                  }, {
                                                      "type":
                                                      "box",
                                                      "layout":
                                                      "baseline",
                                                      "spacing":
                                                      "sm",
                                                      "contents": [{
                                                          "type": "text",
                                                          "text": "???????????? :",
                                                          "color": "#aaaaaa",
                                                          "size": "sm",
                                                          "flex": 0
                                                      }, {
                                                          "type":
                                                          "text",
                                                          "text":
                                                          str(reminderTitle),
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
                                                          "text": "???????????? :",
                                                          "color": "#aaaaaa",
                                                          "size": "sm",
                                                          "flex": 0
                                                      }, {
                                                          "type":
                                                          "text",
                                                          "text":
                                                          str(reminderDate) + " " +
                                                          str(reminderTime),
                                                          "color":
                                                          "#666666",
                                                          "size":
                                                          "sm",
                                                          "flex":
                                                          5
                                                      }]
                                                  }, {
                                                      "type": "text",
                                                      "margin": "md",
                                                      "text": str(userName)+"????????????????????????",
                                                      "wrap": True,
                                                      "weight": "bold",
                                                      "margin": "xl"
                                                  },
                                                  {
                                                      "type": "text",
                                                      "margin": "md",
                                                      "text": "????????????????????????????????????????????????!",
                                                      "wrap": True,
                                                      "weight": "bold",
                                                      "margin": "sm"
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
                                              "contents": [
                                                {
                                                  "type": "button",
                                                  "style": "link",
                                                  "height": "sm",
                                                  "action": {
                                                    "type": "uri",
                                                    "label": "????????????"+str(userName),
                                                    "uri": phoneNumber_url
                                                  }
                                                },
                                                {
                                                  "type": "button",
                                                  "action": {
                                                    "type": "postback",
                                                    "label": "?????????",
                                                    "data": "ateMedicine"+ str(remindTimeID),
                                                    "displayText": "?????????!"
                                                  }
                                                }],
                                              "flex":
                                              0
                                          }
                                      }))
              print("current times", current_sendTimes)
              postgres_manager = PostgresBaseManager()
              postgres_manager.updateSendTimes(current_sendTimes, remindtimeID)
            elif current_sendTimes == 1 and len(phoneNumber)<10:
              line_bot_api.push_message(
                      remindLineID,
                      FlexSendMessage(alt_text='????????????!',
                                      contents={
                                          "type": "bubble",
                                          "hero": {
                                                  "type": "image",
                                                  "url": url,
                                                  "size": "full",
                                                  "aspectRatio": "20:13",
                                                  "aspectMode": "cover",
                                                  "action": {
                                                    "type": "uri",
                                                    "uri": url
                                                  }
                                              },
                                          "body": {
                                              "type":
                                              "box",
                                              "layout":
                                              "vertical",
                                              "contents": [{
                                                  "type": "text",
                                                  "text": str(userName) + "???????????????",
                                                  "weight": "bold",
                                                  "size": "xl",
                                                  "wrap": True
                                              },
                                          
                                              {
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
                                                      
                                                  }, {
                                                      "type":
                                                      "box",
                                                      "layout":
                                                      "baseline",
                                                      "spacing":
                                                      "sm",
                                                      "contents": [{
                                                          "type": "text",
                                                          "text": "???????????? :",
                                                          "color": "#aaaaaa",
                                                          "size": "sm",
                                                          "flex": 0
                                                      }, {
                                                          "type":
                                                          "text",
                                                          "text":
                                                          str(reminderTitle),
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
                                                          "text": "???????????? :",
                                                          "color": "#aaaaaa",
                                                          "size": "sm",
                                                          "flex": 0
                                                      }, {
                                                          "type":
                                                          "text",
                                                          "text":
                                                          str(reminderDate) + " " +
                                                          str(reminderTime),
                                                          "color":
                                                          "#666666",
                                                          "size":
                                                          "sm",
                                                          "flex":
                                                          5
                                                      }]
                                                  }, {
                                                      "type": "text",
                                                      "margin": "md",
                                                      "text": str(userName)+"???????????????????????????????????????!",
                                                      "wrap": True,
                                                      "weight": "bold",
                                                      "margin": "xl"
                                                  },
                                                  ]
                                              }]
                                          },
                                          "footer": {
                                              "type":
                                              "box",
                                              "layout":
                                              "vertical",
                                              "spacing":
                                              "sm",
                                              "contents": [
                                                {
                                                  "type": "button",
                                                  "action": {
                                                    "type": "postback",
                                                    "label": "?????????",
                                                    "data": "ateMedicine"+ str(remindTimeID),
                                                    "displayText": "?????????!"
                                                  }
                                                }],
                                              "flex":
                                              0
                                          }
                                      }))
              print("current times", current_sendTimes)
              postgres_manager = PostgresBaseManager()
              postgres_manager.updateSendTimes(current_sendTimes, remindtimeID)  
            remindTwiceList.pop(0)
    return True


#push?????????????????????
def pushTomorrowGetMedicineTextMsg():
    config = getKey()
    line_bot_api = LineBotApi(config["Channel access token"])
    postgres_manager = PostgresBaseManager()
    List = postgres_manager.getTomorrowList()

    print("tomorrowlist: ", len(List))
    if len(List):
        for r in List:
            reLineID = group_id
            #reLineID = r[5]
            #msg = '?????????????????????!\n' + '??????????????? : ' + str(
            #r[0]) + '\n' + '?????????????????? : ' + str(
            #r[2]) + '\n' + '???????????? : ' + str(r[3]) + ' ' + str(
            #r[4]) + '\n' + '???????????? : ' + str(r[6]) + '\n' + '??????????????????!'
            #line_bot_api.push_message(reLineID, TextSendMessage(text=msg))
            line_bot_api.push_message(
                reLineID,
                FlexSendMessage(alt_text='?????????????????????!',
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
                                            str(r[0]) + "?????????(" + str(r[3]) + ")????????????!",
                                            "weight":
                                            "bold",
                                            "size":
                                            "md",
                                            "wrap": True
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
                                                
                                            }, {
                                                "type":
                                                "box",
                                                "layout":
                                                "baseline",
                                                "spacing":
                                                "sm",
                                                "contents": [{
                                                    "type": "text",
                                                    "text": "?????????????????? :",
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
                                                    "text": "???????????? :",
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
                                                    "text": "???????????? : ",
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
                                                "text": "??????????????????!"
                                            }]
                                        }]
                                    }
                                }))
            #??????sentTimes
            current_sendTimes = r[8]
            remindtimeID = r[7]
            print("current times", current_sendTimes)
            postgres_manager = PostgresBaseManager()
            postgres_manager.updateSendTimes(current_sendTimes, remindtimeID)
    return True


#push?????????????????????
def pushTodayGetMedicineTextMsg():
    config = getKey()
    line_bot_api = LineBotApi(config["Channel access token"])
    postgres_manager = PostgresBaseManager()
    List = postgres_manager.getTodayList1()
    print("before30list: ", len(List))
    if len(List):
        for r in List:
            #????????????
            dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
            dt2 = dt1.astimezone(timezone(timedelta(hours=8)))  # ???????????? -> ?????????
            #?????????????????????????????????
            remindTime = (dt2 +
                          timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:00")
            #print("remind time (before 30): ", remindTime)
            #reLineID = r[5]
            reLineID = group_id
            #print("time: ", str(r[3]) + " " + str(r[4]))
            if str(r[3]) + " " + str(r[4]) == str(remindTime):
                #msg = '????????????30??????????????????/????????????!\n' + '??????????????? : ' + str(
                #r[0]) + '\n' + '?????????????????? : ' + str(
                #r[2]) + '\n' + '???????????? : ' + str(r[3]) + ' ' + str(
                #r[4]) + '\n' + '???????????? : ' + str(
                #r[6]) + '\n' + '??????????????????!'
                #line_bot_api.push_message(reLineID, TextSendMessage(text=msg))
                line_bot_api.push_message(
                    reLineID,
                    FlexSendMessage(alt_text='????????????10??????????????????/????????????!',
                                    contents={
                                        "type": "bubble",
                                        "body": {
                                            "type":
                                            "box",
                                            "layout":
                                            "vertical",
                                            "contents": [{
                                                "type": "text",
                                                "text": str(r[0]) + ", ????????????10??????????????????/????????????!",
                                                "weight": "bold",
                                                "size": "md",
                                                "wrap": True
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
                                                    
                                                }, {
                                                    "type":
                                                    "box",
                                                    "layout":
                                                    "baseline",
                                                    "spacing":
                                                    "sm",
                                                    "contents": [{
                                                        "type": "text",
                                                        "text": "?????????????????? :",
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
                                                        "text": "???????????? :",
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
                                                        "text": "???????????? : ",
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
                                                    "text": "??????????????????!"
                                                }]
                                            }]
                                        }
                                    }))
                #??????sentTimes
                current_sendTimes = r[7]
                remindtimeID = r[8]
                print("current times", current_sendTimes)
                postgres_manager = PostgresBaseManager()
                postgres_manager.updateSendTimes(current_sendTimes, remindtimeID)
    
    return True


#push?????????????????????check box
def pushGetMedicineFlexMsg():
    config = getKey()
    line_bot_api = LineBotApi(config["Channel access token"])
    postgres_manager = PostgresBaseManager()
    List = postgres_manager.getTodayList2()
    # send remind message
    #print("List length: ", len(List))
    #for r in List:
    #print(str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]))
    print("todaylist: ", len(List))
    if len(List):
        for r in List:
            #????????????
            dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
            dt2 = dt1.astimezone(timezone(timedelta(hours=8)))  # ???????????? -> ?????????
            now = dt2.strftime("%Y-%m-%d %H:%M:00")
            #print("now : ", now)

            reLineID = group_id
            reminderID = r[1]
            url = "https://medicine-reminder.r890910.repl.co/search-img?ReminderID=" + reminderID
            print(url)
            #reLineID = r[5]  #???????????????????????????Line ID
            #???????????????
            #type_number = postgres_manager.getReplyMsgType(reLineID)
            #msg = replyMsg(type_number)
            #print("msg:", msg)
            #'???????????????/??????????????????~'
            if str(r[3]) + " " + str(r[4]) == str(now):
                line_bot_api.push_message(
                    reLineID,
                    FlexSendMessage(alt_text='???????????????/??????????????????~',
                                    contents={
                                        "type": "bubble",
                                        "hero": {
                                                "type": "image",
                                                "url": url,
                                                "size": "full",
                                                "aspectRatio": "20:13",
                                                "aspectMode": "cover",
                                                "action": {
                                                  "type": "uri",
                                                  "uri": url
                                                }
                                            },
                                        "body": {
                                            "type":
                                            "box",
                                            "layout":
                                            "vertical",
                                            "contents": [{
                                                "type": "text",
                                                "text": str(r[0]) + "?????????????????????",
                                                "weight": "bold",
                                                "size": "xl",
                                                "wrap": True
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
                                                    
                                                }, {
                                                    "type":
                                                    "box",
                                                    "layout":
                                                    "baseline",
                                                    "spacing":
                                                    "sm",
                                                    "contents": [{
                                                        "type": "text",
                                                        "text": "?????????????????? :",
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
                                                        "text": "???????????? :",
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
                                                        "text": "???????????? : ",
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
                                                    "text": "??????????????????!"
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
                                                  "type": "postback",
                                                  "label": "?????????!",
                                                  "data": "tookMedicine"+ str(r[8]),
                                                    "displayText":"?????????" + str(r[2])
                                                }
                                            }],
                                            "flex":
                                            0
                                        }
                                    }))
                    
                #??????sentTimes
                current_sendTimes = r[7]
                remindtimeID = r[8]
                print("current times", current_sendTimes)
                postgres_manager = PostgresBaseManager()
                postgres_manager.updateSendTimes(current_sendTimes, remindtimeID)
    return True

#????????????????????????
def pushresetMsg():
    config = getKey()
    line_bot_api = LineBotApi(config["Channel access token"])
    postgres_manager = PostgresBaseManager()
    List = postgres_manager.getTodayList3()
    print("reset: ", len(List))
    if len(List):
        for r in List:
            #????????????
            dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
            dt2 = dt1.astimezone(timezone(timedelta(hours=8)))  # ???????????? -> ?????????
            #?????????????????????????????????
            before_10 = (dt2 + timedelta(minutes=-10)).strftime("%Y-%m-%d %H:%M:00")
            #now = dt2.strftime("%Y-%m-%d %H:%M:00")
            reLineID = group_id
            
            if str(r[3]) + " " + str(r[4]) == str(before_10):
                #print("push")
                line_bot_api.push_message(
            reLineID,
            FlexSendMessage(
                alt_text='???????????????????????????!',
                contents={
                    "type": "bubble",
                    "body": {
                        "type":
                        "box",
                        "layout":
                        "vertical",
                        "contents": [{
                            "type": "text",
                            "text": str(r[0]) + ", ????????????????????????30??????!",
                            "margin": "sm",
                            "wrap": True,
                            "weight": "bold"
                        },
                        {
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
                                                        "text": "??????????????? : ",
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
                                                        "text": "?????????????????? :",
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
                                                        "text": "???????????? :",
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
                                                        "text": "???????????? : ",
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
                                                }
                                                            ] }
                        ,{
                            "type": "text",
                            "text": "?????????????????????????????????????????????????????????",
                            "margin": "lg",
                            "wrap": True
                        }, {
                            "type": "text",
                            "text": "???????????????????????????:",
                            "margin": "xl"
                        }, {
                            "type": "text",
                            "text": "??????",
                            "size": "lg",
                            "color": "#2463EB",
                            "weight": "bold",
                            "wrap": True,
                            "decoration": "underline",
                            "align": "center",
                            "margin": "xl",
                            "action": {
                                "type": "uri",
                                "label": "action",
                                "uri":
                                "https://medicine-reminder.r890910.repl.co"
                            }
                        }]
                    }
                }))
            
            #??????sentTimes
            current_sendTimes = r[7]
            remindtimeID = r[8]
            #print("current times", current_sendTimes)
            postgres_manager = PostgresBaseManager()
            postgres_manager.updateSendTimes(current_sendTimes, remindtimeID)
    return True

#push????????????????????????
def pushOntimeTakeMedicine():
    config = getKey()
    line_bot_api = LineBotApi(config["Channel access token"])
    postgres_manager = PostgresBaseManager()
    List = postgres_manager.getLineID()

    if len(List):
        for r in List:
            reLineID = group_id
            ontime_times = postgres_manager.getCheck(reLineID)
            msg = '?????????~??????????????????' + str(ontime_times) + '???\n' + '???????????????!'
            if ontime_times > 0:
                line_bot_api.push_message(reLineID, TextSendMessage(text=msg))
    return True


#??????type_number???????????????reply message
def replyMsg(type_number):
    reply_str = ""
    if type_number == 1:
        reply_str = "??????~??????????????????????????????????????????!"
    elif type_number == 2:
        reply_str = "??????~????????????????????????????????????????????????!"
    elif type_number == 3:
        reply_str = "???!???????????????????????????????!!!!!!!"
    else:
        reply_str = "?????????????????????????????????"
    return reply_str
