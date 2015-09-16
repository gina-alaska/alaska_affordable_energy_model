"""
wastewater.py
Water & Wastewater Systems

ross spicer
created: 2015/09/09

    python mock-up of eff(W & WW) tab. 
"""
import numpy as np

from annual_savings import AnnualSavings
from community_data import manley_data
## Wastewater assumptions

## heating degree days - kWh?
HDD_KWH = {"Circulating/Gravity": 3.93236229561503,
           "Circulating/Vac": 11.4132439375221,
           "Haul": 0,
           "Pressure/Gravity": -0.848162217309015,
           "Wash/HB": -0.528728194855285,
           }

## heating degree days - Gallons HF?
HDD_HF = {"Circulating/Gravity": 0.544867662390884,
           "Circulating/Vac": -0.297715988257898,
           "Haul": 0,
           "Pressure/Gravity": 2.2408614639956,
           "Wash/HB": 0.17155240756494,
           }

## Population - kWh?
POP_KWH = {"Circulating/Gravity": 54.4093002543652,
           "Circulating/Vac": 161.481419074818,
           "Haul": 69.7824047085659,
           "Pressure/Gravity": 263.448648548957,
           "Wash/HB": 144.393961746201,
           }
           
## Population - Gallons HF?
POP_HF = {"Circulating/Gravity": 3.57835240238995,
           "Circulating/Vac": 23.8252508422151,
           "Haul": 7.06151797216891,
           "Pressure/Gravity": -78.7469560579852,
           "Wash/HB": 22.3235825717145,
           }


heat_recovery_multiplier = {True:  0.5, 
                            False: 1.0
                           }

w_ww_audit_cost = 10000
project_life = 20 # years
start_year = 2016

interest_rate = .05
discount_rate = .03


class WaterWastewaterSystems (AnnualSavings):
    """
    this class mocks up the Eff(w & ww) tab in the spreed sheet
    """
    
    def __init__ (self, community_data):
        """ 
        Class initialiser 
        
        pre-conditions:
            hdd(int) is the number of heating degree days. Population(int) is 
        the population of the town. system_type(string) is one of the system 
        types used as keys to the assumption libraries. 
        energy_use_known, heat_recovery, audit_preformed(string) are set 
        to 'yes' or 'no'
        
        Post-conditions: 
            The class members are set to the initila values.
        """
        self.cd = community_data
        
        self.hdd = self.cd["HDD"]
        self.pop = self.cd["population"] 
        self.system_type = self.cd["w&ww_system_type"] 
        
    def calc_annual_electric_savings (self):
        """
        calculate the annual electric savings
        """
        self.annual_electric_savings = np.zeros(self.project_life)
        # calc poposed
        # calc base
        # set self.electric_savings to proposed - base
        
    
    def calc_annual_heating_savings (self):
        """
        calculate the annual heating savings 
        """
        self.annual_heating_savings = np.zeros(self.project_life)
        # same as calc_electric_savings work flow but for heating
        
    def run (self):
        """
        runs the model for the inputs section of the wastewater tab
        pre-conditions:
            Class should have be set up properly, as described in __init__ 
        post-conditions:
            All output values will be calculated and usable
        """
        self.set_project_life_details(start_year ,project_life)
        
        self.calc_electricity_consumption()
        hr_mult = heat_recovery_multiplier[self.cd["w&ww_heat_recovery_used"]]
        self.calc_heating_fuel_consumption(hr_mult)
        
        self.calc_savings_electricity()
        self.calc_savings_heating_feul()
        self.calc_capital_costs()
    
        self.calc_post_savings_values()
        
        #~ self.calc_capital_costs()
        self.calc_annual_electric_savings()
        self.calc_annual_heating_savings()
        self.calc_annual_total_savings()
        
        self.calc_annual_costs(interest_rate)
        self.calc_annual_benefit()
        
        self.calc_npv(discount_rate)
    
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
                               (self.hdd * HDD_KWH[self.system_type] + \
                                self.pop * POP_KWH[self.system_type])
                            
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
            self.heating_fuel = (self.hdd * HDD_HF[self.system_type] + \
                                 self.pop * POP_HF[self.system_type]) * \
                                 hr_coeff 

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
        if not self.cd["w&ww_audit_preformed"]:
            self.capital_costs = float(w_ww_audit_cost) + \
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
        print "kWH\t" + str(int(round(self.electricity))) + "\t\t" + \
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
    ww = WaterWastewaterSystems(manley_data)
    # or
    #~ww = WaterWastewaterSystems(hdd=14593,population=89,system_type="Haul",
                           #~ energy_use_known='no',heat_recovery='no',
                           #~ audit_preformed='no')
    ww.run()
    try:
        ww.print_savings_chart()
    except:
        print "printing error occured"
    return ww # return the object for further testing

