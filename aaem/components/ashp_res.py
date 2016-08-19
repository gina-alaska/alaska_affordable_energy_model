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
COMPONENT_NAME = "ASHP residential"

## List of yaml key/value pairs
yaml = deepcopy(ashp_base.yaml)
yaml[ "btu/hrs"] = 18000
yaml[ "cost per btu/hrs" ] = 6000 

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
            
            kw_exess = ashp.monthly_value_table['kWh consumed'].max()/\
                                (24 * 31)
            try:
                peak_monthly_btu_hr_hh = ashp.peak_monthly_btu_hr_hh
                price =  float(ashp.electricity_prices.ix[ashp.start_year])
                #~ print float(ashp.electricity_prices.ix[ashp.start_year])
            except AttributeError:
                peak_monthly_btu_hr_hh = 0
                price = 0
           
            try:
                intertie = coms[c]['model'].cd.parent
            except AttributeError:
                intertie = c
            try:
                levelized_cost = ashp.levelized_cost_of_energy
            except AttributeError:
                levelized_cost = 0
                
            try:
                break_even = ashp.break_even_cost
            except AttributeError:
                break_even = 0
                
            ashp.get_diesel_prices()
            diesel_price = float(ashp.diesel_prices[0].round(2))
            hf_price = diesel_price + ashp.cd['heating fuel premium']   
            
            l = [c, 
                 ashp.average_cop,
                 ashp.num_houses,
                 peak_monthly_btu_hr_hh,
                 price,
                 ashp.electric_consumption,
                 kw_exess,
                 ashp.heating_oil_saved,
                 ashp.electric_heat_energy_reduction,
                 diesel_price,
                 hf_price,
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
            #~ print c
            #~ print e
            pass
    
    cols =  ['Community',
             "ASHP Residential Average Coefficient of Performance (COP)",
             'Number Houses',
             'ASHP Residential Peak Household Monthly Btu/hr',
             'Electricity Price [$/kWh]',
             'ASHP Residential kWh consumed per year',
             "ASHP Residential Excess Generation Capacity"
                                        " Needed for Peak Monthly Load (kW)",
             "ASHP Residential Displaced Heating Oil [Gal]",
             "ASHP Residential Displaced Electricity [kWh]",
             "Diesel Price - year 1 [$/gal]",
             "Heating Fuel Price - year 1 [$/gal]",
             'Break Even Heating Fuel Price [$/gal]',
             'Levelized Cost Of Energy [$/MMBtu]',
             'ASHP Residential NPV benefits [$]',
             'ASHP Residential NPV Costs [$]',
             'ASHP Residential NPV Net benefit [$]',
             'ASHP Residential Benefit Cost Ratio',
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
prereq_comps = ['residential buildings']

class ASHPResidential (ashp_base.ASHPBase):
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
        super(ASHPResidential, self).__init__(community_data, forecast,
                                                    diag, prerequisites)

        self.reason = "OK"
                        
        ### ADD other intiatzation stuff
        self.ashp_sector_system = "residential"
        
    def load_prerequisite_variables (self, comps):
        """
        load variables from prerequisites
        
        pre:
             prerequisites: dictonary of componentes
        """
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1].split('_')[0] != 'ASHP_res':
            return 
        res = comps['residential buildings']
        self.pre_ashp_heating_oil_used =  res.init_HF
        self.pre_ashp_heating_electricty_used = res.init_kWh
        self.num_houses = res.init_HH
        self.precent_heated_oil = res.comp_specs['data'].T["Fuel Oil"]
        self.precent_heated_elec = res.comp_specs['data'].T["Electricity"]
        #~ print self.pre_ashp_heating_oil_used
        #~ print self.num_houses
        
        
    def calc_heat_energy_produced_per_year (self):
        """
        """
        self.heat_energy_produced_per_year = \
                        self.pre_ashp_heating_oil_used * \
                        self.comp_specs["heating oil efficiency"]*\
                        (1/constants.mmbtu_to_gal_HF)
        #~ print self.heat_energy_produced_per_year
       
    def calc_electric_heat_energy_reduction (self):
        """
        """
        self.electric_heat_energy_reduction = \
                        self.pre_ashp_heating_electricty_used/ self.average_cop
        
    
    def calc_electric_heat_energy_savings (self):
        """
        """
        self.electric_heat_energy_savings = \
                        self.electric_heat_energy_reduction * \
                        self.electricity_prices
        self.electric_heat_energy_savings = \
                        self.electric_heat_energy_savings.values.T[0]
        
        
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
        if len(tag) > 1 and tag[1] != 'ASHP_res':
            self.run = False
            self.reason = "Not a ASHP_res project"
            return 
        
        if self.cd["model heating fuel"]:
            self.calc_heat_energy_produced_per_year()
            self.calc_ashp_system_pramaters()
            self.calc_electric_heat_energy_reduction()
            
        if self.cd["model financial"]:
            self.calc_baseline_heating_oil_cost()
            self.calc_proposed_ashp_operation_cost()
            
            self.calc_capital_costs()
            
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            
            self.calc_electric_heat_energy_savings()
            #~ print self.electric_heat_energy_savings
            self.annual_heating_savings += self.electric_heat_energy_savings
            
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
            self.calc_levelized_costs(self.proposed_ashp_operation_cost)
        else:
            self.reason = "Financial Modeling disabled"

    def calc_capital_costs (self):
        """
        calculate the captial costs
        """
        heating_oil = ((self.pre_ashp_heating_oil_used/self.num_houses)*\
                        self.comp_specs["heating oil efficiency"]) / \
                        constants.mmbtu_to_gal_HF *1e6/ \
                        constants.hours_per_year
        electric_heat = (self.pre_ashp_heating_electricty_used/self.num_houses)\
                        / constants.mmbtu_to_kWh *1e6/ constants.hours_per_year
                        
        average_btu_per_hr =  heating_oil + electric_heat
        
        peak_monthly_btu_hr_hh = \
            float(float(self.comp_specs['data'].ix['Peak Month % of total']) *\
            average_btu_per_hr * 12 / \
            (self.precent_heated_oil+self.precent_heated_elec))
            
        self.peak_monthly_btu_hr_hh = peak_monthly_btu_hr_hh
        
        
        min_tem = float(self.comp_specs['data']
                                .ix['Minimum Temp'].astype(float))
                                
        temps = self.comp_specs['perfromance data']['Temperature']
        
        percent = self.comp_specs['perfromance data']\
                                    ['Percent of Total Capacity']
                                    
        percent_of_total_cap = min(percent)
        if min_tem > min(temps):
            m, b = np.polyfit(temps,percent,1) 
            percent_of_total_cap = m * min_tem + b
        percent_of_total_cap = min(1.0, percent_of_total_cap)
        
        
        self.total_cap_required = 2 * self.peak_monthly_btu_hr_hh /\
                                        percent_of_total_cap
        ratio = self.total_cap_required  / self.comp_specs["btu/hrs"]
        if ratio < 1:
            self.diagnostics.add_note(self.component_name,
                "ratio of peak mothly btu/hr/hh to btu/hrs is 1 ")
            ratio = 1.0

        self.capital_costs = self.num_houses * \
                             round((ratio) * \
                             self.comp_specs["cost per btu/hrs"])* \
                             self.regional_multiplier

    def save_component_csv (self, directory):
        """
        save the component output csv in directory
        """
        if not self.run:
            return
        years = np.array(range(self.project_life)) + self.start_year
    
        try:
            val = self.peak_monthly_btu_hr_hh
            prices = self.electricity_prices.values.T[0].tolist()
        except AttributeError:
            val = 0
            prices = 0
            
        #~ print prices
        df = DataFrame({
                "Community": self.cd['name'],
                "Residential ASHP: Average Coefficient of Performance (COP)": self.average_cop,
                'Residential ASHP: Number Houses': self.num_houses,
                'Residential ASHP: Peak Household Monthly (Btu/hour)': val,
                'Residential ASHP: Electricity Price ($/kWh)':prices,
                'Residential ASHP: kWh consumed per year (kWh/year)':self.electric_consumption,
                "Residential ASHP: Displaced Heating Oil (gallons/year)": self.heating_oil_saved,
                "Residential ASHP: Project Capital Cost ($/year)": self.get_capital_costs(),
                "Residential ASHP: Total Cost Savings ($/year)": self.get_total_savings_costs(),
                "Residential ASHP: Net Benefit ($/year)": self.get_net_beneft(),
                       }, years)

        order = ["Community", 
                 "Residential ASHP: Average Coefficient of Performance (COP)",
                 'Residential ASHP: Number Houses', 
                 'Residential ASHP: Peak Household Monthly (Btu/hour)',
                 'Residential ASHP: Electricity Price ($/kWh)', 
                 'Residential ASHP: kWh consumed per year (kWh/year)',
                 "Residential ASHP: Displaced Heating Oil (gallons/year)", 
                 "Residential ASHP: Project Capital Cost ($/year)",
                 "Residential ASHP: Total Cost Savings ($/year)", 
                 "Residential ASHP: Net Benefit ($/year)"]
                
        fname = os.path.join(directory,
                                   self.cd['name'] + '_' +\
                                   self.component_name + "_output.csv")
        fname = fname.replace(" ","_")
        
        # save to end of project(actual lifetime)
        df[order].ix[:self.actual_end_year].to_csv(fname, index_label="Year")
        fname = os.path.join(directory,
                                   self.cd['name']+'_'+\
                                   self.component_name + "_montly_table.csv")
        fname = fname.replace(" ","_")
        
        self.monthly_value_table.to_csv(fname)



component = ASHPResidential

