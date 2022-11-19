import requests
import json
from utility import getKey, timetable
from linebot import LineBotApi
# 設定 headers，輸入你的 Access Token，記得前方要加上「Bearer 」( 有一個空白 )


def rich_menu():
    config = getKey()
    headers = {'Authorization': 'Bearer ' +
               config["Channel access token"], 'Content-Type': 'application/json'}

    body = {
        'size': {'width': 2500, 'height': 843},   # 設定尺寸
        'selected': 'true',                        # 預設是否顯示
        'name': 'Richmenu demo',                   # 選單名稱
        'chatBarText': 'Richmenu demo',            # 選單在 LINE 顯示的標題
        'areas': [                                  # 選單內容
            {
                # 選單位置與大小
                'bounds': {'x': 0, 'y': 0, 'width': 833, 'height': 843},
                # 點擊後傳送文字
                'action': {'type': 'message', 'text': '文字'}
            },
            {
                'bounds': {'x': 833, 'y': 0, 'width': 833, 'height': 843},
                'action': {'type': 'message', 'text': '網址'}
            },
            {
                'bounds': {'x': 1666, 'y': 0, 'width': 833, 'height': 8443},
                'action': {'type': 'message', 'text': '位置'}
            }
        ]
    }
    # 向指定網址發送 request
    req = requests.request('POST', 'https://api.line.me/v2/bot/richmenu',
                           headers=headers, data=json.dumps(body).encode('utf-8'))
    # 印出得到的結果
    print(req.text)
    line_bot_api = LineBotApi(config["Channel access token"])
    try:
        with open('images/rich-menu.jpg', 'rb') as f:
            line_bot_api.set_rich_menu_image(
                config["richMenuId"], 'image/jpeg', f)
        req = requests.request(
            'POST', 'https://api.line.me/v2/bot/user/all/richmenu/'+config["richMenuId"], headers=headers)

        print(req.text)
    except:
        req = requests.request(
            'POST', 'https://api.line.me/v2/bot/user/all/richmenu/'+config["richMenuId"], headers=headers)

        print(req.text)


rich_menu()
