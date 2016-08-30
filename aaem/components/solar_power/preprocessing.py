"""
preprocessing.py

    preprocessing functions for Solar Power component  
"""
import os.path
from pandas import read_csv
import numpy as np

## List of raw data files required for wind power preproecssing 
raw_data_files = ['solar_data.csv', 'solar_data_existing.csv',
                    "wind_data_existing.csv"]

## preprocessing functons 
def preprocess_header (ppo):
    """
    """
    return  "# " + ppo.com_id + " solar power data\n"+ \
            ppo.comments_dataframe_divide
    

def preprocess (ppo):
    """"""
    data = read_csv(os.path.join(ppo.data_dir,"solar_data.csv"),
                        comment = '#',index_col = 0).ix[ppo.com_id]
    try:
        existing = read_csv(os.path.join(ppo.data_dir,"solar_data_existing.csv"),
                        comment = '#',index_col = 0).ix[ppo.com_id]
        existing = existing['Installed Capacity (kW)']
        if np.isnan(existing):
            existing = 0
    except KeyError:
        existing = 0 
    
    try:
        wind_cap = read_csv(os.path.join(ppo.data_dir,
                                "wind_data_existing.csv"),
                            comment = '#',index_col = 0).ix[ppo.com_id]
        wind_cap = wind_cap['Rated Power (kW)']
        if np.isnan(wind_cap):
            wind_cap = 0
    except (IOError,KeyError):
        wind_cap = 0 
    
    val =  data['Output per 10kW Solar PV']
    #~ return
    out_file = os.path.join(ppo.out_dir,"solar_power_data.csv")

    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.write("key,value\n")
    fd.write("Installed Capacity," + str(existing) + '\n')
    fd.write("Wind Capacity," + str(wind_cap) + '\n')
    fd.write('Output per 10kW Solar PV,' + str(val) + '\n')
    #~ fd.write("HR Opperational,True\n")
    fd.close()

    # create data and uncomment this
    #~ data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['SOLAR_DATA'] = "solar_power_data.csv"

## list of wind preprocessing functions
preprocess_funcs = [preprocess]
