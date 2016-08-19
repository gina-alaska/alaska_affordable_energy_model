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
COMPONENT_NAME = "diesel efficiency"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        "project details": {'phase': 'Reconnaissance',
                            'capital costs': UNKNOWN,
                            'operational costs': UNKNOWN,
                            'expected years to operation': 3,
                            },
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'efficiency improvment': 1.1,
        'o&m costs': {150: 84181.00,
                      360: 113410.00,
                      600: 134434.00,
                      'else':103851.00 }
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
#~ def process_data_import(data_dir):
    #~ """
    #~ """
    #~ pass
    
#~ def load_project_details (data_dir):
    #~ """
    #~ load details related to exitign projects
    
    #~ pre:
        #~ data_dir is a directory with  'project_development_timeframes.csv',
        #~ and "project_name_projects.yaml" in it 
    
    #~ post:
        #~ retunrns a dictonary wht the keys 'phase'(str), 
        #~ 'proposed capacity'(float), 'proposed generation'(float),
        #~ 'distance to resource'(float), 'generation capital cost'(float),
        #~ 'transmission capital cost'(float), 'operational costs'(float),
        #~ 'expected years to operation'(int),
    #~ """
    #~ try:
        #~ tag = os.path.split(data_dir)[1].split('+')
        #~ project_type = tag[1]
        #~ tag = tag[1] + '+' +tag[2]
        #~ if project_type != PROJECT_TYPE:
            #~ tag = None
    #~ except IndexError:
        #~ tag = None
        
    #~ # TODO fix no data in file?
    #~ # data_file = os.path.join(data_dir, 'project_development_timeframes.csv')
    #~ #data = read_csv(data_file, comment = '#',
                    #~ # index_col=0, header=0)[PROJECT_TYPE]

    #~ if tag is None:
        #~ # if no data make some
        #~ yto = 3#int(round(float(data['Reconnaissance'])))
        #~ return {'phase': 'Reconnaissance',
                #~ 'capital costs': UNKNOWN,
                #~ 'operational costs': UNKNOWN,
                #~ 'expected years to operation': yto,
                #~ }
    
    #~ # CHANGE THIS
    
    #~ with open(os.path.join(data_dir, "COPMPONENT_PROJECTS.yaml"), 'r') as fd:
        #~ dets = load(fd)[tag]
    
    #~ # correct number years if nessary
    #~ yto = dets['expected years to operation']
    #~ if yto == UNKNOWN:
        #~ try:
            #~ yto = int(round(float(data[dets['phase']])))
        #~ except TypeError:
            #~ yto = 0
        #~ dets['expected years to operation'] = yto
    #~ dets['expected years to operation'] = int(yto)
    
    #~ return dets
    
#~ ## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {}#'project details': load_project_details}# fill in
    
## preprocessing functons 
#~ def preprocess_header (ppo):
    #~ """
    #~ """
    #~ return  "# " + ppo.com_id + " compdata data\n"+ \
            #~ ppo.comments_dataframe_divide
    
#~ def preprocess (ppo):
    #~ """
    
    #~ """
    #~ #CHANGE THIS
    #~ out_file = os.path.join(ppo.out_dir,"comp_data.csv")

    #~ fd = open(out_file,'w')
    #~ fd.write(preprocess_header(ppo))
    #~ fd.close()

    #~ # create data and uncomment this
    #~ data.to_csv(out_file, mode = 'a',header=False)
    
    #~ ppo.MODEL_FILES['COMP_DATA'] = "comp_data.csv" # CHANGE THIS
    
## list of wind preprocessing functions
#~ preprocess_funcs = []#preprocess]

## preprocess the existing projects
### This function is called differently from the other preprocessor functions,
### so it does not need to be added to preprocess_funcs
#~ def preprocess_existing_projects (ppo):
    #~ """
    #~ preprocess data related to existing projects
    
    #~ pre:
        #~ ppo is a is a Preprocessor object. "wind_projects.csv" and 
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
    
    #~ with open(os.path.join(ppo.out_dir,"wind_projects.yaml"),'w') as fd:
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

## List of raw data files required for wind power preproecssing 
raw_data_files = ['project_development_timeframes.csv']# fillin

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
class DieselEfficiency(AnnualSavings):
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
        
        self.comp_specs = community_data.get_section(COMPONENT_NAME)
        self.component_name = COMPONENT_NAME
        
        self.comp_specs["start year"] = self.cd['current year'] + \
            self.comp_specs["project details"]['expected years to operation']

        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
        
        
    def run (self):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        self.run = True
        self.reason = "OK"
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1] != 'diesel_efficiency':
            self.run = False
            self.reason = "Not a Diesel efficiency project"
            return 
        
        if not self.cd["model electricity"]:
            self.run = False
            self.reason = "Electricty must be modeled"
            return 
            # change these below
            
        self.calc_average_load()
        self.calc_baseline_generation_fuel_use()
        
        self.calc_proposed_generation_fuel_use()

        
        if self.cd["model financial"]:
        
            self.get_diesel_prices()
            
            # change these below
            self.calc_capital_costs()
            self.calc_oppex()
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            # AnnualSavings functions (don't need to write)
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
        
    def calc_average_load (self):
        """
            calculate the average load of the system
            
        pre: 
            self.generation should be a number (kWh/yr)
            
        post:
            self.average_load is a number (kW/yr)
        """
        self.generation = self.forecast.generation_by_type['generation diesel']\
                                .ix[self.start_year:self.end_year-1].values
        self.average_load = self.generation[0] / constants.hours_per_year
        #~ print 'self.average_load',self.average_load
 

    def calc_baseline_generation_fuel_use (self):
        """ Function doc """
        self.baseline_diesel_efficiency = \
                        self.cd["diesel generation efficiency"]
        self.baseline_generation_fuel_use = self.generation / \
                                        self.baseline_diesel_efficiency 
    
    def calc_proposed_generation_fuel_use (self):
        """ Function doc """
        self.proposed_diesel_efficiency = \
                        self.cd["diesel generation efficiency"] * \
                        self.comp_specs['efficiency improvment']
        self.proposed_generation_fuel_use = self.generation / \
                                        self.proposed_diesel_efficiency 
    
    def calc_capital_costs (self):
        """ Function Doc"""
        max_load = self.generation[:self.actual_project_life].max() / \
                                                    constants.hours_per_year
        proposed_cap = 13.416 * max_load ** (1-0.146 )  
        
        self.capital_costs = (1.8 + .001 * proposed_cap)*1000000
    
    def calc_oppex (self):
        """
        """  
        key = 'else'
        for max_load in sorted(self.comp_specs['o&m costs'].keys())[:-1]:
            if self.average_load <= max_load:
                key = max_load
                break
            
        
        self.oppex = self.comp_specs['o&m costs'][key]
        
        
        
    def calc_annual_electric_savings (self):
        """
        """
        price = self.diesel_prices
        
        
        
        base = self.baseline_generation_fuel_use * price + self.oppex
        proposed = self.proposed_generation_fuel_use * price + self.oppex
        
        self.annual_electric_savings = base - proposed
        
    def calc_annual_heating_savings (self):
        """
        """
        self.annual_heating_savings = 0
        
component = DieselEfficiency

def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../test_case/input_data/","../test_case/baseline_results/config_used.yaml")
    fc = Forecast(manley_data)
    comp = ComponentName(manley_data, fc)
    comp.run()
    return comp,fc # return the object for further testing
