"""
preprocessing.py

    preprocessing functions for Biomass - Pellet component  
"""
import os.path
from pandas import read_csv
import aaem.components.biomass_base as bmb
from copy import deepcopy

raw_data_files = deepcopy(bmb.raw_data_files) + ["road_system.csv"]

def preprocess_road_system_header(ppo):
    """
    pre: 
        ppo is a preprocessor object
    post:
        returns the road header
    """
    return  "# " + ppo.com_id + " road system data\n"+ \
            "# is community on road system or in south east \n" +\
            ppo.comments_dataframe_divide

def preprocess_road_system (ppo):
    """
    preprocess road_system data
    pre: 
        ppo is a preprocessor object
    post:
        saves "biomass_data.csv", and updates MODEL_FILES
    """
    data = read_csv(os.path.join(ppo.data_dir,"road_system.csv"),
                        comment = '#',index_col = 0)
                        
    data = ppo.get_communities_data(data)
    #~ print data.T
    data = data.values[0][0]
    
                    
    out_file = os.path.join(ppo.out_dir,"road_system.csv")
    
    fd = open(out_file,'w')
    fd.write(preprocess_road_system_header(ppo))
    fd.write("key,value\n")
    fd.write("On Road/SE," + data + '\n')
    #~ print "a"
    fd.close()

    # create data and uncomment this
    #~ data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['road_system'] = "road_system.csv" # change this


## list of wind preprocessing functions
preprocess_funcs = [deepcopy(bmb.preprocess),preprocess_road_system]
