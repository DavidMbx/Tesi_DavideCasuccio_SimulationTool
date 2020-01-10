import csv
import eccodes
from datetime import datetime

f = open('download.grib')
nomi=[]
date=[]
ore=[]
valori=[]

while 1:
   gid = eccodes.codes_grib_new_from_file(f)
   if gid is None:break
   keys = ('dataDate', 'dataTime', 'shortName')

   print(eccodes.codes_get(gid,'shortName'),eccodes.codes_get(gid,'dataDate'), eccodes.codes_get(gid,'dataTime'),eccodes.codes_get(gid,'values'))
   nomi.append(eccodes.codes_get(gid,'shortName'))
   date.append(eccodes.codes_get(gid,'dataDate'))
   ore.append(eccodes.codes_get(gid,'dataTime'))
   valori.append(eccodes.codes_get(gid,'values'))


   eccodes.codes_release(gid)
f.close()

with open('prova.csv', 'w', newline='') as file:
 writer = csv.writer(file)
 writer.writerow(["time", "2t", "fal", "stl1", "ssr", "ssrd"])
 for n in range(0,len(ore),5):
     if len(str(ore[n+2]))==4:
      ore_str=str(ore[n+2])[:2]+':'+str(ore[n+2])[2:]
     else :
         ore_str = str(ore[n + 2])[:1] + ':' + str(ore[n + 2])[1:]

     writer.writerow([datetime.strptime(str(date[n]), '%Y%m%d').strftime('%m/%d/%Y')+' '+ore_str,valori[n],valori[n+1],valori[n+2],valori[n+3],valori[n+4]])


print(nomi)
print(date)
print(ore)

