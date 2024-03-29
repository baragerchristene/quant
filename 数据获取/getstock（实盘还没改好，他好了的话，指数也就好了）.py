import akshare as ak
import pandas as pd
import datetime
from pymongo import MongoClient


client = MongoClient(
    'mongodb://wth000:wth000@43.159.47.250:27017/dbname?authSource=wth000')
db = client['wth000']
# 输出的表为截止日期
name = '实盘STOCK'
collection = db[f"{name}"]
# 获取当前日期
current_date = datetime.datetime.now()
# 读取180天内的数据，这里面还得排除掉节假日,初始数据建议220,实际更新的时候更新15天就行
# date_ago = current_date - datetime.timedelta(days=220)
date_ago = current_date - datetime.timedelta(days=15)
current_date = current_date - datetime.timedelta(days=10)

start_date = date_ago.strftime('%Y%m%d')  # 要求格式"19700101"
end_date = current_date.strftime('%Y%m%d')

# 从akshare获取A股主板股票的代码和名称
df = ak.stock_zh_a_spot_em()
# 过滤掉ST股票
df = df[~df['名称'].str.contains('ST')]
# 过滤掉退市股票
df = df[~df['名称'].str.contains('退')]
# 迭代每只股票，获取每天的前复权日k数据
df = df[df['代码'].str.startswith(
    ('60', '000', '001'))][['代码', '名称']]
# 遍历目标指数代码，获取其分钟K线数据
for code in df['代码']:
    latest = list(collection.find(
        {"代码": float(code)}, {"timestamp": 1}).sort("timestamp", -1).limit(1))
    print(latest)
    if len(latest) == 0:
        upsert_docs = True
        start_date_query = start_date
    else:
        upsert_docs = False
        latest_timestamp = latest[0]["timestamp"]
        start_date_query = datetime.datetime.fromtimestamp(
            latest_timestamp).strftime('%Y%m%d')

    k_data = ak.stock_zh_a_hist(
        symbol=code, start_date=start_date_query, end_date=end_date, adjust="hfq")
    k_data_true = ak.stock_zh_a_hist(
        symbol=code, start_date=start_date_query, end_date=end_date, adjust="")
    try:
        k_data_true = k_data_true[['日期', '开盘']].rename(columns={'开盘': '真实价格'})
        k_data = pd.merge(k_data, k_data_true, on='日期', how='left')
        k_data['代码'] = float(code)
        k_data["成交量"] = k_data["成交量"].apply(lambda x: float(x))
        k_data['timestamp'] = k_data['日期'].apply(lambda x: float(
            datetime.datetime.strptime(x, '%Y-%m-%d').timestamp()))
        k_data = k_data.sort_values(by=["代码", "日期"])
        docs_to_update = k_data.to_dict('records')
        if upsert_docs:
            print(f"{name}({code}) 新增数据")
            try:
                collection.insert_many(docs_to_update)
            except Exception as e:
                pass
        else:
            bulk_insert = []
            for doc in docs_to_update:
                if doc["timestamp"] > latest_timestamp:
                    # 否则，加入插入列表
                    bulk_insert.append(doc)
                if doc["timestamp"] == latest_timestamp:
                    try:
                        collection.update_many({"代码": doc["代码"], "日期": doc["日期"]}, {
                            "$set": doc}, upsert=True)
                    except Exception as e:
                        pass
        # 执行批量插入操作
        if bulk_insert:
            try:
                collection.insert_many(bulk_insert)
            except Exception as e:
                pass
    except:
        print(f"{name}({code}) 已停牌")
print('任务已经完成')
