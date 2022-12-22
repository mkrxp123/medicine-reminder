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

  def getPostgresdbData(self): #取得資料庫內資料
    # https://ithelp.ithome.com.tw/articles/10268457
    cur = self.conn.cursor()
    sql="""
SELECT public.\"Users\".\"UserName\", public.\"Users\".\"LineID\", public.\"Reminders\".\"ReminderID\", public.\"RemindTimes\".\"RemindTime\", public.\"RemindTimes\".\"RemindDate\"
FROM (public.\"Users\" INNER JOIN public.\"Reminders\" 
ON public.\"Users\".\"UserName\"=public.\"Reminders\".\"UserName\")
INNER JOIN public.\"RemindTimes\" 
ON public.\"Reminders\".\"ReminderID\"=public.\"RemindTimes\".\"ReminderID\"
WHERE public.\"Reminders\".\"GetMedicine\"=True
    """
    cur.execute(sql)
    rows = cur.fetchall()
    #for row in rows:
      #print("%s, %s, %s, %s, %s" %(str(row[0]), str(row[1]),str(row[2]), str(row[3]),str(row[4])))
    message = "是時候該吃藥了，上方為藥品說明圖片。\n"
    message+=("若完成服藥，請點底下確認鍵，否則將持續提醒!\n")
    self.conn.commit()
    cur.close()
    return message

  def checkRemindTime(self):
    cur = self.conn.cursor()
    sql="""
SELECT  public.\"Reminders\".\"ReminderID\", public.\"RemindTimes\".\"RemindDate\", public.\"RemindTimes\".\"RemindTime\", public.\"Reminders\".\"Title\", public.\"Users\".\"LineID\"
FROM (public.\"Users\" INNER JOIN public.\"Reminders\" 
ON public.\"Users\".\"UserName\"=public.\"Reminders\".\"UserName\")
INNER JOIN public.\"RemindTimes\" 
ON public.\"Reminders\".\"ReminderID\"=public.\"RemindTimes\".\"ReminderID\"
WHERE public.\"Reminders\".\"GetMedicine\"=True
    """
    cur.execute(sql)
    tz = timezone(timedelta(hours=+8))
    now = datetime.now(tz)
    t1 = now+timedelta(minutes=5)
    t2 = now-timedelta(minutes=5)
    t1 = t1.replace(tzinfo=None)
    t2 = t2.replace(tzinfo=None)
    rows = cur.fetchall()
    list = []
    for row in rows:
      print(str(row[0])+","+str(row[3])+","+str(row[4]))
      t = datetime.strptime((str(row[1])+" "+str(row[2])), "%Y-%m-%d %H:%M:%S")
      if(t<=t1 and t2<=t):
        print(t)
        list.append([str(row[0]), str(row[3]), str(row[4])])
      
    self.conn.commit()
    cur.close()
    return list
