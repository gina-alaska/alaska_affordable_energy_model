"""
component_template.py

a template for adding components



"""
import numpy as np
from math import isnan
from pandas import DataFrame,concat
import os
from copy import deepcopy

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants


import ashp_base 


# change to component name (i.e. 'residential buildings')
COMPONENT_NAME = "ASHP non-residential"

## List of yaml key/value pairs
yaml = deepcopy(ashp_base.yaml)
yaml[ "btu/hrs"] = 90000
yaml[ "cost per btu/hrs" ] = 25000 
yaml['percent sqft assumed heat displacement'] =.3

## default values for yaml key/Value pairs
yaml_defaults = deepcopy(ashp_base.yaml_defaults)
    
## order to save yaml
yaml_order = deepcopy(ashp_base.yaml_order) 

## comments for the yaml key/value pairs
yaml_comments = deepcopy(ashp_base.yaml_comments)

       
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = deepcopy(ashp_base.yaml_import_lib)
    
raw_data_files = deepcopy(ashp_base.raw_data_files)

## list of wind preprocessing functions
preprocess_funcs = [deepcopy(ashp_base.preprocess)]

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = deepcopy(ashp_base.yaml_not_to_save)
    
## component summary
def component_summary (coms, res_dir):
    """
    save thes the summary for biomass cordwood
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
            
            ashp = coms[c]['model'].comps_used[COMPONENT_NAME]
            try:
                tcr = ashp.total_cap_required
                price =  float(ashp.electricity_prices.ix[ashp.start_year])
                #~ print float(ashp.electricity_prices.ix[ashp.start_year])
            except AttributeError:
                price = 0
                tcr = 0

            try:
                intertie = coms[c]['model'].cd.parent
            except AttributeError:
                intertie = c
               
            try:
                break_even = ashp.break_even_cost
            except AttributeError:
                break_even = 0
               
            
            try:
                levelized_cost = ashp.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0
            
            l = [c, 
                 ashp.average_cop,
                 ashp.heat_displaced_sqft,
                 tcr,
                 price,
                 ashp.electric_consumption,
                 ashp.heating_oil_saved,
                 break_even,
                 levelized_cost,
                 ashp.get_NPV_benefits(),
                 ashp.get_NPV_costs(),
                 ashp.get_NPV_net_benefit(),
                 ashp.get_BC_ratio(),
                 intertie,
                 ashp.reason
                ]
            out.append(l)
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    
    cols = ['Community',
            "ASHP Non-Residential Average Coefficient of Performance (COP)",
            'Heat Displacement square footage [Sqft]',
            'ASHP Non-Residential Total Nameplate Capacity Needed',
            'Electricity Price [$/kWh]',
            'ASHP Non-Residential kWh consumed per year',
            "ASHP Non-Residential Displaced Heating Oil [Gal]",
            'Break Even Diesel Price [$/gal]',
            'Levelized Cost Of Energy [$/MMBtu]',
            'ASHP Non-Residential NPV benefits [$]',
            'ASHP Non-Residential NPV Costs [$]',
            'ASHP Non-Residential NPV Net benefit [$]',
            'ASHP Non-Residential Benefit Cost Ratio',
            'Intertie',
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
prereq_comps = ['non-residential buildings']

class ASHPNonResidential (ashp_base.ASHPBase):
    """
    cordwood biomass componenet
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
        super(ASHPNonResidential, self).__init__(community_data, forecast,
                                                    diag, prerequisites)

        self.reason = "OK"
                        
        ### ADD other intiatzation stuff
        self.ashp_sector_system = "non-residential"
        
    def load_prerequisite_variables (self, comps):
        """
        load variables from prerequisites
        
        pre:
             prerequisites: dictonary of componentes
        """
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1].split('_')[0] != 'ASHP_res':
            return 
        non_res = comps['non-residential buildings']
        self.non_res_sqft = non_res.refit_sqft_total
    
        try:
            self.avg_gal_per_sqft = non_res.baseline_fuel_Hoil_consumption/ \
                                                            self.non_res_sqft
        except ZeroDivisionError:
            self.avg_gal_per_sqft = 0
        
        
    def calc_heat_energy_produced_per_year (self):
        """
        """
        self.heat_displaced_sqft = self.non_res_sqft * self.comp_specs[ 'percent sqft assumed heat displacement']
        average_net_btu_per_hr_pr_sf = self.avg_gal_per_sqft * self.comp_specs["heating oil efficiency"]*(1/constants.mmbtu_to_gal_HF)*1e6/ constants.hours_per_year
        self.heat_energy_produced_per_year = average_net_btu_per_hr_pr_sf * self.heat_displaced_sqft /1e6 * constants.hours_per_year
                        
        #~ print self.heat_energy_produced_per_year
        
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
        if len(tag) > 1 and tag[1] != 'ASHP_non-res':
            self.run = False
            self.reason = "Not a ASHP_non-res project"
            return 
        
        if self.cd["model heating fuel"]:
            self.calc_heat_energy_produced_per_year()
            self.calc_ashp_system_pramaters()
            
        if self.cd["model financial"]:
            self.calc_baseline_heating_oil_cost()
            self.calc_proposed_ashp_operation_cost()
            
            self.calc_capital_costs()
            
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            self.calc_annual_total_savings()
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
        #~ print 'self.monthly_value_table'
        #~ print self.monthly_value_table
        #~ print 'self.electric_consumption',self.electric_consumption
        #~ print 'self.heating_oil_saved',self.heating_oil_saved
        #~ print 'self.average_cop',self.average_cop
        #~ print 'self.baseline_heating_oil_cost',self.baseline_heating_oil_cost
        #~ print 'self.proposed_ashp_operation_cost',self.proposed_ashp_operation_cost
        #~ print self.capital_costs
        #~ print self.benefit_cost_ratio
            self.calc_levelized_costs(self.comp_specs["o&m per year"])


    def calc_capital_costs (self):
        """
        calculate the captial costs
        """
        min_tem = float(self.comp_specs['data'].ix['Minimum Temp'].astype(float))
        temps = self.comp_specs['perfromance data']['Temperature']
        percent = self.comp_specs['perfromance data']['Percent of Total Capacity']
        percent_of_total_cap = min(percent)
        if min_tem > min(temps):
            m, b = np.polyfit(temps,percent,1) 
            percent_of_total_cap = m * min_tem + b
            
        peak_btu_per_hr_per_sf = self.avg_gal_per_sqft * (1/constants.mmbtu_to_gal_HF) * 1e6 * float(self.comp_specs['data'].ix['Peak Month % of total']) /24/31
        peak_btu_per_hr =  peak_btu_per_hr_per_sf*self.heat_displaced_sqft
        self.total_cap_required = 2 * peak_btu_per_hr / percent_of_total_cap
        
        
        self.capital_costs = self.total_cap_required/self.comp_specs["btu/hrs"]* self.comp_specs["cost per btu/hrs"]*self.regional_multiplier
        
    def save_component_csv (self, directory):
        """
        save the component output csv in directory
        """
        if not self.run:
            return
        years = np.array(range(self.project_life)) + self.start_year
    
        try:
            tcr = self.total_cap_required
            prices = self.electricity_prices.values.T[0].tolist()
        except AttributeError:
            tcr = 0
            prices = 0
            
        #~ print prices
        df = DataFrame({
            "Community":self.cd['name'],
            "Non-residential ASHP: Average Coefficient of Performance (COP)": 
                                                    self.average_cop,
            'Non-residential ASHP: Heat Displacement square footage (sqft)':
                                                    self.heat_displaced_sqft,
            'Non-residential ASHP:'
                    ' Total Nameplate Capacity Needed (MMBtu/hour)': 
                                                    tcr,
            'Non-residential ASHP: Electricity Price ($/kWh)': 
                                                    prices,
            'Non-residential ASHP: kWh consumed per year (kWh/year)':
                                                    self.electric_consumption,
            "Non-residential ASHP: Displaced Heating Oil (gallons/year)": 
                                                    self.heating_oil_saved,
            "Non-residential ASHP: Project Capital Cost ($/year)": 
                                                    self.get_capital_costs(),
            "Non-residential ASHP: Total Cost Savings ($/year)": 
                                                self.get_total_savings_costs(),
            "Non-residential ASHP: Net Benefit ($/year)": 
                                                self.get_net_beneft(),
                       }, years)

        order = ["Community", 
            "Non-residential ASHP: Average Coefficient of Performance (COP)",
            'Non-residential ASHP: Heat Displacement square footage (sqft)',
            'Non-residential ASHP: '
                            'Total Nameplate Capacity Needed (MMBtu/hour)',
            'Non-residential ASHP: Electricity Price ($/kWh)', 
            'Non-residential ASHP: kWh consumed per year (kWh/year)',
            "Non-residential ASHP: Displaced Heating Oil (gallons/year)", 
            "Non-residential ASHP: Project Capital Cost ($/year)",
            "Non-residential ASHP: Total Cost Savings ($/year)", 
            "Non-residential ASHP: Net Benefit ($/year)"]
                
        fname = os.path.join(directory,
                                   self.cd['name'] + '_' +\
                                   self.component_name + "_output.csv")
        fname = fname.replace(" ","_")
        
        # save to end of project(actual lifetime)
        df[order].ix[:self.actual_end_year].to_csv(fname, index_label="Year")
        
        fname = os.path.join(directory,
                                    self.cd['name'] + '_' +\
                                    self.component_name + "_montly_table.csv")
        fname = fname.replace(" ","_")
        
        self.monthly_value_table.to_csv(fname)


component = ASHPNonResidential

