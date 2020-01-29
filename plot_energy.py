import pandas as pd
from bokeh.plotting import figure, show, output_file
from bokeh.models import DatetimeTickFormatter
from bokeh.io import export_png


df=pd.read_csv('prova.csv')
print(df)
p=figure(x_axis_label='Hours',y_axis_label='Energy',x_axis_type='datetime' ,plot_width=1000,plot_height=500)
date=pd.to_datetime(df['time'])
p.line(x=date, y=df['2'],  line_width=2)
p.xaxis.formatter = DatetimeTickFormatter(hours=["%H:%M"]) # Or whatever format you want to use...
export_png(p, filename="plot.png")

