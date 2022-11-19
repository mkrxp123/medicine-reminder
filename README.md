# medicine-reminder

## deploy guide

1. 先去[line developer](https://developers.line.biz/zh-hant/)申請一個帳號

2. 之後把創建一個專案，輸入 Provider name 並選擇 message API

3. 看這個[影片](https://www.youtube.com/watch?v=tsvIqoDxUJo&list=PLHOrrQ0BGMkRJDluig6dYVmNVgyHHEtCG&index=4)申請一個 bot，之後在裡面找到 Channel access token 和 Channel secret

4. 把上述兩個東西複製貼上到`setting/key.json`，格式如下(Liff ID 等一下會說明)

   ![](https://i.imgur.com/fPe1elS.png)

5. 用這個[教學](http://white5168.blogspot.com/2020/03/python-replit-line-bot-1.html#.Y2Dsx3ZBxPY)把 line bot 部署在[repl.it](https://replit.com/~)上面，然後當你成功跑出結果的時候，你應該會看到這個畫面

   ![](https://i.imgur.com/DBL8cJU.png)

6. 把上述畫面中的網址複製，並且另外去[line developer](https://developers.line.biz/zh-hant/)申請 Line Login，記得把 Scope 中 openid 和 profile 打開，然後在申請完成之後點擊 LIFF，點選 ADD(如下圖)，把複製的網站後面加個`/nav`，舉例`https://rosyfirebrickoperatingenvironment.mkrxp123.repl.co/nav`

   ![](https://i.imgur.com/PL2cEt5.png)

7. 你之後應該會看到這東西(size 看你想怎麼調整)，然後把 LIFF ID 複製到上面`key.json`裡面

   ![](https://i.imgur.com/YzFhYFM.png)

### 加 richmenu

1. 跑 python3 rich_menu.py, 會先噴一行{"richMenuId":xxxxxxxxx}再噴一些 error，噴 error 因為還沒設"richMenuId"，所以先把 "richMenuId":xxxxxxxxx 這行加進/setting/key.json
2. 再跑一次 python3 rich_menu.py
