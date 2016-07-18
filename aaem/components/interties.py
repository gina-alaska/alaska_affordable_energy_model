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
from biomass_pellet import preprocess_road_system, road_import 


## steps for using
### 1) copy this file as component_name.py and go throug this file folloing the 
###    commented instructions
### 2) add new components things to default yaml file
### 3) add the component to __init__ in this directory

# change to component name (i.e. 'residential buildings')
COMPONENT_NAME = "transmission"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        "project details": IMPORT,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'transmission loss per mile': .1,
        'nearest community': IMPORT,
        'heat recovery o&m' : 1500,
        'on road system': IMPORT,
        'est. intertie cost per mile': {'road needed': 500000, 
                                        'road not needed': 250000},
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
    data = read_csv(os.path.join(data_dir,'transmission_data.csv'),
                    comment = '#',index_col = 0)
    data = data['value'].to_dict()
    data['Maximum savings ($/kWh)'] = float(data['Maximum savings ($/kWh)'])
    data['Distance to Community'] = float(data['Distance to Community'])
    #~ print data
    return data
                    
    
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
        tag = os.path.split(data_dir)[1].split('+')
        project_type = tag[1]
        tag = tag[1] + '+' +tag[2]
        if project_type != 'transmission':
            tag = None
    except IndexError:
        tag = None
        
    # get the estimated years to operation
    # CHANGE THIS Replace the PROJECT_TYPE with the type of the project
    data_file = os.path.join(data_dir, 'project_development_timeframes.csv')
    data = read_csv(data_file, comment = '#',
                    index_col=0, header=0)['Transmission']

    if tag is None:
        # if no data make some
        yto = 5 # int(round(float(data['Reconnaissance'])))
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
    with open(os.path.join(data_dir, "transmission_projects.yaml"), 'r') as fd:
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
yaml_import_lib = {'project details': load_project_details,
                    'nearest community':process_data_import,
                    'on road system': road_import }# fill in
    
## preprocessing functons 
def preprocess_header (ppo):
    """
    """
    return  "# " + ppo.com_id + " Transmission data\n"+ \
            ppo.comments_dataframe_divide
    
def preprocess (ppo):
    """
    
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
        try:
            isnan(nearest_comm)
            nearest_comm =  np.nan
        except ValueError:
            nearest_comm = nearest_comm.values[0]
            
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
preprocess_funcs = [preprocess, preprocess_road_system]

## preprocess the existing projects
### This function is called differently from the other preprocessor functions,
### so it does not need to be added to preprocess_funcs
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
    
    #~ ## CHANGE THIS
    #~ project_data = read_csv(os.path.join(ppo.data_dir,
                            #~ "transmission_projects.csv"),
                            #~ comment = '#',index_col = 0)
    
    #~ project_data = DataFrame(project_data.ix[ppo.com_id])
    #~ if len(project_data.T) == 1 :
        #~ project_data = project_data.T

    #~ ## FILL IN LOOP see function in wind _power.py for an example
    #~ for p_idx in range(len(project_data)):
       #~ pass
    
    #~ with open(os.path.join(ppo.out_dir,"transmission_projects.yaml"),'w') as fd:
        #~ if len(p_data) != 0:
            #~ fd.write(dump(p_data,default_flow_style=False))
        #~ else:
            #~ fd.write("")
        
    #~ ## CHANGE THIS
    #~ ppo.MODEL_FILES['TRANSMISSION_PROJECTS'] = "transmission_projects.yaml"
    #~ shutil.copy(os.path.join(ppo.data_dir,'project_development_timeframes.csv'), 
                #~ ppo.out_dir)
    ppo.MODEL_FILES['TIMEFRAMES'] = 'project_development_timeframes.csv'
    #~ print ppo.MODEL_FILES
    return projects

## List of raw data files required for wind power preproecssing 
raw_data_files = [#"transmission_projects.csv",
                  'project_development_timeframes.csv',
                  'transmission_distances.csv',
                  'road_system.csv']# fillin

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []
    
## component summary
def component_summary (coms, res_dir):
    """
    """
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['model'].cd.intertie
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        try:
            # ??? NPV or year one
            it = coms[c]['model'].comps_used['transmission']
            
            start_yr = it.comp_specs['start year']
            it.get_diesel_prices()
            diesel_price = float(it.diesel_prices[0].round(2))
            if not it.comp_specs["project details"] is None:
                phase = it.comp_specs["project details"]['phase']
            else:
                phase = "Reconnaissance"
                
                
            heat_rec_opp = it.cd['heat recovery operational']
            
           
            generation_displaced = it.baseline_generation[0]
            generation_conserved = it.proposed_generation[0]
            
                    
            
            lost_heat = it.lost_heat_recovery[0]
            
            #~ diesel_red = - it.lost_heat_recovery
            
            eff = it.cd["diesel generation efficiency"]
                
            
            l = [c, 
                start_yr,
                phase,

                generation_displaced,
                generation_conserved,
                
                lost_heat,
                heat_rec_opp,
                
                eff,
                diesel_price,
                
                it.get_NPV_benefits(),
                it.get_NPV_costs(),
                it.get_NPV_net_benefit(),
                it.get_BC_ratio(),
                it.reason
            ]
            out.append(l)
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
        
    
    cols = ['Community',
            'Start Year',
            'project phase',
            
            'Generation Displaced [kWh]',
            'Electricity Generated, Conserved, or transmitted [kWh]',
            
            'Loss of Recovered Heat from Genset [gal]',
            'Heat Recovery Operational',
           
           
            'Diesel Generator Efficiency',
            'Diesel Price - year 1 [$]',
            
            'Transmission NPV benefits [$]',
            'Transmission NPV Costs [$]',
            'Transmission NPV Net benefit [$]',
            'Transmission Benefit Cost Ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                'transmissions_summary.csv')

    data.to_csv(f_name, mode='w')

## list of prerequisites for module
prereq_comps = [] ## FILL in if needed

#   do a find and replace on ComponentName to name of component 
# (i.e. 'ResidentialBuildings')
class Transmission (AnnualSavings):
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
        self.run = True
        self.reason = "OK"
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1] != 'transmission':
            self.run = False
            self.reason = "Not a transmission project"
            return 
            
        if not self.cd["model electricity"]:
            self.run = False
            self.reason = ("'model electricity' in the communtiy data"
                           " must be True to run this component")
            return 
        
        if np.isnan(self.comp_specs['nearest community']\
                                    ['Distance to Community']):
            self.run = False
            self.reason = ("no community to intertie with transmission line")
            return 
        
        self.calc_proposed_generation()
        self.calc_baseline_generation()
            
        
        if self.cd["model heating fuel"]:
            # change these below
            self.calc_lost_heat_recovery()
            # see NOTE*
        
        #~ return
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
            #~ print self.benefit_cost_ratio
 
    def calc_proposed_generation (self):
        """
        """
        con = self.forecast.get_consumption(self.start_year,self.end_year)
        dist = self.comp_specs['nearest community']['Distance to Community']
        annual_tranmission_loss = \
            1 - ((1-self.comp_specs['transmission loss per mile']) ** dist)
        self.proposed_generation = con/ (1 - annual_tranmission_loss)
        #~ print 'self.proposed_generation',self.proposed_generation
        #~ print con
        
    def calc_baseline_generation (self):
        """
        """
        
        self.baseline_generation = \
            self.forecast.get_generation(self.start_year,self.end_year)
        
        gen_eff = self.cd["diesel generation efficiency"]
        self.baseline_generation_fuel_used = self.baseline_generation / gen_eff
        
        #~ print 'self.baseline_generatio',self.baseline_generation
        
    def calc_lost_heat_recovery (self):
        """
        """
        self.lost_heat_recovery = self.baseline_generation_fuel_used
    
    # Make this do stuff
    def calc_capital_costs (self):
        """ Function Doc"""
        road_needed = 'road needed'
        if self.comp_specs['on road system']:
            road_needed = 'road not needed'
        print road_needed
        
        dist = self.comp_specs['nearest community']['Distance to Community']
        self.capital_costs = self.comp_specs['est. intertie cost per mile']\
                                             [road_needed] * dist
        #~ print self.capital_costs
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        """
        #TODO READ in maintenance
        maintenance = 84181 
        base = maintenance + \
            (self.baseline_generation_fuel_used * self.diesel_prices)
        
        ## TODO move the .05
        maintenance = self.capital_costs * .05
        proposed = maintenance + \
            (self.proposed_generation * \
                self.comp_specs['nearest community']['Maximum savings ($/kWh)'])
        self.annual_electric_savings = base - proposed 
        #~ print 'self.annual_electric_savings',self.annual_electric_savings
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        """
        price = self.diesel_prices + self.cd['heating fuel premium']
        maintenance = self.comp_specs['heat recovery o&m']
        self.annual_heating_savings = maintenance + \
                                    (self.lost_heat_recovery * price)

component = Transmission
