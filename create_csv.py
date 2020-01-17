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
   print(eccodes.codes_get(gid,'shortName'),eccodes.codes_get(gid,'dataDate'), eccodes.codes_get(gid,'dataTime'),eccodes.codes_get(gid,'values'))
   nomi.append(eccodes.codes_get(gid,'shortName'))
   date.append(eccodes.codes_get(gid, 'dataDate'))
   ore.append(eccodes.codes_get(gid,'dataTime'))
   if (eccodes.codes_get(gid, 'shortName') == '2t' or eccodes.codes_get(gid, 'shortName') == 'stl1' ):
       valori.append(eccodes.codes_get(gid, 'values')-273)
   else:
       valori.append(eccodes.codes_get(gid,'values'))
   eccodes.codes_release(gid)
f.close()

for j in range(0, len(valori), 24):

 with open('Caserta_'+str(date[j])+'_'+str(ore[j+1])+'.csv', 'w', newline='') as file:
  writer = csv.writer(file)
  writer.writerow(["time", "2t", "stl1", "ssr", "ssrd"])
  for n in range(j,j+24,4):
     if len(str(ore[n+1]))==4:
      ore_str=str(ore[n+1])[:2]+':'+str(ore[n+1])[2:]
     elif len(str(ore[n+1]))==1:
      ore_str=str(ore[n+1])+':00'
     else:
      ore_str = str(ore[n + 1])[:1] + ':' + str(ore[n + 1])[1:]

     writer.writerow([datetime.strptime(str(date[n]), '%Y%m%d').strftime('%d/%m/%Y')+' '+ore_str,valori[n],valori[n+1],valori[n+2],valori[n+3]])


print(nomi)
print(date)
print(ore)

