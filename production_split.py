from datetime import datetime
import pandas as pd

df = pd.read_csv('pvpanels_production/kn10/kn10.csv', sep=" ")
df['time']=pd.to_datetime(df["time"],unit='s')
df.to_csv('pvpanels_production/kn10/production_kn10.csv',index=False)

