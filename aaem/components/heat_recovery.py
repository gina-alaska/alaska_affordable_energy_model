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
COMPONENT_NAME = "heat recovery"
PROJECT_TYPE = 'heat_recovery'
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        "project details": IMPORT,
        'estimate data': IMPORT,
        'estimate pipe distance': 1500,
        'estimate pipe cost/ft': 135,
        'estimate buildings to heat': 2,
        'estimate cost/building':40000,
        
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'percent heat recovery': .10,
        'heating conversion efficiency': .75,
        
        'o&m per year': 500
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
    data_file = os.path.join(data_dir, "heat_recovery_data.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    return data['value'].to_dict()
    
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
        if project_type != PROJECT_TYPE:
            tag = None
    except IndexError:
        tag = None
        
    # get the estimated years to operation
    # CHANGE THIS Replace the PROJECT_TYPE with the type of the project
    data_file = os.path.join(data_dir, 'project_development_timeframes.csv')
    data = read_csv(data_file, comment = '#',
                    index_col=0, header=0)['Heat Recovery']

    if tag is None:
        # if no data make some
        yto = int(round(float(data['Reconnaissance'])))
        return {'name': 'None', 
                'phase': 'Reconnaissance',
                'project type': 'New',
                'total feet piping needed': UNKNOWN, 
                'number buildings': UNKNOWN,
                'buildings': [],
                'proposed gallons diesel offset': UNKNOWN,
                'proposed Maximum btu/hr': UNKNOWN, 
                'captial costs': UNKNOWN,
                'expected years to operation': yto
                }
    
    # CHANGE THIS
    with open(os.path.join(data_dir, "heat_recovery_projects.yaml"), 'r') as fd:
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
    #~ print dets
    return dets
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'project details': load_project_details,
                   'estimate data': process_data_import }# fill in
    
## preprocessing functons 
def preprocess_header (ppo):
    """
    """
    return  "# " + ppo.com_id + " heat recovery data\n"+ \
            ppo.comments_dataframe_divide
    
def preprocess (ppo):
    """
    
    """
    #CHANGE THIS
    out_file = os.path.join(ppo.out_dir,"heat_recovery_data.csv")

    data = read_csv(os.path.join(ppo.data_dir,"heat_recovery_data.csv"), 
                                    comment = '#',index_col = 0)
                                    
    data = ppo.get_communities_data(data)
    data_cols = ['Waste Heat Recovery Opperational','Add waste heat Avail',
                 'Est. current annual heating fuel gallons displaced',
                 'Est. potential annual heating fuel gallons displaced']
    data =  data[data_cols]
    
    # if no data add defaults
    if len(data) == 0:
        data = DataFrame([['No','No', np.nan, np.nan],],columns = data_cols)
    
    # if multiple data rows assume first is best
    if len(data) > 1:
        data = data.iloc[0]


    data['Waste Heat Recovery Opperational'] = \
        data['Waste Heat Recovery Opperational'].fillna('No')
    data['Add waste heat Avail'] = data['Add waste heat Avail'].fillna('No')
    
    data = data.T

    
    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.write("key,value\n")
    fd.close()

    
    
    # create data and uncomment this
    data.to_csv(out_file, mode = 'a', header=False)
    
    ppo.MODEL_FILES['HR_DATA'] = "heat_recovery_data.csv" # CHANGE THIS
    
## list of wind preprocessing functions
preprocess_funcs = [preprocess]

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
    
    proj_cols = ['Project Name','Year','Phase Completed',
                 'New/Repair/Extension',
                 'Total Round-trip Distance of Piping (feet)',
                 'Number of Buildings/Facilities',
                 'Buildings/Facilities to be Served',
                 'Proposed Gallons of Diesel Offset',
                 'Proposed Maximum Btu/hr','Total CAPEX','Source']
    project_data = read_csv(os.path.join(ppo.data_dir,
                                "heat_recovery_data.csv"),
                            comment = '#',index_col = 0)[proj_cols]
                            
    project_data = ppo.get_communities_data(project_data)
    if len(project_data) != 0 and int(project_data.fillna(0).sum(axis=1)) == 0:
        project_data = DataFrame(columns=project_data.columns)
    #~ print project_data

    for p_idx in range(len(project_data)):
        cp = project_data.ix[p_idx]
        p_name = 'heat_recovery+project_' + str(p_idx)
        
        name = str(cp['Project Name'])
        phase = str(cp['Phase Completed'])
        phase = phase[0].upper() + phase[1:]
        project_type = str(cp['New/Repair/Extension'])
        total_piping_needed = \
            float(cp['Total Round-trip Distance of Piping (feet)'])
        num_buildings = int( cp['Number of Buildings/Facilities'] )
        buildings = str(cp['Buildings/Facilities to be Served']).split(',')
        
        diesel_offset = float(cp['Proposed Gallons of Diesel Offset'])
        max_btu_per_hr = float(cp['Proposed Maximum Btu/hr'])
        capex = float(cp['Total CAPEX'])
        
        
        expected_years_to_operation = UNKNOWN
        
        projects.append(p_name)
        
        p_data[p_name] = {'name': name, 
                          'phase': phase,
                          'project type': project_type,
                          'total feet piping needed': total_piping_needed, 
                          'number buildings': num_buildings,
                          'buildings': buildings,
                          'proposed gallons diesel offset':diesel_offset,
                          'proposed Maximum btu/hr': max_btu_per_hr, 
                          'captial costs':capex,
                          'expected years to operation':
                                                expected_years_to_operation
                        }
        
        
    
    with open(os.path.join(ppo.out_dir,
                    "heat_recovery_projects.yaml"),'w') as fd:
        if len(p_data) != 0:
            fd.write(dump(p_data,default_flow_style=False))
        else:
            fd.write("")
        
    ## CHANGE THIS
    ppo.MODEL_FILES['HR_PROJECTS'] = "heat_recovery_projects.yaml"
    shutil.copy(os.path.join(ppo.data_dir,'project_development_timeframes.csv'), 
                ppo.out_dir)
    ppo.MODEL_FILES['TIMEFRAMES'] = 'project_development_timeframes.csv'
    #~ print ppo.MODEL_FILES
    return projects

## List of raw data files required for wind power preproecssing 
raw_data_files = ["heat_recovery_data.csv",
                  'project_development_timeframes.csv']# fillin

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []
    
## component summary
def component_summary (coms, res_dir):
    """
    """
    out = []
    for c in sorted(coms.keys()):
        #~ it = coms[c]['model'].cd.intertie
        #~ if it is None:
            #~ it = 'parent'
        #~ if it == 'child':
            #~ continue
        if c.find("_intertie") != -1:
            continue
        try:
            
            comp = coms[c]['model'].comps_used[COMPONENT_NAME]
            
            comp.get_diesel_prices()
            diesel_price = float(comp.diesel_prices[0].round(2))
            hfp = comp.cd['heating fuel premium']
            
            propsed_hr = comp.proposed_heat_recovery
            #~ eff = comp.cd["diesel generation efficiency"]
            
            try:
                break_even_cost = comp.break_even_cost
                levelized_cost_of_energy = comp.levelized_cost_of_energy
            except AttributeError:
                break_even_cost = np.nan
                levelized_cost_of_energy = np.nan
            
            l = [c, 
                 
                 
                 propsed_hr,
                 diesel_price,
                 hfp,
                 diesel_price + hfp,
                 #~ eff,
                 break_even_cost,
                 levelized_cost_of_energy,
                 comp.get_NPV_benefits(),
                 comp.get_NPV_costs(),
                 comp.get_NPV_net_benefit(),
                 comp.get_BC_ratio(),
                 comp.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    
    cols = ['Community',
        
            'Proposed Heat Recovery [gallons]',
            'Diesel price - year 1 [$/gal]',
            'Heating Fuel Premimum [$/gal]',
            'Heating Fuel Price - year 1 [$/gal]',
            'Break Even Diesel Price [$/gal]',
            'Levelized Cost of Energy [$/MMBtu]',
            'Heat Recovery NPV benefits [$]',
            'Heat Recovery NPV Costs [$]',
            'Heat Recovery NPV Net benefit [$]',
            'Heat Recovery Benefit Cost Ratio',
            'notes'
            ]
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_") + '_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# " + COMPONENT_NAME + " summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')

## list of prerequisites for module
prereq_comps = [] ## FILL in if needed

#   do a find and replace on ComponentName to name of component 
# (i.e. 'ResidentialBuildings')
class HeatRecovery (AnnualSavings):
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
        if len(tag) > 1 and tag[1] != PROJECT_TYPE:
            self.run = False
            self.reason = "Not a " + PROJECT_TYPE + " project"
            self.diagnostics.add_note(self.component_name, self.reason)
            return 
        
        if self.cd["model heating fuel"]:
            try:
                self.calc_proposed_heat_recovery()
            except AttributeError:
                self.run = False
                self.reason = "could not find proposed heat recovery"
                self.diagnostics.add_note(self.component_name, self.reason)
                return 
                
        if np.isnan(self.proposed_heat_recovery) or \
                self.proposed_heat_recovery == 0:
            self.run = False
            self.reason = "No proposed heat recovery"
            self.diagnostics.add_note(self.component_name, self.reason)
            return 
        
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
            
            self.calc_levelized_costs(self.comp_specs['o&m per year'])
            
    
    def get_fuel_total_saved (self):
        """
        returns the total fuel saved in gallons
        """
        return self.proposed_heat_recovery
    
    def get_total_enery_produced (self):
        """
        returns the total energy produced
        """
        return self.proposed_heat_recovery/ constants.mmbtu_to_gal_HF
 
    def calc_proposed_heat_recovery (self):
        """
        heat_recovery(gal diesel) = generation diesel (gal diesel) * .05 / .75
        
        """
        p_gallons = self.comp_specs["project details"]\
                            ['proposed gallons diesel offset']
        p_btu = self.comp_specs["project details"]\
                            ['proposed Maximum btu/hr']
                            
        # is there a project
        if p_gallons != UNKNOWN and p_btu != UNKNOWN:
            self.proposed_heat_recovery = p_gallons
            return
        # else:
        b1 = self.comp_specs['estimate data']\
                    ['Waste Heat Recovery Opperational']
        b2 = self.comp_specs['estimate data']\
                    ['Add waste heat Avail']
                    
              
        
        #~ current_hr = self.comp_specs['estimate data']\
                    #~ ['Est. current annual heating fuel gallons displaced'] 
        #~ try:
            #~ np.isnan(current_hr)
        #~ except TypeError:
            #~ current_hr = np.nan            
        
        potential_hr = self.comp_specs['estimate data']\
                    ['Est. potential annual heating fuel gallons displaced']
        
        try:
            np.isnan(potential_hr)
        except TypeError:
            potential_hr = np.nan            
        
        
        generation = self.forecast.generation_by_type['generation diesel']\
                                                            [self.start_year]
        gen_eff = self.cd["diesel generation efficiency"]
        
        # gallons 
        diesel_consumed = generation / gen_eff
        hr_available = self.comp_specs['percent heat recovery'] * \
                          diesel_consumed
        #notes
        #if b1 == 'Yes' and b2 == 'Yes':
        #   if hr_used is known and hr_proposed is not
        #      hr_used, hr_proposed = .30 * hr_available
        #   if hr_used is unknown and hr_proposed is unknown
        #      hr_used= .70 * hr_available, hr_proposed = .30 * hr_available
        #if b1 == 'Yes' and b2 == 'no':
        #   if hr_used is known:
        #       hr_used
        #   else:
        #       hr_used = hr_avaiavble
        #if b1 == 'No' and b2 == 'No':
        #   system needs to be installed        
        if b1 == 'Yes' and b2 == 'Yes' and np.isnan(potential_hr):
            potential_hr = ((hr_available) * .30)
        if b1 == 'Yes' and b2 == 'Yes':
            pass #potential_hr 
        elif b1 == 'Yes' and b2 == 'No':
            potential_hr = 0
        else:
            potential_hr = 0
            
        

        
        self.proposed_heat_recovery = potential_hr / \
                                self.comp_specs['heating conversion efficiency']
    
    
    # Make this do stuff
    def calc_capital_costs (self):
        """ Function Doc"""
        captial_costs = self.comp_specs["project details"]['captial costs']
        if captial_costs == UNKNOWN:

            install_cost = 50000 * \
                            self.comp_specs['estimate pipe distance']/1000.0

            loop_cost = self.comp_specs['estimate pipe cost/ft'] * \
                        self.comp_specs['estimate pipe distance']
                        
            overhead_cost = self.comp_specs['estimate pipe distance']/1000.0 * \
                            140000
            building_cost = self.comp_specs['estimate buildings to heat'] * \
                                self.comp_specs['estimate cost/building']
            captial_costs = install_cost + loop_cost +\
                            overhead_cost + building_cost
        self.capital_costs = captial_costs
        
    
    def calc_annual_electric_savings (self):
        """
        """
        self.annual_electric_savings = 0
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        
        self.annual_heating_savings = self.proposed_heat_recovery * price + \
                                      self.comp_specs['o&m per year']

component = HeatRecovery
