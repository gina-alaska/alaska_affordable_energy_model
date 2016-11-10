"""
preprocessing.py

    prporcessing for this component is elsewhere 
"""
## List of raw data files required for wind power preproecssing 
raw_data_files = ['project_development_timeframes.csv']

#~ ## preprocessing functons 
# diesel preprocessing is in preprocessor.py
    
## list of wind preprocessing functions
#~ preprocess_funcs = [preprocess]

## preprocess the existing projects
### This function is called differently from the other preprocessor functions,
### so it does not need to be added to preprocess_funcs
#~ def preprocess_existing_projects (ppo):
    #~ """
    #~ preprocess data related to existing projects
    
    #~ pre:
        #~ ppo is a is a Preprocessor object. "wind_projects_potential.csv" and 
        #~ 'project_development_timeframes.csv' exist in the ppo.data_dir 
    #~ post:
        #~ data for existing projets is usable by model
    #~ """
    #~ return
    #~ projects = []
    #~ p_data = {}
    
    #~ ## CHANGE THIS
    #~ project_data = read_csv(os.path.join(ppo.data_dir,"COMPONENT_PROJECTS.csv"),
                           #~ comment = '#',index_col = 0)
    
    #~ project_data = DataFrame(project_data.ix[ppo.com_id])
    #~ if len(project_data.T) == 1 :
        #~ project_data = project_data.T

    #~ ## FILL IN LOOP see function in wind _power.py for an example
    #~ for p_idx in range(len(project_data)):
       #~ pass
    
    #~ with open(os.path.join(ppo.out_dir,"wind_projects_potential.yaml"),'w') as fd:
        #~ if len(p_data) != 0:
            #~ fd.write(dump(p_data,default_flow_style=False))
        #~ else:
            #~ fd.write("")
        
    #~ ## CHANGE THIS
    #~ ppo.MODEL_FILES['COMPONENT_PROJECTS'] = "COMPONENT_PROJECTS.yaml"
    #~ shutil.copy(os.path.join(ppo.data_dir,'project_development_timeframes.csv'), 
                #~ ppo.out_dir)
    #~ ppo.MODEL_FILES['TIMEFRAMES'] = 'project_development_timeframes.csv'
    #~ #print ppo.MODEL_FILES
    #~ return projects

