import json, sqlite3
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, String, MetaData, Integer, LargeBinary, VARCHAR, DateTime, Time, Date, Boolean

sqlite3.enable_callback_tracebacks(True)
from connection import *
from linebot import LineBotApi
from linebot.models import TextSendMessage, ImageSendMessage, MessageEvent, TextMessage, TemplateSendMessage, ButtonsTemplate, PostbackAction, MessageTemplateAction, PostbackEvent
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta, datetime


class Database:

  user = 'postgres'
  password = '12345678'
  host = 'database-1.cbixtilkjhc6.ap-northeast-1.rds.amazonaws.com'
  port = 5432
  dbname = 'HCI database'
  session = None
  reminder_id = 0

  def __init__(self):

    try:
      # GET THE CONNECTION OBJECT (ENGINE) FOR THE DATABASE
      self.db = create_engine(url="postgresql://{0}:{1}@{2}:{3}/{4}".format(
        self.user, self.password, self.host, self.port, self.dbname))
      print(
        f"Connection to the {self.host} for user {self.user} created successfully."
      )
      #setup schema of table
      self.meta = MetaData(self.db)
      self.Users = Table('Users', self.meta, Column('LineID', String),
                         Column('UserName', String))
      self.RemindTimes = Table('RemindTimes', self.meta,
                               Column('ReminderID', Integer),
                               Column('RemindTime', Time),
                               Column('RemindDate', Date))
      self.Reminders = Table('Reminders', self.meta, Column('Title', String),
                             Column('ReminderID', Integer),
                             Column('UserName', String),
                             Column('Picture', LargeBinary, nullable=True),
                             Column('Hospital', String),
                             Column('GroupID', String),
                             Column('GetMedicine', Boolean),
                             Column('PhoneNumber', String))
      self.RemindGroups = Table('RemindGroups', self.meta,
                                Column('GroupID', String),
                                Column('GroupName', String))
      Session = sessionmaker(bind=self.db)
      self.session = Session()
      self.reminder_id = self.GetLargestReminderID() + 1

    except Exception as ex:
      print("Connection could not be made due to the following error: \n", ex)

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

  def InsertReminder(self, title, rid, name, pic, hospital, gid, type):
    insert_statement = self.Reminders.insert().values(Title=title,
                                                      ReminderID=rid,
                                                      UserName=name,
                                                      Picture=pic,
                                                      Hospital=hospital,
                                                      GroupID=gid,
                                                      GetMedicine=type)
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
    return self.session.query(func.max(self.Reminders.c.ReminderID)).scalar()

  def InsertForm(self, form):
    # 統整參數
    get_med = True
    title = ''
    pic = None
    begin_date_str = ''
    end_date_str = ''
    user_name = ''
    hospital = ''
    group_id = None
    phone_number = ''

    # 取得給reminder的實際數值
    if form['med'] == 'take':
      get_med = False
    title = form['title']
    begin_date_str = form['begindate']
    end_date_str = form['enddate']
    user_name = self.GetUserNamefromLineID(form['user_id'])
    hospital = form['hospital']

    # insert至reminder
    insert_statement = self.Reminders.insert().values(
      Title=title,
      ReminderID=self.reminder_id,
      UserName=user_name,
      Picture=pic,
      Hospital=hospital,
      GroupID=group_id,
      GetMedicine=get_med,
      PhoneNumber=phone_number)
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
          ReminderID=self.reminder_id, RemindTime=current_time, RemindDate=day)
        self.db.execute(insert_statement)

    # 最後記得id++
    self.reminder_id += 1

  # 查詢今日所有的提醒的全部資料並存入一個list of dictionary 大概長這樣[{}, {}, {}]
  def GetTodayReminds(self):
    today = datetime.today().strftime('%Y-%m-%d')
    select_statement = '''select * from (select * from "RemindTimes" where "RemindDate" = '{0}'::date) as RemindTime natural join "Reminders" natural join "Users" natural join "RemindGroups"'''.format(
      today)
    result = self.db.execute(select_statement).fetchall()
    Today_Reminds = []
    for row in result:
      Today_Reminds.append(dict(row))
    return Today_Reminds

  # 查詢特定使用者的全部資料
  def GetUserAllReminds(self, user_id):
    select_statement = '''select * from (select * from "Users" where "LineID" = '{0}') as users natural join "Reminders" natural join "RemindTimes" natural join "RemindGroups"'''.format(
      user_id)
    result = self.db.execute(select_statement).fetchall()
    user_data = []
    dates = []
    for row in result:
      user_data.append(dict(row))
    select_statement = '''with date_calc as (select "ReminderID", min("RemindDate") as begindate, max("RemindDate") as enddate from "RemindTimes" Group by "ReminderID" order by "ReminderID" asc) select distinct "ReminderID", begindate, enddate from (select * from "Users" where "LineID" = '{0}') as users natural join "Reminders" natural join "RemindTimes" natural join "RemindGroups" natural join "date_calc"'''.format(
      user_id)
    result = self.db.execute(select_statement).fetchall()
    for row in result:
      dates.append(dict(row))
    #user_data = sorted(user_data, key = itemgetter('ReminderID'))
    #select_statement = '''with date_calc as (select "ReminderID", min("RemindDate") as begindate, max("RemindDate") as enddate from "RemindTimes" Group by "ReminderID" order by "ReminderID" asc) select distinct "ReminderID", begindate, enddate from (select * from "Users" where "LineID" = 'U1100043733aea416a3c3055dfa4accdf') as users natural join "Reminders" natural join "RemindTimes" natural join "RemindGroups" natural join "date_calc"'''
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
  if len(remindList):
    while (len(remindList)):
      msg = postgres_manager.getPostgresdbData()
      reTitle = remindList[0][1]
      reLineID = remindList[0][2]  #要傳送提醒的使用者Line ID
      buttons_template = ButtonsTemplate(
        title=reTitle,
        thumbnail_image_url='https://medlineplus.gov/images/Medicines.jpg',
        text=msg,
        actions=[
          PostbackAction(label='確認', data='ateMedicine', display_text='已吃藥!')
        ])
      template_message = TemplateSendMessage(alt_text='吃藥提醒',
                                             template=buttons_template)
      line_bot_api.push_message(reLineID, template_message)
      remindList.pop(0)
  return True
