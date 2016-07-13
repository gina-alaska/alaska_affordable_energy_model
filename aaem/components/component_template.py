"""
component_template.py

a template for adding components



"""
import numpy as np
from math import isnan
from pandas import DataFrame,concat,read_csv
import os
import shutil
from yaml import dump, load

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants


## steps for using
### 1) copy this file as component_name.py and go throug this file folloing the 
###    commented instructions
### 2) add new components things to default yaml file
### 3) add the component to __init__ in this directory

# change to component name (i.e. 'residential buildings')
COMPONENT_NAME = "<name>"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        "project details": IMPORT,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        #~ 'start year': 2017,
        }
    
## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>'}
       
## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """
    """
    pass
    
def load_project_details (data_dir):
    """
    load details related to exitign projects
    
    pre:
        data_dir is a directory with  'project_development_timeframes.csv',
        and "project_name_projects.yaml" in it 
    
    post:
        retunrns a dictonary wht the keys 'phase'(str), 
        'proposed capacity'(float), 'proposed generation'(float),
        'distance to resource'(float), 'generation capital cost'(float),
        'transmission capital cost'(float), 'operational costs'(float),
        'expected years to operation'(int),
    """
    try:
        tag = os.path.split(data_dir)[1].split('+')[1]
    except IndexError:
        tag = None
        
    # get the estimated years to operation
    # CHANGE THIS Replace the PROJECT_TYPE with the type of the project
    data_file = os.path.join(data_dir, 'project_development_timeframes.csv')
    data = read_csv(data_file, comment = '#',
                    index_col=0, header=0)[PROJECT_TYPE]

    if tag is None:
        # if no data make some
        yto = int(round(float(data['Reconnaissance'])))
        return {'phase': 'Reconnaissance',
                'proposed capacity': UNKNOWN,
                'proposed generation': UNKNOWN,
                'distance to resource': UNKNOWN,
                'generation capital cost': UNKNOWN,
                'transmission capital cost': UNKNOWN,
                'operational costs': UNKNOWN,
                'expected years to operation': yto,
                }
    
    # CHANGE THIS
    with open(os.path.join(data_dir, "COPMPONENT_PROJECTS.yaml"), 'r') as fd:
        dets = load(fd)[tag]
    
    # correct number years if nessary
    yto = dets['expected years to operation']
    if yto == UNKNOWN:
        try:
            yto = int(round(float(data[dets['phase']])))
        except TypeError:
            yto = 0
        dets['expected years to operation'] = yto
    dets['expected years to operation'] = int(yto)
    
    return dets
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'project details': load_project_details}# fill in
    
## preprocessing functons 
def preprocess_header (ppo):
    """
    """
    return  "# " + ppo.com_id + " compdata data\n"+ \
            ppo.comments_dataframe_divide
    
def preprocess (ppo):
    """
    
    """
    #CHANGE THIS
    out_file = os.path.join(ppo.out_dir,"comp_data.csv")

    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.close()

    # create data and uncomment this
    #~ data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['COMP_DATA'] = "comp_data.csv" # CHANGE THIS

## preprocess the existing projects
def preprocess_existing_projects (ppo):
    """
    preprocess data related to existing projects
    
    pre:
        ppo is a is a Preprocessor object. "wind_projects.csv" and 
        'project_development_timeframes.csv' exist in the ppo.data_dir 
    post:
        data for existing projets is usable by model
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
    
    with open(os.path.join(ppo.out_dir,"wind_projects.yaml"),'w') as fd:
        if len(p_data) != 0:
            fd.write(dump(p_data,default_flow_style=False))
        else:
            fd.write("")
        
    ## CHANGE THIS
    ppo.MODEL_FILES['COMPONENT_PROJECTS'] = "COMPONENT_PROJECTS.yaml"
    shutil.copy(os.path.join(ppo.data_dir,'project_development_timeframes.csv'), 
                ppo.out_dir)
    ppo.MODEL_FILES['TIMEFRAMES'] = 'project_development_timeframes.csv'
    #~ print ppo.MODEL_FILES
    return projects

## List of raw data files required for wind power preproecssing 
raw_data_files = ["COMPONENT_PROJECTS.csv",
                  'project_development_timeframes.csv']# fillin

## list of wind preprocessing functions
preprocess_funcs = [preprocess]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []
    
## component summary
def component_summary (coms, res_dir):
    """
    """
    pass

## list of prerequisites for module
prereq_comps = [] ## FILL in if needed

#   do a find and replace on ComponentName to name of component 
# (i.e. 'ResidentialBuildings')
class ComponentName (AnnualSavings):
    """
    """
    def __init__ (self, community_data, forecast, 
                        diag = None, prerequisites = {}):
        """
        Class initialiser

        pre:
            community_data is a CommunityData object. diag (if provided) should 
        be a Diagnostics object
        post:
            the model can be run
        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.forecast = forecast
        self.cd = community_data.get_section('community')
        
        self.comp_specs["start year"] = self.cd['current year'] + \
            self.comp_specs["project details"]['expected years to operation']
       
        self.comp_specs = community_data.get_section(COMPONENT_NAME)
        self.component_name = COMPONENT_NAME

        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
        
        ### ADD other intiatzation stuff  
        ### load prerequisites in the following function
        ### if there are no prerequisites you can delete this and the 
        ### load_prerequisite_variables function
        self.load_prerequisite_variables(prerequisites)
        
    def load_prerequisite_variables (self, comps):
        """
        load variables from prerequisites
        
        pre:
             prerequisites: dictonary of componentes
        """
        # LOAD anything needed from the components passed as input
        # WRITE this
        pass
        
    def run (self):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        if self.cd["model electricity"]:
            # change these below
            self.calc_baseline_kWh_consumption()
            self.calc_retrofit_kWh_consumption()
            self.calc_savings_kWh_consumption()
            # NOTE*:
            #   some times is it easier to find the savings and use that to
            # calculate the retro fit values. If so, flip the function calls 
            # around, and change the functionality of
            # self.calc_savings_kWh_consumption() below
            
        
        if self.cd["model heating fuel"]:
            # change these below
            self.calc_baseline_fuel_consumption()
            self.calc_retrofit_fuel_consumption()
            self.calc_savings_fuel_consumption()
            # see NOTE*
        
        if self.cd["model financial"]:
            # AnnualSavings functions (don't need to write)
            self.get_diesel_prices()
            
            # change these below
            self.calc_capital_costs()
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            # AnnualSavings functions (don't need to write)
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
 
    # Make this do stuff
    def calc_baseline_kWh_consumption (self):
        """ Function doc """
        self.baseline_kWh_consumption = np.zeros(self.project_life)
    
    # Make this do stuff
    def calc_retrofit_kWh_consumption (self):
        """ Function doc """
        self.retrofit_kWh_consumption = np.zeros(self.project_life)
    
    # use this or change it see NOTE* above
    def calc_savings_kWh_consumption(self):
        """
        calculate the savings in electricity consumption(in kWh) for a community
        
        pre:
            self.baseline_kWh_consumption and self.retrofit_kWh_consumption
        should be array of the same length or scaler numbers (units kWh)
    
        post:
            self.savings_kWh_consumption is an array or scaler of numbers 
        (units kWh)
        """
        self.savings_kWh_consumption = self.baseline_kWh_consumption -\
                                       self.retrofit_kWh_consumption
        
    # Make this do stuff
    def calc_baseline_fuel_consumption (self):
        """ Function doc """
        self.baseline_fuel_consumption = np.zeros(self.project_life)
     
    # Make this do stuff
    def calc_retrofit_fuel_consumption (self):
        """ Function doc """
        self.retrofit_fuel_consumption = np.zeros(self.project_life)
        
    # use this or change it see NOTE* above
    def calc_savings_fuel_consumption(self):
        """
        calculate the savings in fuel consumption(in mmbtu) for a community
        
        pre:
            self.baseline_fuel_consumption and self.retrofit_fue;_consumption
        should be array of the same length or scaler numbers (units mmbtu)
    
        post:
            self.savings_fuel_consumption is an array or scaler of numbers 
        (units mmbtu)
        """
        self.savings_fuel_consumption = self.baseline_fuel_consumption -\
                                        self.retrofit_fuel_consumption
    
    
    # Make this do stuff
    def calc_capital_costs (self):
        """ Function Doc"""
        self.capital_costs = np.nan
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        """
        price = 0 
        self.annual_electric_savings = self.savings_kWh_consumption * price
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        """
        price = 0 
        self.annual_heating_savings = self.savings_fuel_consumption * price

component = ComponentName

def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../test_case/input_data/","../test_case/baseline_results/config_used.yaml")
    fc = Forecast(manley_data)
    comp = ComponentName(manley_data, fc)
    comp.run()
    return comp,fc # return the object for further testing
