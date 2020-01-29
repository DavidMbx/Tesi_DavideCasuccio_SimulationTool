import csv
import eccodes
from datetime import datetime

f = open('download.grib')
nomi=[]
date=[]
ore=[]
valori=[]
irrad1=[]
irrad2=[]
n=0

while 1:
   gid = eccodes.codes_grib_new_from_file(f)
   if gid is None:break
   print(eccodes.codes_get(gid,'shortName'),eccodes.codes_get(gid,'dataDate'), eccodes.codes_get(gid,'dataTime'),eccodes.codes_get(gid,'values'))
   nomi.append(eccodes.codes_get(gid,'shortName'))
   date.append(eccodes.codes_get(gid, 'dataDate'))
   ore.append(eccodes.codes_get(gid,'dataTime'))
   if (eccodes.codes_get(gid, 'shortName') == 'ssr' ):
       try:
        if (eccodes.codes_get(gid, 'values')-irrad1[-1]<0):
            valori.append(0)
        else:
            valori.append((eccodes.codes_get(gid, 'values') - irrad1[-1]) / 3600)
       except IndexError:
           valori.append((eccodes.codes_get(gid, 'values') ) / 3600)
       irrad1.append(eccodes.codes_get(gid, 'values'))
   elif ( eccodes.codes_get(gid, 'shortName') == 'ssrd' ):
       try:
           if (eccodes.codes_get(gid, 'values') - irrad2[-1] < 0):
               valori.append(0)
           else:
               valori.append((eccodes.codes_get(gid, 'values') - irrad2[-1]) / 3600)
       except IndexError:
         valori.append((eccodes.codes_get(gid, 'values') ) / 3600)  
       irrad2.append(eccodes.codes_get(gid, 'values'))

   else:
       valori.append(eccodes.codes_get(gid,'values'))
   eccodes.codes_release(gid)
f.close()

for j in range(0, len(valori), 24):

 with open('CS_'+str(date[j])+str(ore[j+1])+'.csv', 'w', newline='') as file:
  writer = csv.writer(file)
  writer.writerow(["time", "aswdifd_s", "aswdir_s", "t_2m", "t_g"])
  for n in range(j,j+24,4):
     if len(str(ore[n+1]))==4:
      ore_str=str(ore[n+1])[:2]+':'+str(ore[n+1])[2:]
     elif len(str(ore[n+1]))==1:
      ore_str=str(ore[n+1])+':00'
     else:
      ore_str = '0'+str(ore[n + 1])[:1] + ':' + str(ore[n + 1])[1:]

     writer.writerow([datetime.strptime(str(date[n]), '%Y%m%d').strftime('%d/%m/%Y')+' '+ore_str,valori[n+3],valori[n+2],valori[n],valori[n+1]])


print(nomi)
print(date)
print(ore)

