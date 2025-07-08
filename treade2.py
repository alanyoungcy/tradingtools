import matplotlib.pyplot as plt
import mplfinance as mpf  # Use the new API
import tushare as ts
import pandas as pd
import numpy as np  # Added for regression calculation

ts.set_token("d2b02153c3479c4f0c0d755f2d52230741ea2976f28425c53c002911")  # 个人口令，使用一次即可。

pro = ts.pro_api()
code = '600004.SH'
df = pro.daily(ts_code=code, start_date='20191201', end_date='20250701')

# 原数据是按日期降序， 将其调整为按日期升序
df = df.sort_values(by='trade_date', ascending=True)

# 转换日期格式并设置为索引
df['trade_date'] = pd.to_datetime(df['trade_date'])
df.set_index('trade_date', inplace=True)

# 重命名列以符合mplfinance要求 (Open, High, Low, Close, Volume)
df = df.rename(columns={
    'open': 'Open',
    'high': 'High', 
    'low': 'Low',
    'close': 'Close',
    'vol': 'Volume'
})

# 计算基于收盘价的线性回归线
# 创建x轴数据（天数序列）
x = np.arange(len(df))
y = df['Close'].values

# 计算线性回归系数 (y = ax + b)
coefficients = np.polyfit(x, y, 1)  # 1表示一次多项式（线性）
regression_line = np.poly1d(coefficients)(x)

# 创建回归线的DataFrame，索引与原数据一致
regression_df = pd.Series(regression_line, index=df.index)

# 创建附加绘图对象（回归线）
addplot = mpf.make_addplot(regression_df, 
                          color='blue', 
                          width=2, 
                          linestyle='--',
                          alpha=0.8,
                          secondary_y=False)

# 使用新的mplfinance API绘制K线图
mpf.plot(df, 
         type='candle',           # 蜡烛图类型
         style='charles',         # 样式
         title=f'{code} - 带回归线的K线图',  # 图表标题
         ylabel='Price',         # Y轴标签
         volume=True,            # 显示成交量
         figsize=(12, 9),        # 图表大小
         addplot=addplot)        # 添加回归线

# 打印回归线信息
slope, intercept = coefficients
print(f"回归线方程: y = {slope:.4f}x + {intercept:.2f}")
print(f"斜率: {slope:.4f} (每日平均价格变化)")
if slope > 0:
    print("趋势: 上升")
elif slope < 0:
    print("趋势: 下降")
else:
    print("趋势: 平稳")