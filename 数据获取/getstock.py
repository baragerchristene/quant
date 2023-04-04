# -*- coding: utf-8 -*-
# 指定解释器位置
#!/root/miniconda3/bin/python
# nohup /root/miniconda3/bin/python /root/binance_trade_tool_vpn/quant/数据获取/getbtc指标.py
# 安装币安的python库
# pip install python-binance
import akshare as ak
import pandas as pd
import datetime
from pymongo import MongoClient, ASCENDING
import time

# 获取当前日期
current_date = datetime.datetime.now().strftime('%Y-%m-%d')
# 读取180天内的数据，这里面还得排除掉节假日
date_ago = datetime.datetime.now() - datetime.timedelta(days=540)
start_date = date_ago.strftime('%Y%m%d')  # 要求格式"19700101"
client = MongoClient(
    'mongodb://wth000:wth000@43.159.47.250:27017/dbname?authSource=wth000')
db = client['wth000']
# 输出的表为截止日期
name = 'STOCK'
collection = db[f"{name}"]

print(f'开始日期{start_date}')
# 以日期为索引
# collection.create_index([('日期', ASCENDING)])

collection.drop()  # 清空集合中的所有文档

# 从akshare获取A股主板股票的代码和名称
stock_info_df = ak.stock_zh_a_spot_em()
# 迭代每只股票，获取每天的前复权日k数据
for code in stock_info_df['代码']:
    k_data = ak.stock_zh_a_hist(
        symbol=code, start_date=start_date, adjust="qfq")
    k_data['代码'] = code
    k_data['成交量'] = k_data['成交量'].astype(float)

    # 将动态市盈率、市净率、流通市值、总市值、成交额等信息加入到数据中
    k_data['名称'] = stock_info_df.loc[stock_info_df['代码'] == code, '名称'].values[0]
    k_data['流通市值'] = stock_info_df.loc[stock_info_df['代码'] == code, '流通市值'].values[0]
    k_data['总市值'] = stock_info_df.loc[stock_info_df['代码'] == code, '总市值'].values[0]
    k_data['成交额'] = stock_info_df.loc[stock_info_df['代码'] == code, '成交额'].values[0]
    # 将数据插入MongoDB，如果已经存在相同时间戳和内容的数据则跳过
    collection.insert_many(k_data.to_dict('records'))

print('任务已经完成')
# time.sleep(3600)
# limit = 400000
# if collection.count_documents({}) >= limit:
#     oldest_data = collection.find().sort([('日期', 1)]).limit(
#         collection.count_documents({})-limit)
#     ids_to_delete = [data['_id'] for data in oldest_data]
#     collection.delete_many({'_id': {'$in': ids_to_delete}})
# print('数据清理成功')
