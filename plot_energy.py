import pandas as pd
from bokeh.plotting import figure, show, output_file
from bokeh.models import DatetimeTickFormatter
from bokeh.io import export_png
from datetime import datetime


df2=pd.read_csv('KNPROVA.csv')
df2['2']=df2['2'].diff()
df=pd.read_csv('pvpanels_production/kn10/production_kn10.csv')

begin = '2015-10-11 00:00:00'
end = '2015-10-11 23:59:00'
df['time']=pd.to_datetime(df['time'])
mask = (df['time'] > begin) & (df['time'] <= end)
df=df.loc[mask]
df.index = df['time']
df3=pd.DataFrame()
df3['value']=df['value'].resample('5Min').mean()
df.reset_index(drop=True, inplace=True)
print(df)
df3.dropna(axis=0,how='any',inplace=True)
print(df3)
df3.to_csv("ciao.csv")
p=figure(x_axis_label='Hours (h)',y_axis_label='Energy (Wh) ',x_axis_type='datetime' ,plot_width=1000,plot_height=500)
date=pd.to_datetime(df2['time'])
p.line(x=date, y=df2['2'],  line_width=2, line_color='red',legend_label='Energia Prodotta')
p.line(x=df3.index, y=df3['value'],  line_width=2, line_color='green' ,legend_label='Energia Consumata')
p.legend.location = "top_right"

p.xaxis.formatter = DatetimeTickFormatter(hours=["%H:%M"]) # Or whatever format you want to use...
export_png(p, filename="plot.png")


