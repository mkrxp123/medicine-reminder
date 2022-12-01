import json, sqlite3
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, String, MetaData, Integer, LargeBinary, VARCHAR, DateTime, Time, Date, Boolean
sqlite3.enable_callback_tracebacks(True)

class Database:

    user = 'postgres'
    password = '12345678'
    host = 'database-1.cbixtilkjhc6.ap-northeast-1.rds.amazonaws.com'
    port = 5432
    dbname = 'HCI database'

    def __init__(self):
        
        try:
       # GET THE CONNECTION OBJECT (ENGINE) FOR THE DATABASE
            self.db = create_engine(url="postgresql://{0}:{1}@{2}:{3}/{4}".format(
                self.user, self.password, self.host, self.port, self.dbname))
            print(f"Connection to the {self.host} for user {self.user} created successfully.")
            #setup schema of table
            self.meta = MetaData(self.db)
            self.Users = Table('Users', self.meta, 
                          Column('LineID', String),
                          Column('UserName', String))
            self.RemindTimes = Table('RemindTimes', self.meta,
                                Column('ReminderID', Integer),
                                Column('RemindTime', Time),
                                Column('RemindDate', Date))
            self.Reminders = Table(
                'Reminders', self.meta, 
                Column('Title', String),
                Column('ReminderID', Integer), 
                Column('UserName', String),
                Column('Picture', LargeBinary, nullable=True),
                Column('Hospital', String),
                Column('GroupID', String),
                Column('GetMedicine', Boolean))
            self.RemindGroups = Table('RemindGroups', self.meta,
                                 Column('GroupID', String),
                                 Column('GroupName', String))
      
        except Exception as ex:
            print("Connection could not be made due to the following error: \n",
                ex)  

    def InsertGroup(self, id, name):
        insert_statement = self.RemindGroups.insert().values(GroupID=id, GroupName=name)
        self.db.execute(insert_statement)

    def GetGroupNameFromGroupID(self, id):
        select_statement = self.RemindGroups.select().where(self.RemindGroups.c.GroupID == id)
        return self.db.execute(select_statement).fetchall()

    def InsertUser(self, id, name):
        insert_statement = self.Users.insert().values(LineID=id, UserName=name)
        self.db.execute(insert_statement)

    def GetUserNamefromLineID(self, id):
        select_statement = self.Users.select().where(self.Users.c.LineID == id)
        return self.db.execute(select_statement).fetchall()

    def InsertReminder(self, title, rid, name, pic, hospital, gid, type):
        insert_statement = self.Reminders.insert().values(
            Title=title, ReminderID=rid, UserName=name, Picture=pic, Hospital=hospital,
            GroupID=gid, GetMedicine=type)
        self.db.execute(insert_statement)

    def GetReminderFromReminderID(self, id):
        select_statement = self.Reminders.select().where(self.Reminders.c.ReminderID == id)
        return self.db.execute(select_statement).fetchall()

    def InsertRemindTime(self, id, time, date):
        insert_statement = self.RemindTimes.insert().values(
            ReminderID=id, RemindTime=time, RemindDate=date)
        self.db.execute(insert_statement)

    def GetRemindTimesFromReminderID(self, id):
        select_statement = self.RemindTimes.select().where(self.RemindTimes.c.ReminderID == id)
        return self.db.execute(select_statement).fetchall()
    

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
