import os
import logging
import gspread
import datetime

from flask import abort, jsonify

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)

channel_secret = os.environ.get('LINE_CHANNEL_SECRET')
channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
spreadsheet_id = os.environ.get('SPREADSHEET_ID')

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

def isFloat(text):
    if isinstance(text, float):
        return True
    else:
        return False

def convertFloat(text):
    try:
        return float(text)
    except:
        return text

def parseRequest(request):
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)
    return events

def getSheet():
    gc = gspread.service_account(filename = 'service_account.json')
    wb = gc.open_by_key(spreadsheet_id)
    ws = wb.sheet1
    return ws

def getValues(ws):
    values = ws.get_all_records()
    return values

def main(request):

    events = parseRequest(request)

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        text = event.message.text
        text = convertFloat(text)

        if isFloat(text):
            if text > 45: # 45°以上は異常とする
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = '体温が高すぎます')
                )

            else:
                ws = getSheet()
                values = getValues(ws)

                now = datetime.datetime.now() + datetime.timedelta(hours = 9) # 日本時間にするため、+9h
                time = f'{now.year}-{now.month}-{now.day} {str(now.hour)}:{str(now.minute).zfill(2)}:{str(now.second).zfill(2)}'
                ws.update(f'A{len(values) + 2}:B', [[time, text]])
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = '体温の入力を受け付けました')
                )
        
        else:
            if text == '削除':
                ws = getSheet()
                values = getValues(ws)
                if len(values) > 0:
                    ws.delete_row(len(values)+1)
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text = '最終結果を削除しました')
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text = 'データがありません')
                    )

            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = '数値のみ入力してください')
                )
                
    return 'OK'