import eccodes

grib=open('download.grib','rb')
gid=eccodes.codes_grib_new_from_file(grib)
stl1=eccodes.codes_get(gid,'date')
print(stl1)

i_keys = ["dataDate", "shortName",'dataTime']
id = eccodes.codes_index_new_from_file('download.grib', i_keys)
dates = eccodes.codes_index_get(id, "dataDate")
names = eccodes.codes_index_get(id, "shortName")
hours=eccodes.codes_index_get(id,'dataTime')
print(dates,names,hours)

for date in dates:
 eccodes.codes_index_select(id, "dataDate", date)
 for hour in hours:
    eccodes.codes_index_select(id,"dataTime",hour)
    for name in names:
        eccodes.codes_index_select(id, "shortName", name)
        gid = eccodes.codes_new_from_index(id)
        values = eccodes.codes_get_values(gid)
        eccodes.codes_release(gid)
        #if name == "2t":
          #values = values - 273.15
        print (date,hour, name)
        eccodes.codes_release(gid)
#eccodes.codes_index_release(id)