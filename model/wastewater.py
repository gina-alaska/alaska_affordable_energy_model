"""
wastewater.py
Water & Wastewater Systems

ross spicer
created: 2015/09/09

    python mock-up of eff(W & WW) tab. 
"""
import numpy as np

from annual_savings import AnnualSavings
#~ # for live testing ---
#~ import annual_savings
#~ reload(annual_savings)
#~ AnnualSavings = annual_savings.AnnualSavings
#---------------------
from community_data import CommunityData
#~ import community_data
#~ reload(community_data)
#~ CommunityData = community_data.CommunityData
import aea_assumptions as AEAA
#~ reload(AEAA)
#~ from forecast import Forecast
import forecast
reload(forecast)
Forecast = forecast.Forecast

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
        self.cd = community_data
        
        self.hdd = self.cd["HDD"]
        self.pop = self.cd["population"] 
        self.system_type = self.cd["w&ww_system_type"] 
        self.forecast = forecast
        
    def calc_annual_electric_savings (self):
        """
        calculate the annual electric savings
        pre:
             TODO: write this 
        post:
            self.annual_electric_savings is an np.array of $/year values
        """
        self.calc_base_electric_savings()
        self.annual_electric_savings = self.base_electric_savings
        
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
           self.base_electric_savings is an np.array of $/year values 
        """
        self.base_electric_savings = np.zeros(self.project_life)
        # kWh/yr*$/kWh
        cost = self.savings_electricity * self.cd["res_non-PCE_elec_cost"]
        self.base_electric_savings += cost #$/yr
    
    
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
        self.annual_heating_savings = self.base_heating_savings - \
                                            self.proposed_heating_savings
        
    def calc_proposed_heating_savings (self):
        """
        calcualte the savings for the proposed heating savings
        pre:
            TODO: write this 
        post:
           self.proposed_heating_savings is an np.array of $/year values 
        """
        self.proposed_heating_savings = np.zeros(self.project_life)
        fuel_cost = self.diesel_prices + AEAA.heating_fuel_premium# $/gal
        #~ print fuel_cost
        # are there ever o&m costs
        # $/gal * gal/yr = $/year 
        self.proposed_heating_savings += self.post_savings_heating_fuel * \
                                                                    fuel_cost
        
    
    def calc_base_heating_savings (self):
        """
        calcualte the savings for the base heating savings
        pre:
            TODO: write this 
        post:
           self.base_heating_savings is an np.array of $/year values 
        """
        self.base_heating_savings = np.zeros(self.project_life)
        fuel_cost = self.diesel_prices + AEAA.heating_fuel_premium #$/gal
        # $/gal * gal/yr = $/year 
        self.base_heating_savings += self.heating_fuel * fuel_cost #$/yr
        
    def run (self):
        """
        runs the model for the inputs section of the wastewater tab
        pre-conditions:
            Class should have be set up properly, as described in __init__ 
        post-conditions:
            All output values will be calculated and usable
        """
        self.set_project_life_details(self.cd["w&ww_start_year"],
                                      self.cd["w&ww_lifetime"])
        
        self.calc_electricity_consumption()
        hrm = AEAA.heat_recovery_multiplier[self.cd["w&ww_heat_recovery_used"]]
        self.calc_heating_fuel_consumption(hrm)
        
        self.calc_savings_electricity()
        self.calc_savings_heating_feul()
        self.calc_capital_costs()
    
        self.calc_post_savings_values()
        self.forecast.set_www_HF_fuel_forecast(self.heating_fuel, 
                                               self.start_year)
        
        
        self.get_diesel_prices()
        self.calc_annual_electric_savings()
        self.calc_annual_heating_savings()
        self.calc_annual_total_savings()
        
        self.calc_annual_costs(AEAA.interest_rate)
        self.calc_annual_net_benefit()
        
        self.calc_npv(AEAA.discount_rate, 2014)
    
    def calc_electricity_consumption (self):
        """
        calculate electric savings
        
        pre:
            "w&ww_energy_use_electric" is a number
            self.pop & self.hdd should be numbers
            self.system_type should be a ww system type
            "w&ww_energy_use_known" is a boolean
        post:
            self.electricity will be a number
        """
        self.electricity = self.cd["w&ww_energy_use_electric"]
        if not self.cd["w&ww_energy_use_known"]:
            self.electricity = \
                               (self.hdd * AEAA.HDD_KWH[self.system_type] + \
                                self.pop * AEAA.POP_KWH[self.system_type])
            # update for 9/28 spread sheet 
            # forcast needs an update to get a range of years 
            self.forecast.forecast_population()
            self.electricity += (self.forecast.population[1:16] - \
                                 self.pop)*AEAA.POP_KWH[self.system_type]
                            
    def calc_heating_fuel_consumption (self, hr_coeff):
        """
        calculate heating fuel savings
        
        pre:
            "w&ww_energy_use_hf" is a number
            self.pop & self.hdd should be numbers
            self.system_type should be a ww system type
            "w&ww_energy_use_known" is a boolean
            hr_coeff should be a number (0 < hr_coeff <= 1)?
        post:
            self.heating_fuel will be a number
        """
        self.heating_fuel = self.cd["w&ww_energy_use_hf"]
        if not self.cd["w&ww_energy_use_known"]:
            self.heating_fuel = (self.hdd * AEAA.HDD_HF[self.system_type] + \
                                 self.pop * AEAA.POP_HF[self.system_type]) * \
                                 hr_coeff 
            # update for 9/28 spread sheet 
            # forcast needs an update to get a range of years 
            pop_fc = self.forecast.get_population(self.start_year,self.end_year)
            self.heating_fuel += (pop_fc - self.pop) * \
                                 AEAA.POP_HF[self.system_type]

    def calc_savings_electricity (self, coeff = .25):
        """
        calculate possible electricity savings
        
        pre:
            "w&ww_audit_savings_elec" is a number
            "w&ww_audit_preformed" is a bool
            self.electricity should be calculated 
            coeff should be a number
        post:
            self.savings_electricity will be a number (kWh)
        """
        self.savings_electricity = self.cd["w&ww_audit_savings_elec"]
        if not self.cd["w&ww_audit_preformed"]:
            self.savings_electricity = self.electricity * coeff
        
    def calc_savings_heating_feul (self, coeff = .35):
        """
        calculate possible hf savings
        
        pre:
            "w&ww_audit_savings_hf" is a number
            "w&ww_audit_preformed" is a boolean
            self.heating_fuel should be calculated 
            coeff should be a number
        post:
            self.savings_heating_fuel will be a number (gal)
        """
        self.savings_heating_fuel = self.cd["w&ww_audit_savings_hf"]
        if not self.cd["w&ww_audit_preformed"]:
            self.savings_heating_fuel = self.heating_fuel * coeff
            
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
        self.capital_costs = self.cd["w&ww_audit_cost"]
        cost_per_person = AEAA.ww_baseline_retrofit_cost * \
                                AEAA.construction_mulitpliers[self.cd["region"]]
        if not self.cd["w&ww_audit_preformed"]:
            self.capital_costs = float(AEAA.w_ww_audit_cost) + \
                                        self.pop * cost_per_person
    
        
    def calc_post_savings_values (self):
        """
            calculate the post savings estimates for heating fuel and 
        electricity consumption 
        
        pre:
            self.electricity, self.savings_electricty, self.heating_fuel, and
        self.savings_heating_fuel are numbers(kWh, kWh, Gallons HF, Gallons HF)
        post:
            post_savings_electricity is a number (kWh)
            post_savings_heating_fuel is a number (Gallons)
        """
        self.post_savings_electricity = self.electricity - \
                                        self.savings_electricity
        self.post_savings_heating_fuel = self.heating_fuel - \
                                         self.savings_heating_fuel
        
    def print_savings_chart (self):
        """
            print the savings chart to see the values in a way similar to  the 
        spread sheet.
        pre:
            the "estimates" should be numbers calling self.run() will do this
        """
        print "\tEst. Pre\tEst. Post\tEst. Savings"
        print "kWH\t" + str(int(round(self.electricity_init))) + "\t\t" + \
              str(int(round(self.post_savings_electricity))) + "\t\t" + \
              str(int(round(self.savings_electricity)))
        print "kWH\t" + str(int(round(self.heating_fuel))) + "\t\t" +\
              str(int(round(self.post_savings_heating_fuel))) + "\t\t" +\
              str(int(round(self.savings_heating_fuel)))
              
        print ""
        print "Capital Costs: $" + "{0:.2f}".format(round(self.capital_costs,2))
       
        
def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("community_data_template.csv",
                                "Manley Hot Springs")
    fc = Forecast(manley_data)
    ww = WaterWastewaterSystems(manley_data, fc)
    ww.run()
    #~ ww.print_savings_chart()
    print ""
    print round(ww.benefit_npv,0)
    print round(ww.cost_npv,0)
    print round(ww.benefit_cost_ratio ,2)
    print round(ww.net_npv,0)
    return ww, fc # return the object for further testing

