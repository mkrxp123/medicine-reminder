# medicine-reminder

## deploy guide

1. 先去[line developer](https://developers.line.biz/zh-hant/)申請一個帳號

2. 之後把創建一個專案，輸入Provider name並選擇message API

3. 看這個[影片](https://www.youtube.com/watch?v=tsvIqoDxUJo&list=PLHOrrQ0BGMkRJDluig6dYVmNVgyHHEtCG&index=4)申請一個bot，之後在裡面找到Channel access token和Channel secret

4. 把上述兩個東西複製貼上到setting/key.json，格式如下(Liff ID等一下會說明)

    ![](https://i.imgur.com/fPe1elS.png)

5. 用這個[教學](http://white5168.blogspot.com/2020/03/python-replit-line-bot-1.html#.Y2Dsx3ZBxPY)把line bot部署在repl.it上面，然後當你成功跑出結果的時候，你應該會看到這個畫面

    ![](https://i.imgur.com/DBL8cJU.png)

6. 把上述畫面中的網址複製，並且另外去[line developer](https://developers.line.biz/zh-hant/)申請Line Login，記得把Scope中openid和profile打開，然後在申請完成之後點擊LIFF，點選ADD(如下圖)，把複製的網站後面加個```/nav```，舉例```https://rosyfirebrickoperatingenvironment.mkrxp123.repl.co/nav```

    ![](https://i.imgur.com/PL2cEt5.png)

7. 你之後應該會看到這東西(size看你想怎麼調整)，然後把LIFF ID複製到上面```key.json```裡面

    ![](https://i.imgur.com/YzFhYFM.png)