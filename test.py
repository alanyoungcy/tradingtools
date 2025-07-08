import  tushare  as  ts

ts.set_token("d2b02153c3479c4f0c0d755f2d52230741ea2976f28425c53c002911")  # 个人口令，使用一次即可。
# 获取贵州茅台数据, 默认最近两年半并按日期降序排列
# df = ts.get_hist_data('600519')  # "600519" 股票的交易代码
# print(df)

# 获得最近的交易数据
pro = ts.pro_api() # 初始化接口
df = pro.daily()  #
print(df.head(100))
print(df.shape)