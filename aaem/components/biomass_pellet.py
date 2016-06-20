"""
component_template.py

a template for adding components



"""
import numpy as np
from math import isnan
from pandas import DataFrame, concat, read_csv
from copy import deepcopy
import os

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants


import biomass_base as bmb


# change to component name (i.e. 'residential buildings')
COMPONENT_NAME = "biomass pellet"

## List of yaml key/value pairs
yaml = deepcopy(bmb.yaml)
yaml["energy density"] = 17600000
yaml["pellet efficiency"] = .8
yaml["cost per btu/hr"] = .54
yaml["default pellet price"] = 400
yaml["on road system"] = "IMPORT"


## default values for yaml key/Value pairs
yaml_defaults = deepcopy(bmb.yaml_defaults)
    
## order to save yaml
yaml_order = deepcopy(bmb.yaml_order) + ["pellet efficiency",
                                "cost per btu/hr",
                                "default pellet price"]

## comments for the yaml key/value pairs
yaml_comments = deepcopy(bmb.yaml_comments)
yaml_comments["energy density"] = "energy density of pellets (btu/ton) <float>"
yaml_comments["pellet efficiency"] = \
                        "effcicieny of pellets (% as decimal) <float>"
yaml_comments["cost per btu/hr"] = "cost per btu/hr ($) <float>"
yaml_comments["default pellet price"] = "pellet cost per ton ($) <float>" 
       

def road_import (data_dir):
    """
    import the road system boolean
    """
    data_file = os.path.join(data_dir, "road_system.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    data = data['value'].to_dict()
    on_road = data["On Road/SE"].lower() == "yes"
    return on_road
    

    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = deepcopy(bmb.yaml_import_lib)
yaml_import_lib["on road system"] = road_import
    
raw_data_files = deepcopy(bmb.raw_data_files) + ["road_system.csv"]

## list of prerequisites for module
prereq_comps = deepcopy(bmb.prereq_comps)

def preprocess_road_system_header(ppo):
    """
    pre: 
        ppo is a preprocessor object
    post:
        returns the road header
    """
    return  "# " + ppo.com_id + " biomass data\n"+ \
            "# biomass data from biomass_data.csv preprocessed into a \n" +\
            "# based on the row for the given community \n" +\
            ppo.comments_dataframe_divide

def preprocess_road_system (ppo):
    """
    preprocess road_system data
    pre: 
        ppo is a preprocessor object
    post:
        saves "biomass_data.csv", and updates MODEL_FILES
    """
    data = read_csv(os.path.join(ppo.data_dir,"road_system.csv"),
                        comment = '#',index_col = 0).ix[ppo.com_id]
                        
    out_file = os.path.join(ppo.out_dir,"road_system.csv")

    fd = open(out_file,'w')
    fd.write(preprocess_road_system_header(ppo))
    fd.write("key,value\n")
    fd.close()

    # create data and uncomment this
    data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['road_system'] = "road_system.csv" # change this


## list of wind preprocessing functions
preprocess_funcs = [deepcopy(bmb.preprocess),preprocess_road_system]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []
    
## component summary
def component_summary (coms, res_dir):
    """
    save thes the summary for biomass pellet
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
            
           
            biomass = coms[c]['model'].comps_used[COMPONENT_NAME]
            
            l = [c, 
                 biomass.max_boiler_output,
                 biomass.heat_displaced_sqft,
                 biomass.biomass_fuel_consumed,
                 biomass.fuel_price_per_unit,
                 biomass.comp_specs['energy density'],
                 biomass.heat_diesel_displaced,
                 biomass.get_NPV_benefits(),
                 biomass.get_NPV_costs(),
                 biomass.get_NPV_net_benefit(),
                 biomass.get_BC_ratio(),
                 biomass.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    
    data = DataFrame(out,columns = \
       ['Community',
        'Maximum Boiler Output [Btu/hr]',
        'Heat Displacement square footage [Sqft]',
        'Proposed ' + biomass.biomass_type + " Consumed [" + biomass.units +"]",
        'Price [$/' + biomass.units + ']',
        "Energy Density [Btu/" + biomass.units + "]",
        "Displaced Heating Oil [Gal]",
        'NPV benefits [$]',
        'NPV Costs [$]',
        'NPV Net benefit [$]',
        'Benefit Cost Ratio',
        'notes']
                    ).set_index('Community')#.round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.replace(" ","_") + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# " + COMPONENT_NAME + " summary\n"))
    fd.close()
    data.to_csv(f_name, mode='a')

#   do a find and replace on ComponentName to name of component 
# (i.e. 'ResidentialBuildings')
class BiomassPellet (bmb.BiomassBase):
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
        self.component_name = COMPONENT_NAME
        super(BiomassPellet, self).__init__(community_data, forecast, 
                                                    diag, prerequisites)
        self.biomass_type = "pellets"
        self.units = "tons"
        self.reason = "OK"
        
    def run (self):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        s_key = 'Sufficient Biomass for 30% of Non-residential buildings'
        
        
        if not self.comp_specs["on road system"] and \
            not self.comp_specs['data'][s_key]:
            self.diagnostics.add_warning(self.component_name, 
                                    "not " + s_key +"; Not on road system")
            self.max_boiler_output = 0
            self.heat_displaced_sqft = 0
            self.biomass_fuel_consumed = 0
            self.fuel_price_per_unit = 0
            self.heat_diesel_displaced = 0
            self.reason = "not " + s_key +"; Not on road system"
            return
        
        
        if not self.comp_specs['data'][s_key]:
            self.diagnostics.add_warning(self.component_name, 
                                    "not " + s_key)
            self.max_boiler_output = 0
            self.heat_displaced_sqft = 0
            self.biomass_fuel_consumed = 0
            self.fuel_price_per_unit = 0
            self.heat_diesel_displaced = 0
            self.reason = "not " + s_key
            return
        
        if not self.comp_specs["on road system"]:
            self.diagnostics.add_warning(self.component_name, 
                                    "not on road system")
            self.max_boiler_output = 0
            self.heat_displaced_sqft = 0
            self.biomass_fuel_consumed = 0
            self.fuel_price_per_unit = 0
            self.heat_diesel_displaced = 0
            self.reason = "Not on road system"
            return
        
        if self.cd["model heating fuel"]:
            self.calc_heat_displaced_sqft()
            self.calc_energy_output()
            efficiency = self.comp_specs["pellet efficiency"]
            self.calc_max_boiler_output(efficiency)
            factor = self.comp_specs['data']['Capacity Factor']
            self.calc_biomass_fuel_consumed(factor)
            self.calc_diesel_displaced()
            
        
        if self.cd["model financial"]:
            self.get_diesel_prices()
            
            self.calc_capital_costs()
            self.calc_maintainance_cost()
            
            
            self.fuel_price_per_unit = self.comp_specs["default pellet price"]
            
            self.calc_proposed_biomass_cost(self.fuel_price_per_unit)
            self.calc_displaced_heating_oil_price()
            
            
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])

            
    def calc_maintainance_cost(self):
        """
        calculate maitiance costs
        """
        
        self.maintenance_cost = self.capital_costs * .01

    def calc_capital_costs (self):
        """
        calculate the captial costs
        """
        self.capital_costs = self.max_boiler_output * \
                                self.comp_specs["cost per btu/hr"]
        #~ print self.capital_costs

component = BiomassPellet

def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../test_case/input_data/","../test_case/baseline_results/config_used.yaml")
    fc = Forecast(manley_data)
    comp = ComponentName(manley_data, fc)
    comp.run()
    return comp,fc # return the object for further testing
