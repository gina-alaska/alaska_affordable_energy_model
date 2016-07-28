"""
hydro.py

hydro power component



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


# change to component name (i.e. 'residential buildings')
COMPONENT_NAME = "Hydropower"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        "project details": IMPORT,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'percent excess energy': .15,
        'percent excess energy capturable': .7,
        'efficiency electric boiler': .99,
        'efficiency heating oil boiler': .8,
        'percent heat recovered': .15,
        'percent o&m': .01
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
        tag = os.path.split(data_dir)[1].split('+')
        project_type = tag[1]
        tag = tag[1] + '+' +tag[2]
        if project_type != 'hydro':
            tag = None
    except IndexError:
        tag = None
    
        
    # get the estimated years to operation
    # CHANGE THIS Replace the PROJECT_TYPE with the type of the project
    data_file = os.path.join(data_dir, 'project_development_timeframes.csv')
    data = read_csv(data_file, comment = '#',
                    index_col=0, header=0)['Hydroelectric']

    if tag is None:
        # if no data make some
        yto = 5#int(round(float(data['Reconnaissance'])))
        return None
            #~ {'phase': 'Reconnaissance',
                #~ 'proposed capacity': 25,
                #~ 'proposed generation': 1000,
                #~ 'distance to resource': 10,
                #~ 'generation capital cost': 500,
                #~ 'transmission capital cost': 500,
                #~ 'expected years to operation': yto,
                #~ }

    
    # CHANGE THIS
    with open(os.path.join(data_dir, "hydro_projects.yaml"), 'r') as fd:
        dets = load(fd)[tag]
    
    # correct number years if nessary
    yto = dets['expected years to operation']
    if yto == UNKNOWN:
        try:
            yto = int(round(float(data[dets['phase']])))
        except (TypeError, KeyError):
            yto = 0
        dets['expected years to operation'] = yto
    dets['expected years to operation'] = int(yto)
    
    return dets
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'project details': load_project_details}# fill in
    
## preprocessing functons 
## list of preprocessing functions
## all preprocessing is for existing projects
preprocess_funcs = [] 

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
    project_data = read_csv(os.path.join(ppo.data_dir,"hydro_projects.csv"),
                           comment = '#',index_col = 0)
    
    try:
        project_data = DataFrame(project_data.ix[ppo.com_id])
        if len(project_data.T) == 1 :
            project_data = project_data.T
    except KeyError:
        project_data = []

    #~ ## FILL IN LOOP see function in wind _power.py for an example
    names = []
    for p_idx in range(len(project_data)):
        cp = project_data.ix[p_idx]
        p_name = 'hydro+project_' + str(p_idx) #+ str(cp['Project']).replace(' ','_').replace('/','-').replace(';','').replace('.','').replace("'",'').replace('_-_','_').replace(',','').replace('(','').replace(')','')
        #~ i = 1
        #~ i = 1
        #~ while (p_name in names):
            #~ p_name = 'hydro+' + str(cp['Project']).replace(' ','_').replace('/','-').replace(';','').replace('.','').replace("'",'').replace('_-_','_').replace(',','').replace('(','').replace(')','') + '_' + str(i)
            #~ i += 1
        #~ names.append(p_name)

        
        phase = cp['Phase Completed']
        phase = phase[0].upper() + phase[1:]
        proposed_capacity = float(cp['AAEM Capacity (kW)'])
        proposed_generation = float(cp['AAEM Generation (kWh)'])
        #~ distance_to_resource = float(cp['Distance'])
        generation_capital_cost = float(cp['Construction Cost (2014$)'])
        transmission_capital_cost = float(cp['Transmission Cost (current)'])
        expected_years_to_operation = UNKNOWN
        if phase == "0":
            phase = "Reconnaissance"
            

        projects.append(p_name)
        
            
        p_data[p_name] = {'name': str(cp['Project']),
                    'phase': phase,
                    'proposed capacity': proposed_capacity,
                    'proposed generation': proposed_generation,
                    #~ 'distance to resource': distance_to_resource,
                    'generation capital cost': generation_capital_cost,
                    'transmission capital cost': transmission_capital_cost,
                    'expected years to operation': expected_years_to_operation
                        }
    
    with open(os.path.join(ppo.out_dir,"hydro_projects.yaml"),'w') as fd:
        if len(p_data) != 0:
            fd.write(dump(p_data,default_flow_style=False))
        else:
            fd.write("")
        
    ## CHANGE THIS
    ppo.MODEL_FILES['COMPONENT_PROJECTS'] = "hydro_projects.yaml"
    shutil.copy(os.path.join(ppo.data_dir,'project_development_timeframes.csv'), 
                ppo.out_dir)
    ppo.MODEL_FILES['TIMEFRAMES'] = 'project_development_timeframes.csv'
    #~ print ppo.MODEL_FILES
    return projects

## List of raw data files required for wind power preproecssing 
raw_data_files = ["hydro_projects.csv",
                  'project_development_timeframes.csv']# fillin

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
            hydro = coms[c]['model'].comps_used['Hydropower']
            
            start_yr = hydro.comp_specs['start year']
            hydro.get_diesel_prices()
            diesel_price = float(hydro.diesel_prices[0].round(2))
            #~ print hydro.diesel_prices[0]
            if not hydro.comp_specs["project details"] is None:
                phase = hydro.comp_specs["project details"]['phase']
            else:
                phase = "Reconnaissance"

            name = hydro.comp_specs["project details"]['name']
            
            average_load = hydro.average_load
            proposed_load =  hydro.load_offset_proposed
            
            
            heat_rec_opp = hydro.cd['heat recovery operational']
            
           
            net_gen_hydro = hydro.net_generation_proposed
            
            captured_energy = hydro.captured_energy
            
            
            lost_heat = hydro.lost_heat_recovery
            electric_diesel_reduction= hydro.generation_diesel_reduction
            
            diesel_red = hydro.captured_energy - hydro.lost_heat_recovery
            
            eff = hydro.cd["diesel generation efficiency"]
            
            levelized_cost = hydro.levelized_cost_of_energy
            break_even = hydro.break_even_cost
            #~ except AttributeError:
                #~ offset = 0
                #~ net_gen_hydro = 0
                #~ decbb = 0
                #~ electric_diesel_reduction=0
                #~ loss_heat = 0
                
                #~ diesel_red = 0
                #~ eff = hydro.cd["diesel generation efficiency"]    
                
            #~ try:
                #~ red_per_year = net_gen_hydro / eff
            #~ except ZeroDivisionError:
                #~ red_per_year = 0
            
            l = [c, 
                name,
                start_yr,
                phase,

                average_load, 
                proposed_load,
                net_gen_hydro,
                
                captured_energy, 
                lost_heat, 
                heat_rec_opp,
                diesel_red, 
                electric_diesel_reduction,
                
                eff,
                diesel_price,
                break_even,
                levelized_cost,
                hydro.get_NPV_benefits(),
                hydro.get_NPV_costs(),
                hydro.get_NPV_net_benefit(),
                hydro.get_BC_ratio(),
                hydro.reason
            ]
            out.append(l)
        except (KeyError,AttributeError,TypeError) as e:
            #~ print e
            pass
        
    
    cols = ['Community',
            'Project Name',
            'Start Year',
            'project phase',
            
            'Average Diesel Load [kw]',
            'Wind Capacity Proposed [kW]',
            'Net Proposed Hydro Generation [kWh]',
            
            'Heating Oil Equivalent Captured by Secondary Load [gal]',
            'Loss of Recovered Heat from Genset [gal]',
            'Heat Recovery Operational',
            'Net Reduction in Heating Oil Consumption [gal]',
            'Hydro Power Reduction in Utility Diesel Consumed per year',
            'Diesel Generator Efficiency',
            'Diesel Price - year 1 [$/gal]',
            'Break Even Diesel Price [$/gal]',
            
            'Levelized Cost Of Energy [$/kWh]',
            'Hydro NPV benefits [$]',
            'Hydro NPV Costs [$]',
            'Hydro NPV Net benefit [$]',
            'Hydro Benefit Cost Ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                'hydropower_summary.csv')

    data.to_csv(f_name, mode='w')

## list of prerequisites for module
prereq_comps = [] ## no prereqs 

# component
class Hydropower (AnnualSavings):
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
        try:
            self.comp_specs["start year"] = self.cd['current year'] + \
            self.comp_specs["project details"]['expected years to operation']
        except TypeError:
            self.comp_specs["start year"] = self.cd['current year']
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
        
        self.load_prerequisite_variables(prerequisites)
        
    def load_prerequisite_variables (self, comps):
        """
        load variables from prerequisites
        
        pre:
             prerequisites: dictonary of componentes
        """
        # not used here
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
        if len(tag) > 1 and tag[1] != 'hydro':
            self.run = False
            self.reason = "Not a Hydro project"
            return 
        
        if self.comp_specs["project details"] is None:
            self.run = False
            self.reason = "No Project Data"
            return 
        
        if not self.cd["model electricity"]:
            self.run = False
            self.reason = ("'model electricity' in the communtiy data"
                           " must be True to run this component")
            return 
            
        try:
            self.calc_average_load()
            self.calc_generation_proposed()
        except AttributeError:
            self.diagnostics.add_warning(self.component_name, 
                            "could not be run")
            self.run = False
            self.reason = "could not find average load or proposed generation"
            return
            
        if self.load_offset_proposed is None:
            self.run = False
            self.reason = "No project data provided"
            return
            
        if self.cd["model heating fuel"]:
            self.calc_heat_recovery ()
        
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
            
            
            o_m = self.net_generation_proposed * \
                    self.cd['diesel generator o&m cost']
        
            self.calc_levelized_costs(o_m)
            
    def calc_average_load (self):
        """
            calculate the average load of the system
            
        pre: 
            self.generation should be a number (kWh/yr)
            
        post:
            self.average_load is a number (kW/yr)
        """
        self.generation = self.forecast.generation_by_type['generation diesel']\
                                                            [self.start_year]
        self.average_load = self.generation / constants.hours_per_year
        #~ print 'self.average_load',self.average_load
 
    def calc_generation_proposed (self):
        """
            calulate the proposed generation for wind
        pre:
            self.generation should be a number (kWh/yr), 
            'percent generation to offset' is a decimal %
            'resource data' is a wind data object
            'assumed capacity factor' is a decimal %
        
        post:
            self.load_offest_proposed is a number (kW)
            self.gross_generation_proposed is a number (kWh/yr)
            self.net_generation_proposed is a number (kWh/yr)
        """
        if self.comp_specs["project details"]['proposed capacity'] == UNKNOWN:
            self.load_offset_proposed = None
            self.gross_generation_proposed = None
            self.net_generation_proposed = None
            
        else:
            self.load_offset_proposed = \
                    self.comp_specs["project details"]['proposed capacity']
            self.gross_generation_proposed = \
                    self.comp_specs["project details"]['proposed generation']
            tansmission_losses = self.cd['line losses'] *\
                                 self.gross_generation_proposed
            exess_energy = \
                (self.gross_generation_proposed - tansmission_losses) * \
                self.comp_specs['percent excess energy']
            
            self.percent_excess_energy = exess_energy / \
                                         self.gross_generation_proposed   
            
            self.net_generation_proposed = self.gross_generation_proposed -\
                                           tansmission_losses -\
                                           exess_energy
        
            if self.net_generation_proposed > self.generation:
                self.net_generation_proposed = self.generation
                                           
        #~ print 'self.load_offset_proposed', self.load_offset_proposed
        #~ print 'self.gross_generation_proposed', self.gross_generation_proposed
        #~ print 'self.net_generation_proposed', self.net_generation_proposed


    def calc_heat_recovery (self):
        """
        caclulate heat recovery values used by component
        pre:
            self.percent_excess_energy is the precentage of excess energy
        created in generation
            self.gross_generation_proposed is a floating point value
        post:
            self.generation_diesel_reduction, self.lost_heat_recovery, 
        and self.generation_diesel_reduction
            
        """
        # %
       
        captured_percent = self.percent_excess_energy * \
                    self.comp_specs['percent excess energy capturable']
        
        #kWh/year
        captured_energy = captured_percent * self.gross_generation_proposed
        
        #~ conversion: gal <- kwh
        conversion = self.comp_specs['efficiency electric boiler']/ \
                     (1/constants.mmbtu_to_gal_HF)/ \
                     self.comp_specs['efficiency heating oil boiler']/\
                     (constants.mmbtu_to_kWh)
        self.captured_energy = captured_energy * conversion # gallons/year
        
        # gal/year <- kWh*year/ (kWh/gal) 
        gen_eff = self.cd["diesel generation efficiency"]
        self.generation_diesel_reduction = self.net_generation_proposed /\
                                            gen_eff
                                            
        #~ electric_diesel = self.generation /gen_eff
        #~ if self.generation_diesel_reduction > electric_diesel:
            #~ self.generation_diesel_reduction = electric_diesel
        
        # gal/year
        if not self.cd['heat recovery operational']:

            self.lost_heat_recovery  = 0
        else:
            self.lost_heat_recovery = self.generation_diesel_reduction * \
                                self.comp_specs['percent heat recovered']
        
        #~ print 'self.captured_energy', self.captured_energy
        #~ print 'self.lost_heat_recovery', self.lost_heat_recovery

    # Make this do stuff
    def calc_capital_costs (self):
        """
        calculate the captial costs
        
        pre:
            the project details section of the hydro section is initlized
        according to structure shown in load project detials
        post:
            self.capital_costs is the total cost of the project in dollars
        """
        transmission_cost = \
            self.comp_specs['project details']['transmission capital cost']
        generator_cost = \
            self.comp_specs['project details']['generation capital cost']
        self.capital_costs = transmission_cost + generator_cost
        #~ print 'self.capital_costs', self.capital_costs
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        calculates the annual electric savings
        pre:
            self.captial_costs should be caclulated
            self.comp_specs and self.cd should have all values nessary for 
        this component.
            self.diesel_prices should be intilized
        post:
            self.annual_electric_savings is the annual elctric savings in 
        dollars
        """
        proposed_generation_cost = self.capital_costs * \
                                self.comp_specs['percent o&m']
                        
        
        maintianice_cost = self.net_generation_proposed * \
                        self.cd['diesel generator o&m cost']  
        
        price = self.diesel_prices
        
        fuel_cost = price * self.generation_diesel_reduction
        
        baseline_generation_cost = fuel_cost + maintianice_cost
        
        self.annual_electric_savings = baseline_generation_cost - \
                                        proposed_generation_cost 
        #~ print 'self.annual_electric_savings', self.annual_electric_savings
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        calcualte the annual heating savings
        pre:
            self.diesel_prices should be initilzed as a np.array of 
        floats ($/gal)
            self.cd should have all values initilzed as designed
            self.captured_energy and self.lost_heat_recovery are [gallons]
        post:
            self.annual_heating_savings is an array or scaler in dollars
        
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        
        self.annual_heating_savings = \
                (self.captured_energy - self.lost_heat_recovery) *\
                price
        #~ print 'self.annual_heating_savings', self.annual_heating_savings
        
    def get_fuel_total_saved (self):
        """
        returns the total fuel saved in gallons
        """
    
        return sum(np.zeros(self.actual_project_life) + \
                (self.captured_energy - self.lost_heat_recovery) + \
                (self.generation_diesel_reduction))
    
    def get_total_enery_produced (self):
        """
        returns the total energy produced
        """
        return sum(np.zeros(self.actual_project_life) + \
                    self.net_generation_proposed) 
        
    def save_component_csv (self, directory):
        """
        save the output from the component.
        """
        #~ return
        if not self.run:
            return
        
        
        years = np.array(range(self.project_life)) + self.start_year
    
        # ??? +/- 
        # ???
        df = DataFrame({
                'Hydro: Capacity (kW)':self.load_offset_proposed,
                "Hydro: Generation (kWh/year)": self.net_generation_proposed,
                'Hydro: Energy Captured by Secondary Load'
                    ' (gallons of heating oil equivalent)':self.captured_energy,

                'Hydro: Utility Diesel Displaced (gallons/year)':
                                            self.captured_energy - \
                                            self.lost_heat_recovery,
                'Hydro: Heat Recovery Lost (gallons/year)':
                                            self.lost_heat_recovery, 
                "Hydro: Heat Recovery Cost Savings ($/year)": 
                                            self.get_heating_savings_costs(),
                "Hydro: Electricity Cost Savings ($/year)": 
                                            self.get_electric_savings_costs(),
                "Hydro: Project Capital Cost ($/year)": 
                                            self.get_capital_costs(),
                "Hydro: Total Cost Savings ($/year)":
                                            self.get_total_savings_costs(),
                "Hydro: Net Benefit ($/year)": self.get_net_beneft(),
                       }, years)

        df["Community"] = self.cd['name']
        
        ol = ["Community",
              'Hydro: Capacity (kW)',
              'Hydro: Energy Captured by Secondary Load'
                        ' (gallons of heating oil equivalent)',
              'Hydro: Utility Diesel Displaced (gallons/year)',
              'Hydro: Heat Recovery Lost (gallons/year)',
              "Hydro: Generation (kWh/year)",
              "Hydro: Heat Recovery Cost Savings ($/year)",
              "Hydro: Electricity Cost Savings ($/year)",
              "Hydro: Project Capital Cost ($/year)",
              "Hydro: Total Cost Savings ($/year)",
              "Hydro: Net Benefit ($/year)"]

        fname = os.path.join(directory,
                             self.cd['name'] + '_' + \
                             self.component_name + "_output.csv")
        fname = fname.replace(" ","_")
        
        df[ol].ix[:self.actual_end_year].to_csv(fname, index_label="Year")

component = Hydropower


