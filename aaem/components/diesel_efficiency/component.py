"""
component.py

diesel_efficiency component
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

class DieselEfficiency(AnnualSavings):
    """
    diesel efficieny component
    """
    def __init__ (self, community_data, forecast, 
                        diag = None, prerequisites = {}):
        """
        Class initialiser

        input:
            community_data: a CommunityData object
            forecast: a Forecast object
            diag: diagnostics object (optional)
            prerequisites: dictionay of prerequisit componentes
        
        output:
            None

        peconditions: 
            None
        
        postconditions:
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
        
        
    def run (self, scalers = {'captial costs':1.0}):
        """
        run the forecast model

        postconditions:
            the component will have been run. If run was completed 
        self.run == True, otherwise self.reason will indcate where failure 
        occured
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
            
        preconditions:
            self.forecast: the forecast for this component should be run prior
                to calling this function
        
        postconditions:
            self.generation: generation per year (kWh) [np.array][floats]
            self.average_load: averge load on system year 1 (kW/yr) [float]
        """
        self.generation = self.forecast.generation_by_type['generation diesel']\
                                .ix[self.start_year:self.end_year-1].values
        self.average_load = self.generation[0] / constants.hours_per_year
        #~ print 'self.average_load',self.average_load
 

    def calc_baseline_generation_fuel_use (self):
        """
            calculates baseline generation fuel use
        
        preconditions:
            self.cd: "diesel generation efficiency" should get the 
                diesel generation efficiency (Gal/kWh) [float]
            self.generation:  generation per year (kWh) [np.array][floats]
       
        postcondtions:
            self.baseline_diesel_efficiency will be the diesel generation 
                efficiency before any imporvements are made (Gal/kWh) [float]
            self.baseline_generation_fuel_use: fuel used per year (gal) 
                [np.array][floats]
        """
        self.baseline_diesel_efficiency = \
                        self.cd["diesel generation efficiency"]
        self.baseline_generation_fuel_use = self.generation / \
                                        self.baseline_diesel_efficiency 
    
    def calc_proposed_generation_fuel_use (self):
        """
            calculates proposed generation fuel use
        
        preconditions:
            self.cd: "diesel generation efficiency" should get the 
                diesel generation efficiency (Gal/kWh) [float]
            self.comp_specs: 'efficiency improvment' key should get the 
                improvement factor (float)
            self.generation:  generation per year (kWh) [np.array][floats]
       
        postcondtions:
            self.proposed_diesel_efficiency will be the diesel generation 
                efficiency before any imporvements are made (Gal/kWh) [float]
            self.proposed_generation_fuel_use: fuel used per year (gal) 
                [np.array][floats]
        """
        self.proposed_diesel_efficiency = \
                        self.cd["diesel generation efficiency"] * \
                        self.comp_specs['efficiency improvment']
        self.proposed_generation_fuel_use = self.generation / \
                                        self.proposed_diesel_efficiency 
                                        
    def calc_max_capacity (self):
        """
            calculate max load and capacity
            
        preconditions:
            self.generation:  generation per year (kWh) [np.array][floats]
            
        postconditions: 
            self.max_load: maximum load over project lifetime (KWh) [float]
            self.max_capacity: proposed max capacity (KWh) [float]
        """
        self.max_load = self.generation[:self.actual_project_life].max() / \
                                                    constants.hours_per_year
        self.max_capacity = 13.416 * self.max_load ** (1 - 0.146)  
    
    def calc_capital_costs (self):
        """
            calculate the capital costs
            
        preconditions:
            self.max_capacity: proposed max capacity (KWh) [float]
        
        postconditions:
            self.capital_costs: total cost of imporvments ($) [float] 
        """
        self.capital_costs = (1.8 + .001 * self.max_capacity) * 1000000
    
    def calc_oppex (self):
        """
            calculate the operational costs
            
        preconditions:
            self.average_load: average load (KWh) [float]
            self.comp_specs: 'o&m costs' is a dictionary with keys as the 
                cielings for the costs, and a key 'else' for anything greater 
                than the last cieling
        
        postconditions:
            self.oppex: operational costs per year ($) [float] 
        """
        key = 'else'
        for max_load in sorted(self.comp_specs['o&m costs'].keys())[:-1]:
            if self.average_load <= max_load:
                key = max_load
                break
        
        self.oppex = self.comp_specs['o&m costs'][key]
        
        
    def calc_annual_electric_savings (self):
        """
            calculate annual electric savings created by the project
        
        precodtions:
            Note: for the arrays in this function index 0 should represent the 
                start year self.start year and each subsequent index the 
                next year 
            self.diesel_prices: diesel prices ($/gal) [np.array][floats]
            self.baseline_generation_fuel_use: (gal) [np.array][floats]
            self.proposed_generation_fuel_use (gal) [np.array][floats]
            self.oppex: ($) [float]
            
        postconditions:
            self.annual_electric_savings: electric savings ($/year) 
                [np.array][floats]
        """
        price = self.diesel_prices
        
        base = self.baseline_generation_fuel_use * price + self.oppex
        proposed = self.proposed_generation_fuel_use * price + self.oppex
        
        self.annual_electric_savings = base - proposed
        
    def calc_annual_heating_savings (self):
        """
            calculate annual heating savings created by the project
            
        postconditions:
            self.annual_heating_savings are 0
        """
        self.annual_heating_savings = 0
        
    def get_fuel_total_saved (self):
        """
        preconditions:
            self.baseline_generation_fuel_use: [np.array][floats]
            self.proposed_generation_fuel_use: [np.array][floats]
        
        ouptut:
            returns the total fuel saved in gallons
        """
        return self.baseline_generation_fuel_use - \
                self.proposed_generation_fuel_use
    
    def get_total_enery_produced (self):
        """
        ouptut:
            returns the total energy produced
        """
        return self.get_fuel_total_saved() / constants.mmbtu_to_gal_HF
        
    def save_component_csv (self, directory):
        """
            save the output from the component.
        
        precondtitions:
            self.run: True for the output to be saved
            
        output:
            saves "<community>_diesel_efficienct_output.csv"
        """
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
