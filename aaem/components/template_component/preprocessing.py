"""
Template Component Preprocessing 
--------------------------------

Example preprocessing functions.

"""
import os.path
from pandas import read_csv
import ymal

# fill in with files used
# find/replace "COMPONENT_PROJECTS.csv"
## List of raw data files required for wind power preproecssing 
raw_data_files = ["COMPONENT_PROJECTS.csv",
                  'project_development_timeframes.csv']

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
    return  "# " + ppo.com_id + " compdata data\n"+ \
            ppo.comments_dataframe_divide
    
## UPADTE
def preprocess (ppo):
    """preprocess  data in <FILES>
    
    Parameters
    ----------
    ppo: preprocessor.Proprocessor
        a preprocessor object
        
    Returns
    -------
    list
        project names
    
    """
    #CHANGE THIS
    out_file = os.path.join(ppo.out_dir,"comp_data.csv")

    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.close()

    # create data and uncomment this
    #~ data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['COMP_DATA'] = "comp_data.csv" # CHANGE THIS
    

## list of preprocessing functions
preprocess_funcs = [preprocess]

# find/replace COMPONENT_PROJECTS.yaml
## preprocess the existing projects
### This function is called differently from the other preprocessor functions,
### so it does not need to be added to preprocess_funcs
def preprocess_existing_projects (ppo):
    """preprocess data related to existing projects
    
    Parameters
    ----------
    ppo: preprocessor.Proprocessor
        a preprocessor object
        
    Returns
    -------
    list
        project names
    
    """
    projects = []
    p_data = {}
    
    ## CHANGE THIS
    project_data = read_csv(os.path.join(ppo.data_dir,"COMPONENT_PROJECTS.csv"),
                           comment = '#',index_col = 0)
    
    project_data = DataFrame(project_data.ix[ppo.com_id])
    if len(project_data.T) == 1 :
        project_data = project_data.T

    ## FILL IN LOOP see function in wind _power.py for an example
    for p_idx in range(len(project_data)):
       pass
    
    with open(os.path.join(ppo.out_dir,"COMPONENT_PROJECTS.yaml"),'w') as fd:
        if len(p_data) != 0:
            fd.write(yaml.dump(p_data,default_flow_style=False))
        else:
            fd.write("")
        
    ## CHANGE THIS
    ppo.MODEL_FILES['COMPONENT_PROJECTS'] = "COMPONENT_PROJECTS.yaml"
    shutil.copy(os.path.join(ppo.data_dir,'project_development_timeframes.csv'), 
                ppo.out_dir)
    ppo.MODEL_FILES['TIMEFRAMES'] = 'project_development_timeframes.csv'
    #~ print ppo.MODEL_FILES
    return projects


