# medicine-reminder

## deploy guide

1. 先去[line developer](https://developers.line.biz/zh-hant/)申請一個帳號

2. 之後把創建一個專案，輸入 Provider name 並選擇 message API

3. 看這個[影片](https://www.youtube.com/watch?v=tsvIqoDxUJo&list=PLHOrrQ0BGMkRJDluig6dYVmNVgyHHEtCG&index=4)申請一個 bot，之後在裡面找到 Channel access token 和 Channel secret

4. 把上述兩個東西複製貼上到`setting/key.json`，格式如下(Liff ID 等一下會說明)

   ![](https://i.imgur.com/fPe1elS.png)

5. 用這個[教學 1](http://white5168.blogspot.com/2020/03/python-replit-line-bot-1.html#.Y2Dsx3ZBxPY)[教學 2](https://www.youtube.com/watch?v=7roDWI0_YMo&list=PLHOrrQ0BGMkRJDluig6dYVmNVgyHHEtCG&index=5)把 line bot 部署在[repl.it](https://replit.com/~)上面，然後當你成功跑出結果的時候，你應該會看到這個畫面

   ![](https://i.imgur.com/DBL8cJU.png)

6. 把上述畫面中的網址複製，並且另外去[line developer](https://developers.line.biz/zh-hant/)申請 Line Login，記得把 Scope 中 openid 和 profile 打開，然後在申請完成之後點擊 LIFF，點選 ADD(如下圖)，把複製的網站後面加個`/nav`，舉例`https://rosyfirebrickoperatingenvironment.mkrxp123.repl.co/nav`，記得設定完之後在上方圖示，找到紅色框起來的部分設定為 publish，不然只有 developer 自己能用而已

   ![](https://i.imgur.com/PL2cEt5.png)
   ![](https://i.imgur.com/Cyhkn5I.png)

7. 你之後應該會看到這東西(size 看你想怎麼調整)，然後把 LIFF ID 複製到上面`key.json`裡面

   ![](https://i.imgur.com/YzFhYFM.png)

### 加 richmenu

1. 跑 `python3 rich_menu.py`, 會先噴一行`{"richMenuId":xxxxxxxxx}`再噴一些 error，噴 error 因為還沒設"richMenuId"，所以先把 "richMenuId":xxxxxxxxx 這行加進`/setting/key.json`
2. 再跑一次 `python3 rich_menu.py`

### 使用 pgAdmin 操作資料庫

1. 安裝後在左上角的 server 點右鍵選擇"RegisterServer"

   ![image](https://user-images.githubusercontent.com/46371116/202854145-dc647d2f-188a-4b1a-a6a3-6fe10e1b01f7.png)

2. Server 名稱可以自訂不影響

   ![image](https://user-images.githubusercontent.com/46371116/202854202-511f6610-4273-4175-af89-cdfff4ce6b2b.png)

3. Hostname 填入 "database-1.cbixtilkjhc6.ap-northeast-1.rds.amazonaws.com"
4. port 5432
5. password 12345678
6. 點 save 連接
7. 在 server 下面的 schema 裡可以找到所有的 schema 和 table

   ![image](https://user-images.githubusercontent.com/46371116/202854380-19156724-a7fd-4957-b234-c0caad609d74.png)

8.目前預計在 Testing Database 裡的 Public schema 測試

### 關於 database 的實作

目前實現將提醒結束日期、UserID、以及提醒時間存入 database 中
其他需要的資料為：

1. UserName 用戶名
2. GroupID 群組 ID
3. GroupName 群組名
4. Title 提醒標題
5. Picture 照片
6. Hospital 醫院名
7. GetMedicine 是否為吃藥提醒

### 前端加的小東西

回傳的 form 裡有表示是吃藥還是領藥的提醒，吃藥的話會是'med': 'take'，領藥的話會是'med': 'pick_up'

```
{'med': 'take', 'begindate': '2022-12-02T01:22', 'enddate': '2022-12-02T01:23', 'timepicker0': '00:02', 'user_id': 'U1e53f9b4b5e63bea01f5c192f45929cd'}
```
