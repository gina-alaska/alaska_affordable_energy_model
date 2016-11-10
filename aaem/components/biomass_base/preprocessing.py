"""
preprocessing.py

    preprocessing functions for Biomass - Base component  
"""
import os.path
from pandas import read_csv
import numpy as np

## List of raw data files required for wind power preproecssing 
raw_data_files = ['biomass_resource_data.csv']

## preprocessing functons 
def preprocess_header (ppo):
    """
    pre: 
        ppo is a preprocessor object
    post:
        returns the biomass header
    """
    return  "# " + ppo.com_id + " biomass data\n"+ \
            "# biomass data from biomass_data.csv preprocessed into a \n" +\
            "# based on the row for the given community \n" +\
            ppo.comments_dataframe_divide
    
def preprocess (ppo):
    """
    preprocess biomass data
    pre: 
        ppo is a preprocessor object
    post:
        saves "biomass_data.csv", and updates MODEL_FILES
    """
    try:
        data = read_csv(os.path.join(ppo.data_dir,"biomass_resource_data.csv"),
                        comment = '#',index_col = 0).ix[ppo.com_id]
    except KeyError:
        data = read_csv(os.path.join(ppo.data_dir,"biomass_resource_data.csv"),
                        comment = '#',index_col = 0).ix[0]
        data.ix[:] = np.nan
        
                        
    out_file = os.path.join(ppo.out_dir,"biomass_data.csv")

    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.write("key,value\n")
    fd.close()

    # create data and uncomment this
    data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['BIOMASS_DATA'] = "biomass_data.csv" # change this

## list of wind preprocessing functions
preprocess_funcs = [preprocess]
