"""
wastewater.py
Water & Wastewater Systems

ross spicer
created: 2015/09/09

    python mock-up of eff(W & WW) tab. 
"""
import numpy as np

from annual_savings import AnnualSavings
from community_data import CommunityData
from forecast import Forecast

class WaterWastewaterSystems (AnnualSavings):
    """
    this class mocks up the Eff(w & ww) tab in the spreed sheet
    """
    
    def __init__ (self, community_data, forecast):
        """ 
        Class initialiser 
        
        pre-conditions:
            
        
        Post-conditions: 
            The class members are set to the initial values.
        """
        self.component_name = 'water wastewater'
          
        self.cd = community_data.get_section('community')
        self.comp_specs = community_data.get_section('water wastewater')
        
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"])
        
        
      
        self.cost_per_person = self.comp_specs['average refit cost'] * \
      community_data.get_section('construction multipliers')[self.cd["region"]] 
       
        self.forecast = forecast
        
        self.hdd = self.cd["HDD"]
        self.pop = self.forecast.base_pop
        self.system_type = self.comp_specs["system type"] 
        self.forecast = forecast
        
        
        self.population_fc = self.forecast.get_population(self.start_year,
                                                                 self.end_year)
        
    def calc_annual_electric_savings (self):
        """
        calculate the annual electric savings
        pre:
             TODO: write this 
        post:
            self.annual_electric_savings is an np.array of $/year values
        """
        self.calc_base_electric_savings()
        self.annual_electric_savings = self.baseline_kWh_cost
        
    def calc_proposed_electric_savings (self):
        """
        calcualte the savings for the proposed electric savings
        pre:
            TODO: write this 
        post:
           self.proposed_electric_savings is an np.array of $/year values 
        """
        pass
    
    def calc_base_electric_savings (self):
        """
        calcualte the savings for the base electric savings
        pre:
            TODO: write this 
        post:
           self.baseline_kWh_cost is an np.array of $/year values 
        """
        self.baseline_kWh_cost = np.zeros(self.project_life)
        # kWh/yr*$/kWh
        cost = self.baseline_kWh_consumption * self.cd["elec non-fuel cost"] 
        self.baseline_kWh_cost += cost #$/yr
    
    
    def calc_annual_heating_savings (self):
        """
        calculate the annual heating savings 
        pre:
             TODO: write this 
        post:
            self.annual_heating_savings is an np.array of $/year values
        """
        self.calc_proposed_heating_savings()
        self.calc_base_heating_savings()
        
        # $ / yr
        self.annual_heating_savings = self.baseline_HF_cost - \
                                            self.refit_HF_cost
        
    def calc_proposed_heating_savings (self):
        """
        calcualte the savings for the proposed heating savings
        pre:
            TODO: write this 
        post:
           self.refit_HF_cost is an np.array of $/year values 
        """
        self.refit_HF_cost = np.zeros(self.project_life)
        fuel_cost = self.diesel_prices + self.cd['heating fuel premium']# $/gal
        # are there ever o&m costs
        # $/gal * gal/yr = $/year 
        self.refit_HF_cost += self.refit_HF_consumption * \
                                                                    fuel_cost
        
    
    def calc_base_heating_savings (self):
        """
        calcualte the savings for the base heating savings
        pre:
            TODO: write this 
        post:
           self.baseline_HF_cost is an np.array of $/year values 
        """
        self.baseline_HF_cost = np.zeros(self.project_life)
        fuel_cost = self.diesel_prices + self.cd['heating fuel premium'] #$/gal
        # $/gal * gal/yr = $/year 
        self.baseline_HF_cost += self.baseline_HF_consumption * fuel_cost #$/yr
        
    def run (self):
        """
        runs the model for the inputs section of the wastewater tab
        pre-conditions:
            Class should have be set up properly, as described in __init__ 
        post-conditions:
            All output values will be calculated and usable
        """
        
        self.calc_baseline_kWh_consumption()
        self.calc_baseline_HF_consumption()
        
        self.calc_refit_kWh_consumption()
        self.calc_refit_HF_consumption()
        
        #~ self.calc_savings_electricity()
        #~ self.calc_savings_heating_feul()
        self.calc_capital_costs()
    
        #~ self.calc_post_savings_values()
        #~ self.forecast.set_www_HF_fuel_forecast(self.baseline_HF_consumption, 
                                               #~ self.start_year)
        
        
        #~ self.get_diesel_prices()
        #~ self.calc_annual_electric_savings()
        #~ self.calc_annual_heating_savings()
        #~ self.calc_annual_total_savings()
        
        #~ self.calc_annual_costs(self.cd['interest rate'])
        #~ self.calc_annual_net_benefit()
        
        #~ self.calc_npv(self.cd['discount rate'], 2014)
    
    def calc_baseline_kWh_consumption (self):
        """
        calculate electric savings
        
        pre:
            "w&ww_energy_use_electric" is a number
            self.pop & self.hdd should be numbers
            self.system_type should be a ww system type
            "w&ww_energy_use_known" is a boolean
        post:
            self.baseline_kWh_consumption will be a number
        """
        if self.comp_specs["energy use known"]:
            self.baseline_kWh_consumption = self.comp_specs['data'].ix['kWh/yr']
        else: #if not self.cd["w&ww_energy_use_known"]:
            hdd_coeff = np.float64(self.comp_specs['data'].ix['HDD kWh'])
            pop_coeff = np.float64(self.comp_specs['data'].ix['pop kWh'])
            
            self.baseline_kWh_consumption = \
                            (self.hdd * hdd_coeff + self.pop * pop_coeff) + \
                            ((self.population_fc - self.pop) * pop_coeff)
                            
    def calc_baseline_HF_consumption (self):
        """
        calculate heating fuel savings
        
        pre:
            "w&ww_energy_use_hf" is a number
            self.pop & self.hdd should be numbers
            self.system_type should be a ww system type
            "w&ww_energy_use_known" is a boolean
            hr_coeff should be a number (0 < hr_coeff <= 1)?
        post:
            self.baseline_HF_consumption will be a number
        """
        if self.comp_specs["energy use known"]:
            self.baseline_HF_consumption = \
                            np.float64(self.comp_specs['data'].ix['HF used'])
        else: #if not self.cd["energy_use_known"]:
            hr_used = self.comp_specs['heat recovery used']
            hr_coeff =  self.comp_specs['heat recovery multiplier'][hr_used]
            hdd_coeff = np.float64(self.comp_specs['data'].ix['HDD HF'])
            pop_coeff = np.float64(self.comp_specs['data'].ix['pop HF'])
            
            self.baseline_HF_consumption = \
                    ((self.hdd * hdd_coeff+ self.pop * pop_coeff) * hr_coeff) +\
                    ((self.population_fc - self.pop) * pop_coeff)

    def calc_refit_kWh_consumption (self):
        """
        calculate post refit kWh use
        
        pre:
            self.baseline_kWh_consumption should be calculated
        post:
            self.refit_kWh_consumption is calculated
        """
        #~ consumption = np.float64(self.comp_specs['data'].ix['kWh/yr w/ retro'])
        #~ if np.isnan(consumption):
        percent = 1 - self.comp_specs['electricity refit reduction']
        consumption = self.baseline_kWh_consumption * percent
         
        self.refit_kWh_consumption = consumption 

    def calc_refit_HF_consumption (self):
        """
        calculate post refit HF use
        
        pre:
            self.baseline_HF_consumption should be calculated
        post:
            self.refit_HF_consumption is calculated
        """
        #~ consumption = np.float64(self.comp_specs['data'].ix['HF w/Retro'])
        #~ if np.isnan(consumption):
        percent = 1 - self.comp_specs['heating fuel refit reduction']
        consumption = self.baseline_HF_consumption * percent
         
        self.refit_HF_consumption = consumption 
        
    #~ def calc_savings_kWh_consumption (self):
        

    #~ def calc_savings_electricity (self, coeff = .25):
        #~ """
        #~ calculate possible electricity savings
        
        #~ pre:
            #~ "w&ww_audit_savings_elec" is a number
            #~ "w&ww_audit_preformed" is a bool
            #~ self.baseline_kWh_consumption should be calculated 
            #~ coeff should be a number
        #~ post:
            #~ self.savings_electricity will be a number (kWh)
        #~ """
        #~ if  self.comp_specs["audit preformed"]:
            #~ self.savings_electricity = \
                    #~ self.cdself.comp_specs['data'].ix['kWh/yr w/ retro']
        #~ else: # if not self.comp_sepcs["audit preformed"]:
            #~ self.savings_electricity = self.baseline_kWh_consumption * coeff
        
    #~ def calc_savings_heating_feul (self, coeff = .35):
        #~ """
        #~ calculate possible hf savings
        
        #~ pre:
            #~ "w&ww_audit_savings_hf" is a number
            #~ "w&ww_audit_preformed" is a boolean
            #~ self.baseline_HF_consumption should be calculated 
            #~ coeff should be a number
        #~ post:
            #~ self.savings_heating_fuel will be a number (gal)
        #~ """
        #~ if  self.comp_specs["audit preformed"]:
            #~ self.savings_electricity = \
                    #~ self.cdself.comp_specs['data'].ix['HF w/Retro']
        #~ else: # if not self.comp_sepcs["audit preformed"]:
            #~ self.savings_heating_fuel = self.baseline_HF_consumption * coeff
            
    def calc_capital_costs (self, cost_per_person = 450):
        """
        calculate the capital costs
        
        pre:
            "w&ww_audit_cost" is a number
            "w&ww_audit_preformed" is a boolean
            cost_per_person is a dolar value per person > 0
            self.pop > 0
        post:
            self.captial_costs will be a dollar value
        """
        self.capital_costs = self.comp_specs["audit cost"]
        if not self.comp_specs["audit preformed"]:
            self.capital_costs = float(self.comp_specs["audit cost"]) + \
                                        self.pop *  self.cost_per_person
    
        
    #~ def calc_post_savings_values (self):
        #~ """
            #~ calculate the post savings estimates for heating fuel and 
        #~ electricity consumption 
        
        #~ pre:
            #~ self.baseline_kWh_consumption, self.savings_electricty, self.baseline_HF_consumption, and
        #~ self.savings_heating_fuel are numbers(kWh, kWh, Gallons HF, Gallons HF)
        #~ post:
            #~ post_savings_electricity is a number (kWh)
            #~ post_savings_heating_fuel is a number (Gallons)
        #~ """
        #~ self.refit_kWh_consumption = self.baseline_kWh_consumption - \
                                        #~ self.savings_electricity
        #~ self.refit_HF_consumption = self.baseline_HF_consumption - \
                                         #~ self.savings_heating_fuel

       
component = WaterWastewaterSystems
    
def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../data/","../test_case/manley_data.yaml")
    fc = Forecast(manley_data)
    ww = WaterWastewaterSystems(manley_data, fc)
    ww.run()
    print ""
    #~ print round(ww.benefit_npv,0)
    #~ print round(ww.cost_npv,0)
    #~ print round(ww.benefit_cost_ratio ,2)
    #~ print round(ww.net_npv,0)
    return ww, fc # return the object for further testing

