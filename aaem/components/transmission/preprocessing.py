"""
Transmission Preprocessing 
--------------------------

preprocessing functions for The Transmission component  

"""
import os.path
from pandas import read_csv
import numpy as np

## List of raw data files required for wind power preproecssing 
raw_data_files = [#"transmission_projects.csv",
                  'project_development_timeframes.csv',
                  'transmission_distances.csv',
                  ]

## preprocessing functons 
def preprocess_header (ppo):
    """Generate preprocesed data file header
    
    Parameters
    ----------
        ppo: aaem.prerocessor.Preprocessor
            a preprocessing object
            
    Returns
    ------- 
        String of header info
    """
    return  "# " + ppo.com_id + " Transmission data\n"+ \
            ppo.comments_dataframe_divide
    
def preprocess (ppo):
    """preprocess data in transmission_data.csv
    
    Parameters
    ----------
    ppo: preprocessor.Proprocessor
        a preprocessor object
        

    """
    #CHANGE THIS
    out_file = os.path.join(ppo.out_dir,"transmission_data.csv")

    data = read_csv(os.path.join(ppo.data_dir,'transmission_distances.csv'),
                    comment = '#',index_col = 0)
                    
    
    #~ try:
    data = ppo.get_communities_data(data)
    #~ except KeyError:
        #~ data
    
    #~ print data
    try:
        max_savings = float(data['Maximum savings ($/kWh)'])
        nearest_comm = data['Nearest Community with Lower Price Power']
        nearest_comm = str(nearest_comm.values[0])
        if 'nan' == nearest_comm:
            nearest_comm = ''
        distance = float(data['Distance to Community'])
    except TypeError:
        max_savings = np.nan
        nearest_comm = np.nan
        distance = np.nan
    
    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.write('key,value\n')
    fd.write('Maximum savings ($/kWh),' + str(max_savings) +'\n')
    fd.write('Nearest Community with Lower Price Power,' \
                                        + str(nearest_comm) +'\n')
    fd.write('Distance to Community,' + str(distance ) +'\n')
    fd.close()
    
    # create data and uncomment this
    #~ data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['TRANSMISSION_DATA'] = "transmission_data.csv" # CHANGE THIS
    
## list of wind preprocessing functions
preprocess_funcs = [preprocess]



