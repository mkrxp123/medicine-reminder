# reference: https://reurl.cc/NGykqq
import psycopg
from datetime import datetime, timezone, timedelta, tzinfo

class PostgresBaseManager:
  def __init__(self):
    self.dbname = 'HCI database'
    self.user = 'postgres'
    self.password='12345678'
    self.host = 'database-1.cbixtilkjhc6.ap-northeast-1.rds.amazonaws.com'
    self.port = '5432'
    self.conn = self.connectServerPostgresdb()

  def connectServerPostgresdb(self): #連接Postgres SQL認證用
    conn = psycopg.connect(
      dbname=self.dbname, 
      user=self.user, 
      password=self.password, 
      host=self.host, 
      port=self.port)
    print("Connection established!")
    return conn

  def closePostgresConnection(self): #關閉資料庫連線
    self.conn.close()
  
  def runServerPostgresdb(self): #測試是否可以連線到Postgres SQL
    cur = self.conn.cursor()
    cur.execute('SELECT VERSION()')
    results = cur.fetchall()
    print("Database version : {0} ".format(results))
    self.conn.commit()
    cur.close()

  #抓取吃藥提醒
  def checkRemindTime(self):
    cur = self.conn.cursor()
    sql="""
SELECT  public.\"Reminders\".\"ReminderID\", public.\"RemindTimes\".\"RemindDate\", public.\"RemindTimes\".\"RemindTime\", public.\"Reminders\".\"Title\", public.\"Users\".\"LineID\", public.\"RemindTimes\".\"RemindTimeID\", public.\"Reminders\".\"UserName\", public.\"RemindTimes\".\"SendTimes\", public.\"Users\".\"PhoneNumber\"
FROM (public.\"Users\" INNER JOIN public.\"Reminders\" 
ON public.\"Users\".\"UserName\"=public.\"Reminders\".\"UserName\")
INNER JOIN public.\"RemindTimes\" 
ON public.\"Reminders\".\"ReminderID\"=public.\"RemindTimes\".\"ReminderID\"
WHERE public.\"Reminders\".\"GetMedicine\"=False and public.\"RemindTimes\".\"Checked\" != True and public.\"RemindTimes\".\"SendTimes\"=0
    """
    cur.execute(sql)
    tz = timezone(timedelta(hours=+8))
    now = datetime.now(tz)
    t1 = now+timedelta(seconds=10)
    t2 = now-timedelta(seconds=10)
    t3 = now
    t1 = t1.replace(tzinfo=None)
    t2 = t2.replace(tzinfo=None)
    t3 = t3.replace(tzinfo=None)
    rows = cur.fetchall()
    list = []
    for row in rows:
      #print(str(row[0])+","+str(row[3])+","+str(row[4]))
      t = datetime.strptime((str(row[1])+" "+str(row[2])), "%Y-%m-%d %H:%M:%S")
      if(t3>=t):
        print(t)
        list.append([str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), int(row[5]), str(row[6]), int(row[7]), str(row[8])])
      
      
    self.conn.commit()
    cur.close()
    return list

  #更新remind time checked狀態
  #抓取吃藥提醒
  def getRemindTwiceList(self):
    cur = self.conn.cursor()
    sql="""
SELECT  public.\"Reminders\".\"ReminderID\", public.\"RemindTimes\".\"RemindDate\", public.\"RemindTimes\".\"RemindTime\", public.\"Reminders\".\"Title\", public.\"Users\".\"LineID\", public.\"RemindTimes\".\"RemindTimeID\", public.\"Reminders\".\"UserName\", public.\"RemindTimes\".\"SendTimes\", public.\"Users\".\"PhoneNumber\"
FROM (public.\"Users\" INNER JOIN public.\"Reminders\" 
ON public.\"Users\".\"UserName\"=public.\"Reminders\".\"UserName\")
INNER JOIN public.\"RemindTimes\" 
ON public.\"Reminders\".\"ReminderID\"=public.\"RemindTimes\".\"ReminderID\"
WHERE public.\"Reminders\".\"GetMedicine\"=False and public.\"RemindTimes\".\"Checked\" != True and public.\"RemindTimes\".\"SendTimes\"=1
    """
    cur.execute(sql)
    tz = timezone(timedelta(hours=+8))
    now = datetime.now(tz)
    #t1 = now+timedelta(minutes=10)
    t2 = now-timedelta(minutes=10)
    #t1 = t1.replace(tzinfo=None)
    t2 = t2.replace(tzinfo=None)
    rows = cur.fetchall()
    list = []
    for row in rows:
      t = datetime.strptime((str(row[1])+" "+str(row[2])), "%Y-%m-%d %H:%M:%S")
      if(t<=t2):
        print(t)
        list.append([str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), int(row[5]), str(row[6]), int(row[7]), str(row[8])])
      
      
    self.conn.commit()
    cur.close()
    return list

  #更新remind time checked狀態
  def updateRemindTimeChecked(self, checked, remindTimeID):
    cursor = self.conn.cursor()
    update = """UPDATE public.\"RemindTimes\" 
                set \"Checked\" = %b 
                WHERE \"RemindTimeID\" = %b"""
    
    cursor.execute(update,(checked, remindTimeID))
    self.conn.commit()
    cursor.close()

  #更新user手機號碼
  def updatePhoneNumber(self, userID, phoneNumber):
    cursor = self.conn.cursor()
    update = """UPDATE public.\"Users\" 
                set \"PhoneNumber\" = %s
                WHERE \"LineID\" = %s"""

    cursor.execute(update, (phoneNumber, userID))
    self.conn.commit()
    cursor.close()

  #取得user手機號碼
  
  def getPhoneNumber(self, userID):
    cursor = self.conn.cursor()
    sql = """SELECT public.\"Users\".\"LineID\", public.\"Users\".\"PhoneNumber\" 
              FROM public.\"Users\""""
    cursor.execute(sql)
    data = cursor.fetchall()
    list = []
    for r in data:
      if str(r[0]) == userID:
        list.append([str(r[1])]) 
    self.conn.commit()
    cursor.close()
    return list

  #更新user對應的group id
  
  def updateGroupID(self, userID, groupID):
    cursor = self.conn.cursor()
    update = """UPDATE public.\"Users\" 
                set \"PhoneNumber\" = %s
                WHERE \"LineID\" = %s"""

    cursor.execute(update, (groupID, userID))
    self.conn.commit()
    cursor.close()

  #抓30分鐘前的資料  
  def getTodayList1(self):
    #抓取資料
    cursor = self.conn.cursor()
    data = """SELECT public.\"Reminders\".\"UserName\", public.\"Reminders\".\"ReminderID\",   
                       public.\"Reminders\".\"Title\", public.\"RemindTimes\".\"RemindDate\",     
                       public.\"RemindTimes\".\"RemindTime\", public.\"Users\".\"LineID\",   
                       public.\"Reminders\".\"Hospital\", public.\"RemindTimes\".\"SendTimes\",   
                       public.\"RemindTimes\".\"RemindTimeID\"
                FROM (public.\"Users\" INNER JOIN public.\"Reminders\" 
                ON public.\"Users\".\"UserName\"=public.\"Reminders\".\"UserName\")
                INNER JOIN public.\"RemindTimes\" 
                ON public.\"Reminders\".\"ReminderID\"=public.\"RemindTimes\".\"ReminderID\"
                WHERE public.\"Reminders\".\"GetMedicine\"=True and 
                public.\"RemindTimes\".\"Checked\" != True and public.\"RemindTimes\".\"SendTimes\"=1 """
    cursor.execute(data)
    data2 = cursor.fetchall()

    #取得日期
    dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
    dt2 = dt1.astimezone(timezone(timedelta(hours=8)))  # 轉換時區 -> 東八區
    #dt3 = (dt2 + timedelta(hours = -1) + timedelta(seconds = -1*dt2.second)).strftime("%H:%M:%S")   #輸出比現在時間早半小時
    today = dt2.strftime("%Y-%m-%d")
    #print("today : ", today)

    list = []
    for r in data2:
      if str(r[3]) == str(today):
        list.append([str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]), int(r[7]), int(r[8])])
        #print("todatList: ", str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]), str(r[7]), str(r[8]))

    self.conn.commit()
    cursor.close()
    return list
  
    
  #抓取現在的提醒
  def getTodayList2(self):
    #抓取資料
    cursor = self.conn.cursor()
    data = """SELECT public.\"Reminders\".\"UserName\", public.\"Reminders\".\"ReminderID\",   
                       public.\"Reminders\".\"Title\", public.\"RemindTimes\".\"RemindDate\",     
                       public.\"RemindTimes\".\"RemindTime\", public.\"Users\".\"LineID\",   
                       public.\"Reminders\".\"Hospital\", public.\"RemindTimes\".\"SendTimes\",   
                       public.\"RemindTimes\".\"RemindTimeID\"
                FROM (public.\"Users\" INNER JOIN public.\"Reminders\" 
                ON public.\"Users\".\"UserName\"=public.\"Reminders\".\"UserName\")
                INNER JOIN public.\"RemindTimes\" 
                ON public.\"Reminders\".\"ReminderID\"=public.\"RemindTimes\".\"ReminderID\"
                WHERE public.\"Reminders\".\"GetMedicine\"= True
                and public.\"RemindTimes\".\"Checked\" != True and public.\"RemindTimes\".\"SendTimes\"=2 """
    cursor.execute(data)
    data2 = cursor.fetchall()

    #取得日期
    dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
    dt2 = dt1.astimezone(timezone(timedelta(hours=8)))  # 轉換時區 -> 東八區
    #dt3 = (dt2 + timedelta(hours = -1) + timedelta(seconds = -1*dt2.second)).strftime("%H:%M:%S")   #輸出比現在時間早半小時
    today = dt2.strftime("%Y-%m-%d")
    #print("today : ", today)

    list = []
    for r in data2:
      if str(r[3]) == str(today):
        list.append([str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]), int(r[7]), int(r[8])])
        #print("todatList: ", str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]), str(r[7]), str(r[8]))

    self.conn.commit()
    cursor.close()
    return list

  #抓取錯過的今天領藥提醒
  def getTodayList3(self):
    #抓取資料
    cursor = self.conn.cursor()
    data = """SELECT public.\"Reminders\".\"UserName\", public.\"Reminders\".\"ReminderID\",   
                       public.\"Reminders\".\"Title\", public.\"RemindTimes\".\"RemindDate\",     
                       public.\"RemindTimes\".\"RemindTime\", public.\"Users\".\"LineID\",   
                       public.\"Reminders\".\"Hospital\", public.\"RemindTimes\".\"SendTimes\",   
                       public.\"RemindTimes\".\"RemindTimeID\"
                FROM (public.\"Users\" INNER JOIN public.\"Reminders\" 
                ON public.\"Users\".\"UserName\"=public.\"Reminders\".\"UserName\")
                INNER JOIN public.\"RemindTimes\" 
                ON public.\"Reminders\".\"ReminderID\"=public.\"RemindTimes\".\"ReminderID\"
                WHERE public.\"Reminders\".\"GetMedicine\"= True
                and public.\"RemindTimes\".\"Checked\" != True and public.\"RemindTimes\".\"SendTimes\"=3 """
    cursor.execute(data)
    data2 = cursor.fetchall()

    #取得日期
    dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
    dt2 = dt1.astimezone(timezone(timedelta(hours=8)))  # 轉換時區 -> 東八區
    today = dt2.strftime("%Y-%m-%d")
    #print("today : ", today)
    
    list = []
    for r in data2:
      if str(r[3]) == str(today):
        list.append([str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]), int(r[7]), int(r[8])])
        #print("todatList: ", str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]), str(r[7]), str(r[8]))

    self.conn.commit()
    cursor.close()
    return list

  #抓取明天的領藥資訊
  def getTomorrowList(self):
    #抓取資料
    cursor = self.conn.cursor()
    data = """SELECT public.\"Reminders\".\"UserName\", public.\"Reminders\".\"ReminderID\",   
                       public.\"Reminders\".\"Title\", public.\"RemindTimes\".\"RemindDate\",     
                       public.\"RemindTimes\".\"RemindTime\", public.\"Users\".\"LineID\",   
                       public.\"Reminders\".\"Hospital\", public.\"RemindTimes\".\"RemindTimeID\",   
                       public.\"RemindTimes\".\"SendTimes\"
                FROM (public.\"Users\" INNER JOIN public.\"Reminders\" 
                ON public.\"Users\".\"UserName\"=public.\"Reminders\".\"UserName\")
                INNER JOIN public.\"RemindTimes\" 
                ON public.\"Reminders\".\"ReminderID\"=public.\"RemindTimes\".\"ReminderID\"
                WHERE public.\"Reminders\".\"GetMedicine\"= True 
                and public.\"RemindTimes\".\"Checked\" != True and public.\"RemindTimes\".\"SendTimes\"= 0 """
    cursor.execute(data)
    data2 = cursor.fetchall()

    #取得日期
    dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
    dt2 = dt1.astimezone(timezone(timedelta(hours=8)))  # 轉換時區 -> 東八區
    #print("dt2: ", dt2)
    #dt3 = (dt2 + timedelta(hours = -1) + timedelta(seconds = -1*dt2.second)).strftime("%H:%M:%S")   #輸出比現在時間早半小時
    #tomorrow = (dt2 + timedelta(days=1 )).strftime("%Y-%m-%d")   #輸出比現在時間早一天
    tomorrow = dt2.strftime("%Y-%m-%d")
    #print("tomorrow : ", tomorrow)

    list = []
    for r in data2: 
      if str(r[3]) == str(tomorrow):
        list.append([str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]), int(r[7]), int(r[8])])
        #print(str(r[0]), str(r[1]), str(r[2]), str(r[3]), str(r[4]), str(r[5]), str(r[6]), str(r[7]), str(r[8]))

    self.conn.commit()
    cursor.close()
    return list

  #更新Users table的ReplyMsgType
  
  
  def updateReplyMsgType(self, value, remindTimeID):

    cursor = self.conn.cursor()
    update = """UPDATE public.\"Users\" 
                set \"ReplyMsgType\" = %b 
                WHERE \"LineID\" = %s"""

    cursor.execute(update, (value, remindTimeID))
    #print("complete update ReplyMsgType!")
    self.conn.commit()
    cursor.close()

  #更新RemindTimes table的SendTimes
  
  def updateSendTimes(self, current_sendTimes, userID):

    update_sendTimes = current_sendTimes+1
    cursor = self.conn.cursor()
    update = """UPDATE public.\"RemindTimes\" 
                set \"SendTimes\" = %b 
                WHERE \"RemindTimeID\" = %b"""
    
    cursor.execute(update, (update_sendTimes, userID))
    #print("complete update sendTimes!")
    
    self.conn.commit()
    cursor.close()

  #抓取ReplyMsgType
  
  def getReplyMsgType(self, userID):

    cursor = self.conn.cursor()
    data = """SELECT public.\"Users\".\"ReplyMsgType\", public.\"Users\".\"LineID\" 
              FROM public.\"Users\""""
    cursor.execute(data)
    rows = cursor.fetchall()

    type_number = 0
    for r in rows:
      if str(r[1]) == userID:
        type_number = r[0]
        break
    #print("type number:", type_number)
      
    self.conn.commit()
    cursor.close()
    return type_number

  #抓取Check
  
  def getCheck(self, userID):

    cursor = self.conn.cursor()
    data = """SELECT public.\"RemindTimes\".\"Checked\", public.\"Users\".\"LineID\",     
                     public.\"RemindTimes\".\"RemindDate\", public.\"RemindTimes\".\"RemindTime\"
              FROM (public.\"Users\" INNER JOIN public.\"Reminders\" 
              ON public.\"Users\".\"UserName\"=public.\"Reminders\".\"UserName\")
              INNER JOIN public.\"RemindTimes\" 
              ON public.\"Reminders\".\"ReminderID\"=public.\"RemindTimes\".\"ReminderID\"
              WHERE public.\"Reminders\".\"GetMedicine\"=False 
              and public.\"RemindTimes\".\"Checked\"=True"""
    cursor.execute(data)
    rows = cursor.fetchall()

    #取得日期
    dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
    dt2 = dt1.astimezone(timezone(timedelta(hours=8)))  # 轉換時區 -> 東八區
    today = dt2.strftime("%Y-%m-%d")

    counter = 0
    for r in rows:
      #print(str(r[1]), userID)
      #print(str(r[2]), today)
      #print(str(r[0]))
      if (str(r[1]) == str(userID)) and (str(r[2]) == str(today)):
        #print("+1")
        counter = counter + 1
      #print(userID, counter)
    #print("counter:", counter)
    self.conn.commit()
    cursor.close()
    return counter

  
  #抓取LineID
  
  def getLineID(self):

    cursor = self.conn.cursor()
    data = """SELECT public.\"Users\".\"LineID\" FROM public.\"Users\""""
    cursor.execute(data)
    data2 = cursor.fetchall()

    list = []
    for r in data2:
      list.append([str(r[0])])
      #print(str(r[0]))
      
    self.conn.commit()
    cursor.close()
    return list
