"""
component.py

    Air Source Heat Pumps - Non-Residential component body
"""
import numpy as np
from pandas import DataFrame
import os

from aaem.components.annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants
from config import COMPONENT_NAME, UNKNOWN

import aaem.components.ashp_base as ashp_base

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
        non_res = comps['Non-residential Energy Efficiency']
    
        try:
            self.non_res_sqft = non_res.total_sqft_to_retrofit
            self.avg_gal_per_sqft = non_res.baseline_fuel_Hoil_consumption/ \
                                                            self.non_res_sqft
        except (ZeroDivisionError, AttributeError):
            self.non_res_sqft = 0
            self.avg_gal_per_sqft = 0
        
        
    def calc_heat_energy_produced_per_year (self):
        """
        """
        self.heat_displaced_sqft = self.non_res_sqft * self.comp_specs[ 'percent sqft assumed heat displacement']
        average_net_btu_per_hr_pr_sf = self.avg_gal_per_sqft * self.comp_specs["heating oil efficiency"]*(1/constants.mmbtu_to_gal_HF)*1e6/ constants.hours_per_year
        self.heat_energy_produced_per_year = average_net_btu_per_hr_pr_sf * self.heat_displaced_sqft /1e6 * constants.hours_per_year
                        
        #~ print self.heat_energy_produced_per_year
        
    def run (self, scalers = {'capital costs':1.0}):
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
            self.calc_annual_costs(self.cd['interest rate'],
                                            scalers['capital costs'])
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
        calculate the capital costs
        """
        min_tem = float(self.comp_specs['data']\
                                .ix['Minimum Temp'].astype(float))
        temps = self.comp_specs['perfromance data']['Temperature']
        percent = self.comp_specs['perfromance data']\
                                    ['Percent of Total Capacity']
        percent_of_total_cap = min(percent)
        if min_tem > min(temps):
            m, b = np.polyfit(temps,percent,1) 
            percent_of_total_cap = m * min_tem + b
        percent_of_total_cap = min(1.0, percent_of_total_cap)
        
        peak_btu_per_hr_per_sf = self.avg_gal_per_sqft * \
                                    (1/constants.mmbtu_to_gal_HF) * \
                                    1e6 * \
                                    float(self.comp_specs['data']\
                                        .ix['Peak Month % of total'])\
                                    / 24 / 31
        peak_btu_per_hr =  peak_btu_per_hr_per_sf*self.heat_displaced_sqft
        self.total_cap_required = 2 * peak_btu_per_hr / percent_of_total_cap
        
        
        self.capital_costs = self.total_cap_required/ \
                                    self.comp_specs["btu/hrs"] *\
                                    self.comp_specs["cost per btu/hrs"] *\
                                    self.regional_multiplier
        
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
                                   self.component_name.lower() + "_output.csv")
        fname = fname.replace(" ","_")
        
        # save to end of project(actual lifetime)
        df[order].ix[:self.actual_end_year].to_csv(fname, index_label="Year")
        
        fname = os.path.join(directory,
                            self.cd['name'] + '_' +\
                            self.component_name.lower() + "_montly_table.csv")
        fname = fname.replace(" ","_")
        
        self.monthly_value_table.to_csv(fname)
