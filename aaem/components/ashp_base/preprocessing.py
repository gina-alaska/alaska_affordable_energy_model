"""
preprocessing.py

    preprocessing functions for Air Source Heat Pumps Base component  
"""
import os.path
from pandas import read_csv
import shutil

## List of raw data files required for wind power preproecssing 
raw_data_files = ['ashp_data.csv',"ashp_perfromance_data.csv"]

## preprocessing functons 
def preprocess_header (ppo):
    """
    """
    return  "# " + ppo.com_id + "ashp data\n"+ \
            ppo.comments_dataframe_divide
            
def preprocess (ppo):
    """"""
    data = read_csv(os.path.join(ppo.data_dir,"ashp_data.csv"),
                        comment = '#',index_col = 0)#.ix[ppo.com_id]

    data = ppo.get_communities_data(data).T
    out_file = os.path.join(ppo.out_dir,"ashp_data.csv")

    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.write('key,value\n')
    fd.close()

    # create data and uncomment this
    data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['ASHP_DATA'] = "ashp_data.csv" # change this
    
    
    shutil.copy(os.path.join(ppo.data_dir,"ashp_perfromance_data.csv"),
                        ppo.out_dir)
    
    ppo.MODEL_FILES['ASHP_PERFROMANCE_DATA'] = "ashp_perfromance_data.csv" 

## list of wind preprocessing functions
preprocess_funcs = [preprocess]
