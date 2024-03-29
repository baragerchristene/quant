import math
import pandas as pd
import os

name = 'BTC'# 分钟k的收益反向越低于1越好，这个是纯粹的做空策略
# name = 'COIN'
# name = 'STOCK'

# 获取当前.py文件的绝对路径
file_path = os.path.abspath(__file__)
# 获取当前.py文件所在目录的路径
dir_path = os.path.dirname(file_path)
# 获取当前.py文件所在目录的上四级目录的路径
dir_path = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(dir_path))))
file_path = os.path.join(dir_path, f'{name}指标.csv')
df = pd.read_csv(file_path)

# 去掉n日后总涨跌幅大于百分之三百的噪音数据
for n in range(1, 9):
    df = df[df[f'{n}日后总涨跌幅（未来函数）'] <= 300*(1+n*0.2)]

code_count = len(df['代码'].drop_duplicates())
print("标的数量", code_count)
if 'btc' in name.lower():
    # 下降通道做多（名义盈利越多，说明市场上涨的越好）
    # for n in range(6, 13):  # 计算未来n日涨跌幅
    #     df = df[df[f'{n*10}日最高开盘价比值'] <= 1-n*0.001].copy()
    # 上升通道做空（名义亏损越多，说明市场下降的越好）
    for n in range(1, 6):  # 计算未来n日涨跌幅
        df = df[df[f'{n*10}日最低开盘价比值'] >= 1+n*0.001].copy()

if 'coin' in name.lower():
    # 成交额过滤劣质股票
    df = df[df[f'昨日成交额'] >= 1000000].copy()
    # 熊市过滤
    df = df[df['SMA120开盘比值'] <= 0.5].copy()
    for n in range(1, 10):  # 计算未来n日涨跌幅
        df = df[df[f'{n*10}日最低开盘价比值'] >= 1+n*0.01].copy()
    # 开盘价过滤高滑点股票
    df = df[df[f'开盘'] >= 0.00000500].copy()
if 'stock' in name.lower():
    # 熊市过滤
    df = df[df['SMA120开盘比值'] <= 0.5].copy()
    for n in range(1, 10):  # 计算未来n日涨跌幅
        df = df[df[f'{n*10}日最低开盘价比值'] >= 1+n*0.01].copy()
    df = df[
        (df['开盘收盘幅'] <= 8)
        &
        (df['开盘收盘幅'] >= 0)
        &
        (df['真实价格'] >= 4)
    ]
    print('测试标的为股票类型，默认高开百分之八无法买入')

# 将交易标的细节输出到一个csv文件
trading_detail_filename = f'{name}交易标的细节.csv'
df.to_csv(trading_detail_filename, index=False)

# 假设开始时有1元资金,实操时每个月还得归集一下资金，以免收益不平均
cash_balance = 1
# 用于记录每日的资金余额
daily_cash_balance = {}
if 'stock' in name.lower():
    n = 9  # 设置持仓周期
    m = 0.003  # 设置手续费
if 'coin' in name.lower():
    n = 6  # 设置持仓周期
    m = 0.005  # 设置手续费
if 'btc' in name.lower():
    n = 6  # 设置持仓周期
    m = -0.0001  # 设置手续费

df_strategy = pd.DataFrame(columns=['日期', '执行策略'])
df_daily_return = pd.DataFrame(columns=['日期', '收益率'])

cash_balance_list = []
# 记录每个交易日是否执行了策略，并输出到csv文件中
for date, group in df.groupby('日期'):
    # 如果当日没有入选标的，则单日收益率为0
    if group.empty:
        daily_return = 0
    else:
        daily_return = ((group[f'{n}日后总涨跌幅（未来函数）'] +
                        1).mean()*(1-m)-1)/n  # 计算平均收益率
    df_daily_return = pd.concat(
        [df_daily_return, pd.DataFrame({'日期': [date], '收益率': [daily_return]})])
    # 更新资金余额并记录每日资金余额
    cash_balance *= (1 + daily_return)
    daily_cash_balance[date] = cash_balance
    cash_balance_list.append(cash_balance)  # 添加每日资金余额到列表中
df_cash_balance = pd.DataFrame(
    {'日期': list(daily_cash_balance.keys()), '资金余额': list(daily_cash_balance.values())})
df_strategy_and_return = pd.merge(df_daily_return, df_cash_balance, on='日期')
# 输出每日执行策略和净资产收益率到csv文件
df_strategy_and_return.to_csv(f'{name}每日策略和资产状况.csv', index=False)
