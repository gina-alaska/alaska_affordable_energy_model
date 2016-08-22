

import numpy as np
from pandas import DataFrame
import os


from aaem.components.annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants


from config import COMPONENT_NAME, UNKNOWN

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
        self.calc_max_capacity()
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
            self.calc_levelized_costs(0)
        
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
                                        
    def calc_max_capacity (self):
        """
        """
        self.max_load = self.generation[:self.actual_project_life].max() / \
                                                    constants.hours_per_year
        self.max_capacity = 13.416 * self.max_load ** (1 - 0.146)  
    
    def calc_capital_costs (self):
        """ Function Doc"""
        self.capital_costs = (1.8 + .001 * self.max_capacity) * 1000000
    
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
        
    def get_fuel_total_saved (self):
        """
        returns the total fuel saved in gallons
        """
        return self.baseline_generation_fuel_use - \
                self.proposed_generation_fuel_use
    
    def get_total_enery_produced (self):
        """
        returns the total energy produced
        """
        return self.get_fuel_total_saved() / constants.mmbtu_to_gal_HF
        
    def save_component_csv (self, directory):
        """
        save the output from the component.
        """
        #~ return
        if not self.run:
            return
        
        
        years = np.array(range(self.project_life)) + self.start_year

        
        df = DataFrame({
                "Diesel Efficiency: Generation (kWh/year)": self.generation,
                'Diesel Efficiency: Baseline Diesel'
                    ' Generator Efficiency [Gal/kWh]':
                                            self.baseline_diesel_efficiency,
                'Diesel Efficiency: Proposed Diesel'
                    ' Generator Efficiency [Gal/kWh]':
                                            self.proposed_diesel_efficiency,
                'Diesel Efficiency: Utility Diesel Baseline (gallons/year)':
                                        self.baseline_generation_fuel_use,
                'Diesel Efficiency: Utility Diesel Proposed (gallons/year)':
                                        self.proposed_generation_fuel_use,
                'Diesel Efficiency: Utility Diesel Displaced (gallons/year)':
                                        self.baseline_generation_fuel_use - \
                                        self.proposed_generation_fuel_use,
                "Diesel Efficiency: Electricity Cost Savings ($/year)": 
                                            self.get_electric_savings_costs(),
                "Diesel Efficiency: Project Capital Cost ($/year)": 
                                            self.get_capital_costs(),
                "Diesel Efficiency: Total Cost Savings ($/year)":
                                            self.get_total_savings_costs(),
                "Diesel Efficiency: Net Benefit ($/year)":
                                                self.get_net_beneft(),
                       }, years)

        df["Community"] = self.cd['name']
        
        ol = ["Community",
              "Diesel Efficiency: Generation (kWh/year)",
              'Diesel Efficiency: Baseline Diesel'
                    ' Generator Efficiency [Gal/kWh]',
              'Diesel Efficiency: Proposed Diesel'
                    ' Generator Efficiency [Gal/kWh]',
              'Diesel Efficiency: Utility Diesel Baseline (gallons/year)',
              'Diesel Efficiency: Utility Diesel Proposed (gallons/year)',
              'Diesel Efficiency: Utility Diesel Displaced (gallons/year)',
              "Diesel Efficiency: Electricity Cost Savings ($/year)",
              "Diesel Efficiency: Project Capital Cost ($/year)",
              "Diesel Efficiency: Total Cost Savings ($/year)",
              "Diesel Efficiency: Net Benefit ($/year)"]
        fname = os.path.join(directory,
                             self.cd['name'] + '_' + \
                             self.component_name + "_output.csv")
        fname = fname.replace(" ","_")
        
        df[ol].ix[:self.actual_end_year].to_csv(fname, index_label="Year")
