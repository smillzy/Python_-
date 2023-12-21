# coding: utf-8
import requests
import pandas as pd
import json
import datetime as dt
from dateutil.relativedelta import relativedelta
import time
import sqlite3 as lite
import threading

dbname = '證交所資料.db'
tablename = '三大法人美日買賣金額統計表'
index = ['自營商自行買賣_買進金額', 
          '自營商自行買賣_賣出金額',
          '自營商避險_買進金額',
          '自營商避險_賣進金額',
          '投信_買進金額',
          '投信_賣進金額',
          '外資及陸資不含外資自營商_買進金額',
          '外資及陸資不含外資自營商_賣進金額',
          '外資自營商_買進金額',
          '外資自營商_賣進金額']

def insertdata(sqlfile, tablename, df):
    sql = 'INSERT OR REPLACE INTO {} {} VALUES ({});'
    sql = sql.format(tablename, tuple(df.columns.tolist()), ','.join('?'*len(df.columns)))
    sqloperate(sqlfile, sql, df)
    
def createtable(sqlfile, tablename, df):
    col = ','.join(list(map(lambda x :'{} TEXT NOT NULL'.format(x), df.columns)))
    pkey = 'PRIMARY KEY("日期")'
    sql = 'CREATE TABLE IF NOT EXISTS {} ({}, {});'.format(tablename, col, pkey)
    sqloperate(sqlfile, sql, df, True)

def sqloperate(sqlfile, sql, df, flag = False):
    con = lite.connect(sqlfile)
    cur = con.cursor()
    try:
        if flag:
            cur.execute(sql)
        else:
            cur.executemany(sql, df.values)
            con.commit()
    except Exception as e:
        print(e)
        con.rollback()
    cur.close()
    con.close()
    
def gettwsedata(dayDate):
    url  ='https://www.twse.com.tw/rwd/zh/fund/BFI82U'
    payload = {
        'response':'json',
        'dayDate':'20231201'
    }
    payload['dayDate'] = dayDate
    res = requests.get(url, params = payload)
    jd = json.loads(res.text)
    if jd['stat'] == 'OK':
        df = pd.DataFrame(jd['data'], columns = jd['fields'])
        df = df.apply(lambda x:x.str.replace(',', ''))
        data = (df.iloc[0, 1:3].tolist() +
            df.iloc[1, 1:3].tolist() +
            df.iloc[2, 1:3].tolist() +
            df.iloc[3, 1:3].tolist() +
            df.iloc[4, 1:3].tolist())
        df1 = pd.DataFrame(data, index = index).T
        df1.insert(0, '日期', jd['date'])
    else:
        df1 = pd.DataFrame()
    return df1

def countdown(t):
    while -1 < t:
        mins, secs = divmod(t, 60)
        txt = '{:02}:{:02}'.format(mins, secs)
        if t > 0:
            print(txt, end = '\r')
        if t == 0:
            print(txt, end = '\n')
        threading.Event().wait(1)
        t -= 1

data = []
base = dt.datetime.today() - relativedelta(days = 5)# months, years, weeks
while base < dt.datetime.today():
    assigndate = base.strftime('%Y%m%d')
    print(assigndate)
    df1 = gettwsedata(assigndate)
    if not df1.empty:
        data.append(df1)
    base += relativedelta(days = 1) 
    countdown(15)
df = pd.concat(data, ignore_index = True)
createtable(dbname, tablename, df)
insertdata(dbname, tablename, df)
df
