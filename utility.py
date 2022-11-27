import json, sqlite3
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, String, MetaData, Integer, LargeBinary, VARCHAR, DateTime, Time, Date, Boolean
sqlite3.enable_callback_tracebacks(True)

def setup():
    user = 'postgres'
    password = '12345678'
    host = 'database-1.cbixtilkjhc6.ap-northeast-1.rds.amazonaws.com'
    port = 5432
    database = 'HCI database'
    try:
       # GET THE CONNECTION OBJECT (ENGINE) FOR THE DATABASE
        engine = create_engine(url="postgresql://{0}:{1}@{2}:{3}/{4}".format(
            user, password, host, port, database))
        print(f"Connection to the {host} for user {user} created successfully.")
        #setup schema of table
        meta = MetaData(engine)
        Users = Table('Users', meta, 
                      Column('LineID', String),
                      Column('UserName', String))
        RemindTimes = Table('RemindTimes', meta,
                            Column('ReminderID', Integer),
                            Column('RemindTime', Time),
                            Column('RemindDate', Date))
        Reminders = Table(
            'Reminders', meta, 
            Column('Title', String),
            Column('ReminderID', Integer), 
            Column('UserName', String),
            Column('Picture', LargeBinary, nullable=True),
            Column('Hospital', String),
            Column('GroupID', String),
            Column('GetMedicine', Boolean))
        RemindGroups = Table('RemindGroups', meta,
                             Column('GroupID', String),
                             Column('GroupName', String))
    except Exception as ex:
        print(
            "Connection could not be made due to the following error: \n",
            ex)
    return engine, Users, RemindTimes, Reminders, RemindGroups

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
