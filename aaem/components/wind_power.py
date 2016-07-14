"""
wind_power.py

wind power component
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

#TODO 2016/06/01
# ambler

IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,

        "project details": IMPORT,#{
        
            #~ 'phase':IMPORT,
            #~ 'proposed capacity': IMPORT,
            #~ 'proposed generation': IMPORT,
            #~ 'distance to resource': IMPORT,
            #~ 'generation capital cost':IMPORT,
            #~ 'transmission capital cost': IMPORT,
            #~ 'operational costs': IMPORT,
            #~ 'expected years to operation':IMPORT,
                #~ },
        
        'default distance to resource': 1,

        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        
        'average load limit': 100.0,
        'percent generation to offset': 1.00,
        'resource data':'IMPORT',
         #'minimum wind class': 3,
        #~ 'generation capital cost': 'UNKNOWN', #  same as generation captial cost
        'secondary load': True,
        'secondary load cost': 200000,
        'road needed for transmission line' : True,
        'est. transmission line cost': { True:500000, False:250000},
        'costs': 'IMPORT',
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
        'start year': 2020,
        }

## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>',
        'average load limit': 
                'lower limit in kW on average load required to do project',
        'percent generation to offset': '',
        'minimum wind class': 'minimum wind class for feasibility',
        'secondary load': '',
        'secondary load cost': '',
        'road needed for transmission line':'',
        'distance to resource': 'miles defaults to 1 mile',
        'est. transmission line cost': 'cost/mile',
        'assumed capacity factor': "TODO read in preprocessor",
        }
       
## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """
    Loads wind_power_data.csv
    
    pre:
        wind_power_data.csv exists at data_dir
    post:
        the values in wind_power_data.csv are returned as a dictionary 
    """
    data_file = os.path.join(data_dir, "wind_power_data.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    return data['value'].to_dict()
    
def load_wind_costs_table (data_dir):
    """
    loads the wind cost table
    
    pre:
        wind_costs.csv exists at data_dir
    post:
        the wind cost values are returned as a pandas DataFrame
    """
    data_file = os.path.join(data_dir, "wind_costs.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    data.index =data.index.astype(str)
    return data
    
def load_project_details (data_dir):
    """
    load details related to exitign projects
    
    pre:
        data_dir is a directory with  'project_development_timeframes.csv',
        and "wind_projects.yaml" in it 
    
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
        if project_type != 'wind':
            tag = None
    except IndexError:
        tag = None
    
    # get the estimated years to operation
    data_file = os.path.join(data_dir, 'project_development_timeframes.csv')
    data = read_csv(data_file, comment = '#', index_col=0, header=0)['Wind']

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
                
    #read data
    with open(os.path.join(data_dir, "wind_projects.yaml"), 'r') as fd:
        dets = load(fd)[tag]
      
    # correct number years if nessary
    if dets['expected years to operation'] == UNKNOWN:
        if dets['phase'] == 'Operational':
            yto = 0
        else:
            try:
                yto = int(round(float(data[dets['phase']])))
            except TypeError:
                yto =0
        #~ print yto
        dets['expected years to operation'] = yto
    dets['expected years to operation'] = \
        int(dets['expected years to operation'])    
    return dets
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'resource data':process_data_import,
                   'costs':load_wind_costs_table,
                   'project details': load_project_details,
                   }

## wind preprocessing functons 
def wind_preprocess_header (ppo):
    """
    wind preporcess header
    
    pre:
        ppo: a Preprocessor object
    post:
        returns the header for the wind data preprocessed csv file
    """
    ## TODO Expand
    return  "# " + ppo.com_id + " wind data\n"+ \
            ppo.comments_dataframe_divide
    
def wind_preprocess (ppo):
    """
    Reprocesses the wind data
    
    pre:
        ppo is a Preprocessor object. wind_class_assumptions, 
    wind_data_existing.csv and wind_data_potential.csv file exist at 
    ppo.data_dir's location 
    
    post:
        preprocessed wind data is saved at ppo.out_dir as wind_power_data.csv
    """
    try:
        existing = read_csv(os.path.join(ppo.data_dir,"wind_data_existing.csv"),
                        comment = '#',index_col = 0).ix[ppo.com_id]
        existing = existing['Rated Power (kW)']
    except KeyError:
        existing = 0
    #~ #~ print existing
    try:
        potential = read_csv(os.path.join(ppo.data_dir,
                                "wind_data_potential.csv"),
                            comment = '#',index_col = 0).ix[ppo.com_id]
    except KeyError:
        potential = DataFrame(index = ['Wind Potential','Wind-Resource',
                                       'Assumed Wind Class',
                                       'Wind Developability','Site Accessible ',
                                       'Permittability','Site Availability',
                                       'Load','Certainty',
                                       'Estimated Generation','Estimated Cost',
                                       'Note','Resource Note'])
                                       
    try:
        intertie = read_csv(os.path.join(ppo.data_dir,
                            "wind_data_interties.csv"),
                            comment = '#',
                            index_col = 0).ix[ppo.com_id+"_intertie"]
        intertie = int(intertie['Highest Wind Class on Intertie'])
    except KeyError:
        intertie = 0

    try:
        if intertie > int(potential['Assumed Wind Class']):
            potential.ix['Assumed Wind Class'] = intertie
            ppo.diagnostics.add_note("wind", 
                    "Wind class updated to max on intertie")
        
    except KeyError:
        pass
    
    assumptions = read_csv(os.path.join(ppo.data_dir,
                                "wind_class_assumptions.csv"),
                           comment = '#',index_col = 0)
                           
    try:
        solar_cap = read_csv(os.path.join(ppo.data_dir,
                                "solar_data_existing.csv"),
                            comment = '#',index_col = 0).ix[ppo.com_id]
        solar_cap = solar_cap['Installed Capacity (kW)']
        if np.isnan(solar_cap):
            solar_cap = 0
    except (IOError,KeyError):
        solar_cap = 0 
    
    try:
        capa = assumptions.ix[int(float(potential.ix['Assumed Wind Class']))]
        capa = capa.ix['REF V-VI Net CF']
    except (TypeError,KeyError):
        capa = 0
    #~ print capa
    
    #~ #~ print potential
    out_file = os.path.join(ppo.out_dir,"wind_power_data.csv")
    #~ #~ print ppo.out_dir,"wind_power_data.csv"
    fd = open(out_file,'w')
    fd.write(wind_preprocess_header(ppo))
    fd.write("key,value\n")
    fd.write("existing wind," + str(existing) +'\n')
    fd.write("existing solar," + str(solar_cap) + '\n')
    fd.write('assumed capacity factor,' +str(capa) +'\n')
    fd.close()

    #~ df = concat([ww_d,ww_a])
    potential.to_csv(out_file, mode = 'a',header=False)
    #~ self.wastewater_data = df
    ppo.MODEL_FILES['WIND_DATA'] = "wind_power_data.csv"
    
def copy_wind_cost_table(ppo):
    """
    copies wind cost table file to each community
    
    pre:
        ppo is a Preprocessor object. wind_costs.csv exists at ppo.data_dir
    post:
        wind_costs.csv is copied from ppo.data_dir to ppo.out_dir 
    """
    data_dir = ppo.data_dir
    out_dir = ppo.out_dir
    shutil.copy(os.path.join(data_dir,"wind_costs.csv"), out_dir)
    ppo.MODEL_FILES['WIND_COSTS'] = "wind_costs.csv"
## end wind preprocessing functions

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
    
    project_data = read_csv(os.path.join(ppo.data_dir,"wind_projects.csv"),
                           comment = '#',index_col = 0)
    
    project_data = DataFrame(project_data.ix[ppo.com_id])
    if len(project_data.T) == 1 :
        project_data = project_data.T


    for p_idx in range(len(project_data)):
        cp = project_data.ix[p_idx]
        
        p_name = cp['Project Name']
        try:
            if p_name == "" or np.isnan(p_name):
                p_name = "project_" + str(p_idx)
        except TypeError:
            p_name = "project_" + str(p_idx)
        p_name = 'wind+' + p_name
        
        phase = cp['Phase']
        proposed_capacity = cp['Proposed Capacity (kW)']
        proposed_generation = cp['Proposed Generation (kWh)']
        distance_to_resource = cp['Distance to Resource (ft)']
        generation_capital_cost = cp['Generation Capital Cost']
        transmission_capital_cost = cp['Transmission CAPEX']
        operational_costs = cp['Operational Costs / year']
        expected_years_to_operation = cp['Expected years to operation']
        if phase == "0":
            continue
        if phase == "Reconnaissance" and np.isnan(proposed_capacity) and\
           np.isnan(proposed_generation) and np.isnan(distance_to_resource) and\
           np.isnan(generation_capital_cost)  and \
           np.isnan(transmission_capital_cost) and \
           np.isnan(operational_costs) and \
           np.isnan(expected_years_to_operation):
            continue
        
        projects.append(p_name)
        
        proposed_capacity = float(proposed_capacity)
        if np.isnan(proposed_capacity):
            proposed_capacity = UNKNOWN
    
        proposed_generation = float(proposed_generation)
        if np.isnan(proposed_generation):
            proposed_generation = UNKNOWN
        
        distance_to_resource = float(distance_to_resource)
        if np.isnan(distance_to_resource):
            distance_to_resource = UNKNOWN
           
        generation_capital_cost = float(generation_capital_cost)
        if np.isnan(generation_capital_cost):
            generation_capital_cost = UNKNOWN
        
        transmission_capital_cost = float(transmission_capital_cost)
        if np.isnan(transmission_capital_cost):
            transmission_capital_cost = UNKNOWN
        
        operational_costs = float(operational_costs)
        if np.isnan(operational_costs):
            operational_costs = UNKNOWN
            
        expected_years_to_operation = float(expected_years_to_operation)
        if np.isnan(expected_years_to_operation):
            expected_years_to_operation = UNKNOWN
            
        p_data[p_name] = {'phase': phase,
                    'proposed capacity': proposed_capacity,
                    'proposed generation': proposed_generation,
                    'distance to resource': distance_to_resource,
                    'generation capital cost': generation_capital_cost,
                    'transmission capital cost': transmission_capital_cost,
                    'operational costs': operational_costs,
                    'expected years to operation': expected_years_to_operation
                        }
                            
    if len(p_data) != 0:
        fd = open(os.path.join(ppo.out_dir,"wind_projects.yaml"),'w')
        fd.write(dump(p_data,default_flow_style=False))
        fd.close()
    else:
        fd = open(os.path.join(ppo.out_dir,"wind_projects.yaml"),'w')
        fd.write("")
        fd.close()
        #~ return projects 


    ppo.MODEL_FILES['WIND_PROJECTS'] = "wind_projects.yaml"
    shutil.copy(os.path.join(ppo.data_dir,'project_development_timeframes.csv'), 
                ppo.out_dir)
    ppo.MODEL_FILES['TIMEFRAMES'] = 'project_development_timeframes.csv'
    #~ print ppo.MODEL_FILES
    return projects
        

## List of raw data files required for wind power preproecssing 
raw_data_files = ['wind_class_assumptions.csv',
                  'wind_costs.csv',
                  "wind_data_existing.csv",
                  "wind_data_potential.csv",
                  "diesel_data.csv",
                  'wind_data_interties.csv',
                  "solar_data_existing.csv",
                  "wind_projects.csv",
                  'project_development_timeframes.csv']

## list of wind preprocessing functions
preprocess_funcs = [wind_preprocess, copy_wind_cost_table]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = ['costs']

## component summary
def component_summary (coms, res_dir):
    """ 
    save the component summary for wind
    
    pre:
        res_dir is a directory
    post:
        file is written in res_dir
    """
    #~ return
    out = []
    for c in sorted(coms.keys()):
        it = coms[c]['model'].cd.intertie
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        try:
            # ??? NPV or year one
            wind = coms[c]['model'].comps_used['wind power']
            
            start_yr = wind.comp_specs['start year']
            wind.get_diesel_prices()
            diesel_price = float(wind.diesel_prices[0].round(2))
            phase = wind.comp_specs["project details"]['phase']
            average_load = wind.average_load
            existing_load = wind.comp_specs['resource data']\
                                            ['existing wind']
            existing_solar = wind.comp_specs['resource data']['existing solar']
            wind_class = float(wind.comp_specs['resource data']\
                                                ['Assumed Wind Class']) 
            proposed_load =  wind.load_offset_proposed
            cap_fac = float(wind.comp_specs['resource data']\
                                            ['assumed capacity factor'])
            heat_rec_opp = wind.cd['heat recovery operational']
            try:
                #~ offset = wind.load_offset_proposed
                net_gen_wind = wind.net_generation_wind
                decbb = wind.diesel_equiv_captured
                
                
                loss_heat = wind.loss_heat_recovery
                electric_diesel_reduction=wind.electric_diesel_reduction
                
                diesel_red = wind.reduction_diesel_used
                
                eff = wind.cd["diesel generation efficiency"]
                
            except AttributeError:
                offset = 0
                net_gen_wind = 0
                decbb = 0
                electric_diesel_reduction=0
                loss_heat = 0
                
                diesel_red = 0
                eff = wind.cd["diesel generation efficiency"]    
                
            #~ try:
                #~ red_per_year = net_gen_wind / eff
            #~ except ZeroDivisionError:
                #~ red_per_year = 0
            
            l = [c, 
                start_yr,
                phase,
                wind_class, 
                average_load, 
                proposed_load,
                existing_load,
                existing_solar,
                cap_fac,
                net_gen_wind,
                decbb, 
                loss_heat, 
                heat_rec_opp,
                diesel_red, 
                electric_diesel_reduction,
                eff,
                diesel_price,
                wind.get_NPV_benefits(),
                wind.get_NPV_costs(),
                wind.get_NPV_net_benefit(),
                wind.get_BC_ratio(),
                wind.reason
            ]
            out.append(l)
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
        
    
    cols = ['Community',
            'Start Year',
            'project phase',
            'Assumed Wind Class',
            'Average Diesel Load [kw]',
            'Wind Capacity Proposed [kW]',
            'Existing Wind Capacity [kW]',
            'Existing Solar Capacity [kW]',
            'Assumed Wind Class Capacity Factor [%]',
            'Net Proposed Wind Generation [kWh]',
            'Heating Oil Equivalent Captured by Secondary Load [gal]',
            'Loss of Recovered Heat from Genset [gal]',
            'Heat Recovery Operational',
            'Net in Heating Oil Consumption [gal]',
            'Wind Power Reduction in Utility Diesel Consumed per year',
            'Diesel Denerator Efficiency','Diesel Price - year 1 [$]',
            'Wind NPV benefits [$]',
            'Wind NPV Costs [$]',
            'Wind NPV Net benefit [$]',
            'Wind Benefit Cost Ratio',
            'notes'
            ]
        
    
    data = DataFrame(out,columns = cols).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                'wind_power_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# wind summary\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')

## component name
COMPONENT_NAME = "wind power"

## list of prerequisites for module
prereq_comps = []

## component
class WindPower(AnnualSavings):
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
        #~ print self.cd['current year']
        self.comp_specs["start year"] = self.cd['current year'] + \
            self.comp_specs["project details"]['expected years to operation']
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
                        
        ### ADD other intiatzation stuff
        
        
    
    def run (self):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        #~ #~ print self.comp_specs['resource data']
        #~ return
        
        self.run = True
        self.reason = "OK"
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1] != 'wind':
            self.run = False
            self.reason = "Not a Wind project"
            return 
            
        try:
            #~ self.generation = self.forecast.get_generation(self.start_year)
            self.calc_average_load()
            self.calc_generation_wind_proposed()
        except AttributeError:
            self.diagnostics.add_warning(self.component_name, 
                            "could not be run")
            self.run = False
            self.reason = "could not find average load or proposed generation"
            return
            
        
 
        
        #~ #~ print self.comp_specs['resource data']['Assumed Wind Class'] 
        # ??? some kind of failure message
        if self.average_load is None or \
            (self.average_load > self.comp_specs['average load limit'] and \
            self.load_offset_proposed > 0):
            #~ float(self.comp_specs['resource data']['Assumed Wind Class']) > \
                #~ self.comp_specs['minimum wind class'] and \
               
        # if the average load is greater that the lower limit run this component
        # else skip    
            
            self.calc_transmission_losses()
            self.calc_exess_energy()
            self.calc_net_generation_wind()
            self.calc_electric_diesel_reduction()
            self.calc_diesel_equiv_captured()
            self.calc_loss_heat_recovery()
            self.calc_reduction_diesel_used()
            
            
           
            if self.cd["model electricity"]:
                # change these below
                #~ self.calc_baseline_kWh_consumption()
                #~ self.calc_retrofit_kWh_consumption()
                #~ self.calc_savings_kWh_consumption()
                # NOTE*:
                #   some times is it easier to find the savings and use that to
                # calculate the retro fit values. If so, flip the function calls 
                # around, and change the functionality of
                # self.calc_savings_kWh_consumption() below
                pass
            
            if self.cd["model heating fuel"]:
                pass
                # see NOTE*
        
            if self.cd["model financial"]:
                # AnnualSavings functions (don't need to write)
                self.get_diesel_prices()
                
                # change these below
                self.calc_capital_costs()
                self.calc_maintainance_cost()
                self.calc_annual_electric_savings()
                self.calc_annual_heating_savings()
                
                # AnnualSavings functions (don't need to write)
                self.calc_annual_total_savings()
                self.calc_annual_costs(self.cd['interest rate'])
                self.calc_annual_net_benefit()
                self.calc_npv(self.cd['discount rate'], self.cd["current year"])
                #~ print self.benefit_cost_ratio
        else:
            #~ print "wind project not feasiable"
            self.run = False
            if self.load_offset_proposed <= 0: 
                self.reason = "no load offset proposed"
            else:
                self.reason = "average load too small"
            self.diagnostics.add_note(self.component_name, 
            "communites average load is not large enough to consider project")
        #~ print self.benefit_cost_ratio
        
    def calc_average_load (self):
        """
            calculate the average load of the system
            
        pre: 
            self.generation should be a number (kWh/yr)
            
        post:
            self.average_load is a number (kW/yr)
        """
        if self.comp_specs["project details"]['proposed capacity'] != UNKNOWN:
            self.average_load = None
        self.generation = self.forecast.generation_by_type['generation diesel']\
                                                            [self.start_year]
        self.average_load = self.generation / constants.hours_per_year
        #~ print 'self.average_load',self.average_load
        
    def calc_generation_wind_proposed (self):
        """
            calulate the proposed generation for wind
        pre:
            self.generation should be a number (kWh/yr), 
            'percent generation to offset' is a decimal %
            'resource data' is a wind data object
            'assumed capacity factor' is a decimal %
        
        post:
            self.load_offest_proposed is a number (kW)
            self.generation_wind_proposed is a number (kWh/yr)
        """
        if self.comp_specs["project details"]['proposed capacity'] != UNKNOWN:
            self.load_offset_proposed = \
                    self.comp_specs["project details"]['proposed capacity']
            self.generation_wind_proposed = \
                    self.comp_specs["project details"]['proposed generation']
            return
        
        self.load_offset_proposed = 0
        
        offset = self.average_load*\
                self.comp_specs['percent generation to offset']
        #~ print self.forecast.generation_by_type['generation hydro'].sum()
        hydro = \
            self.forecast.generation_by_type['generation hydro'].fillna(0).sum()
        if hydro > 0:
            offset *= 2
        #~ self.comp_specs['resource data']['existing wind'] = 0
        
        # existing very variable RE
        existing_RE = \
            int(float(self.comp_specs['resource data']['existing wind'])) + \
            int(float(self.comp_specs['resource data']['existing solar']))
        
        if existing_RE < (round(offset/25) * 25): # ???
            #~ print "True"
            self.load_offset_proposed = round(offset/25) * 25 - existing_RE
        
                    
        
        # not needed for now
        #~ self.total_wind_generation = self.generation_load_proposed + \
                    #~ int(self.comp_specs['resource data']['existing wind'])
        
        self.generation_wind_proposed =  self.load_offset_proposed * \
            float(self.comp_specs['resource data']['assumed capacity factor'])*\
                                    constants.hours_per_year
        #~ print 'self.load_offset_proposed',self.load_offset_proposed
        #~ print 'self.generation_wind_proposed',self.generation_wind_proposed 
        
    def calc_transmission_losses (self):
        """
            calculate the line losses on proposed system
            
        pre:
            self.generation_wind_proposed is a number (kWh/yr). 
            self.cd is a CommunityData object
        """
        self.transmission_losses = self.generation_wind_proposed * \
                                                        self.cd['line losses']
        #~ print 'self.transmission_losses',self.transmission_losses
        
    def calc_exess_energy (self):
        """
            calculate the excess energy
            TODO add more:
        """
        #~ print sorted(self.cd.keys())
        self.exess_energy = \
            (self.generation_wind_proposed - self.transmission_losses) * \
            self.comp_specs['percent excess energy']
        #~ print 'self.exess_energy',self.exess_energy
            
    def calc_net_generation_wind (self):
        """
            calculate the proposed net generation
        """
        self.net_generation_wind = self.generation_wind_proposed  - \
                                    self.transmission_losses  -\
                                    self.exess_energy
        #~ print 'self.net_generation_wind',self.net_generation_wind 
            
    def calc_electric_diesel_reduction (self):
        """ 
            calculate the reduction in diesel due to the proposed wind
        """
        gen_eff = self.cd["diesel generation efficiency"]
            
        self.electric_diesel_reduction = self.net_generation_wind / gen_eff
        
        electric_diesel = self.generation/gen_eff
        if self.electric_diesel_reduction > electric_diesel:
            self.electric_diesel_reduction = electric_diesel
            
        
        
        #~ print 'self.electric_diesel_reduction',self.electric_diesel_reduction
        
    def calc_diesel_equiv_captured (self):
        """
            calulate the somthing ???
        """
        if self.generation_wind_proposed == 0:
            exess_percent = 0
        else:
            exess_percent = self.exess_energy / self.generation_wind_proposed
        exess_captured_percent = exess_percent * \
                    self.comp_specs['percent excess energy capturable']
        if self.comp_specs['secondary load']:
            net_exess_energy = exess_captured_percent * \
                                self.generation_wind_proposed 
        else:
            net_exess_energy = 0
       
        #~ conversion = 0.99/0.138/0.8/293 
        conversion = self.comp_specs['efficiency electric boiler']/ \
                     (1/constants.mmbtu_to_gal_HF)/ \
                     self.comp_specs['efficiency heating oil boiler']/\
                     (constants.mmbtu_to_kWh)
        self.diesel_equiv_captured = net_exess_energy * conversion
             
        #~ print 'self.diesel_equiv_captured ',self.diesel_equiv_captured 
        
    def calc_loss_heat_recovery (self):
        """ 
             calulate the somthing ???
        """
        hr_used = self.cd['heat recovery operational']
        self.loss_heat_recovery = 0
        if hr_used:# == 'Yes': 
            self.loss_heat_recovery = self.electric_diesel_reduction * \
            self.comp_specs['percent heat recovered']
        #~ print 'self.loss_heat_recovery',self.loss_heat_recovery
        
    def calc_reduction_diesel_used (self):
        """ 
             calulate the somthing ???
        """
        self.reduction_diesel_used = self.diesel_equiv_captured - \
                                     self.loss_heat_recovery
        #~ print 'self.reduction_diesel_used',self.reduction_diesel_used
                                     
    def calc_maintainance_cost (self):
        """ 
            calculate the maintainance cost
        """
        
        if str(self.comp_specs['project details']['operational costs']) \
                                                                != 'UNKNOWN':
            self.maintainance_cost = \
                self.comp_specs['project details']['operational costs']
        else:
            self.maintainance_cost = \
                self.comp_specs['percent o&m'] * self.capital_costs
        #~ print 'self.maintainance_cost',self.maintainance_cost
        

    
    
    # Make this do stuff
    def calc_capital_costs (self):
        """
        caclulate the progect captial costs
        """
        powerhouse_control_cost = 0
        if not self.cd['switchgear suatable for RE']:
            powerhouse_control_cost = self.cd['switchgear cost']
        
        road_needed = self.comp_specs['road needed for transmission line']
        

        if str(self.comp_specs['project details']['transmission capital cost'])\
           != 'UNKNOWN':
            transmission_line_cost = \
            int(self.comp_specs['project details']['transmission capital cost'])
        else:
            if str(self.comp_specs['project details']['distance to resource']) \
                != 'UNKNOWN':
                distance = \
                    float(self.comp_specs['project details']\
                        ['distance to resource'])
                distance = distance * constants.feet_to_mi
            else:
                distance = self.comp_specs['default distance to resource']
            transmission_line_cost = distance*\
            self.comp_specs['est. transmission line cost'][road_needed]
        
        secondary_load_cost = 0
        if self.comp_specs['secondary load']:
            secondary_load_cost = self.comp_specs['secondary load cost']
        
        if str(self.comp_specs['project details']['generation capital cost']) \
            != 'UNKNOWN':
            wind_cost = \
              int(self.comp_specs['project details']['generation capital cost'])
        else:
            for i in range(len(self.comp_specs['costs'])):
                if int(self.comp_specs['costs'].iloc[i].name) < \
                                            self.load_offset_proposed:
                    if i == len(self.comp_specs['costs']) - 1:
                        cost = float(self.comp_specs['costs'].iloc[i])
                        break
                    continue
               
                cost = float(self.comp_specs['costs'].iloc[i])
                break
            
            wind_cost = self.load_offset_proposed * cost
        
        
        #~ print powerhouse_control_cost 
        #~ print transmission_line_cost 
        #~ print secondary_load_cost 
        #~ print wind_cost
        self.capital_costs = powerhouse_control_cost + transmission_line_cost +\
                             secondary_load_cost + wind_cost
                             
        #~ print 'self.capital_costs',self.capital_costs
        
    
    # Make this do stuff
    def calc_annual_electric_savings (self):
        """
        """
        price = self.diesel_prices
        #TODO add rural v non rural
        self.base_generation_cost = self.electric_diesel_reduction * price
                        
        
        self.proposed_generation_cost = self.maintainance_cost
        
        self.annual_electric_savings = self.base_generation_cost - \
                            self.proposed_generation_cost
        #~ print 'self.annual_electric_savings',self.annual_electric_savings
        
        
        
    # Make this do sruff. Remember the different fuel type prices if using
    def calc_annual_heating_savings (self):
        """
        """
        price = (self.diesel_prices + self.cd['heating fuel premium'])
        
        #~ self.base_heating_cost =
        
        #~ self.proposed_heating_cost =
        
        
        
        
        self.annual_heating_savings = self.reduction_diesel_used * price
        #~ print 'self.annual_heating_savings',self.annual_heating_savings


    def save_component_csv (self, directory):
        """
        save the output from the component.
        """
        #~ return
        if not self.run:
            #~ fname = os.path.join(directory,
                                   #~ self.component_name + "_output.csv")
            #~ fname = fname.replace(" ","_")
        
            #~ fd = open(fname, 'w')
            #~ fd.write("Wind Power minimum requirments not met\n")
            #~ fd.close()
            return
        
        
        years = np.array(range(self.project_life)) + self.start_year
    
        # ??? +/- 
        # ???
        df = DataFrame({
                'Wind: Capacity (kW)':self.load_offset_proposed,
                "Wind: Generation (kWh/year)": self.net_generation_wind,
                'Wind: Energy Captured by Secondary Load'
                    ' (gallons of heating oil equivalent)':
                                                    self.diesel_equiv_captured,
                'Wind: Assumed capacity factor':
                    float(self.comp_specs['resource data']\
                                                ['assumed capacity factor']),
                'Wind: Utility Diesel Displaced (gallons/year)':
                                            self.electric_diesel_reduction,
                'Wind: Heat Recovery Lost (gallons/year)':
                                            self.loss_heat_recovery, 
                "Wind: Heat Recovery Cost Savings ($/year)": 
                                            self.get_heating_savings_costs(),
                "Wind: Electricity Cost Savings ($/year)": 
                                            self.get_electric_savings_costs(),
                "Wind: Project Capital Cost ($/year)": 
                                            self.get_capital_costs(),
                "Wind: Total Cost Savings ($/year)":
                                            self.get_total_savings_costs(),
                "Wind: Net Benefit ($/year)": self.get_net_beneft(),
                       }, years)

        df["Community"] = self.cd['name']
        
        ol = ["Community",
              'Wind: Capacity (kW)',
              'Wind: Energy Captured by Secondary Load'
                        ' (gallons of heating oil equivalent)',
              'Wind: Assumed capacity factor',
              'Wind: Utility Diesel Displaced (gallons/year)',
              'Wind: Heat Recovery Lost (gallons/year)',
              "Wind: Generation (kWh/year)",
              "Wind: Heat Recovery Cost Savings ($/year)",
              "Wind: Electricity Cost Savings ($/year)",
              "Wind: Project Capital Cost ($/year)",
              "Wind: Total Cost Savings ($/year)",
              "Wind: Net Benefit ($/year)"]
        fname = os.path.join(directory,
                             self.cd['name'] + '_' + \
                             self.component_name + "_output.csv")
        fname = fname.replace(" ","_")
        
        df[ol].ix[:self.actual_end_year].to_csv(fname, index_label="Year")
        
    
component = WindPower

def test ():
    """
    tests the class using the manley data.
    """
    pass
