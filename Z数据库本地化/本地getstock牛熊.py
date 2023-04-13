import akshare as ak
import pandas as pd
import datetime

start_date = '20060101'  # 要求格式"19700101"
end_date = '20090101'  # 要求格式"19700101"
# 从akshare获取A股主板股票的代码和名称
stock_info_df = ak.stock_zh_a_spot_em()
# 过滤掉ST股票
stock_info_df = stock_info_df[~stock_info_df['名称'].str.contains('ST')]

# 创建一个空的DataFrame用于存储数据
df = pd.DataFrame()

# 迭代每只股票，获取每天的前复权日k数据
for code in stock_info_df['代码']:
    if code.startswith(('60', '000', '001')):
        k_data = ak.stock_zh_a_hist(
            symbol=code, start_date=start_date, adjust="qfq")
        k_data['代码'] = float(code)
        try:
            # 将数据存储到df中
            df = pd.concat([df, k_data], ignore_index=True)
            print(f"任务执行中")
        except:
            print(f"({code}) 已停牌")
            continue


# 过滤掉停牌的股票数据
df = df.dropna()

# 将df存储为csv文件
df.to_csv('stock牛熊.csv', index=False)
print('任务已经完成')
