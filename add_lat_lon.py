from pandas import read_csv
import sys
import numpy as np

## http://geonames.usgs.gov/domestic/download_data.htm

community_list, gnis_data, outfile = sys.argv[1:4]

community_list = read_csv(community_list, comment = '#')
gnis_data = read_csv(gnis_data, delimiter = '|')



community_list['LAT'] = np.nan
community_list['LONG'] = np.nan
 
for c in community_list.index:
    index = gnis_data[gnis_data.columns[0]] == community_list['GNIS'][c]
    community_list['LAT'][c] = gnis_data['PRIM_LAT_DEC'][index]
    community_list['LONG'][c] = gnis_data['PRIM_LONG_DEC'][index]
 
 
 
community_list[["Model ID","Community","Energy Region","LAT",
                "LONG","GNIS","FIPS","Alias"]].to_csv(outfile, index = False)




