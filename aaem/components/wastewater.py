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
#~ import aea_assumptions as AEAA
import forecast
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
        self.cd = community_data.get_section('community')
        self.comp_specs = community_data.get_section('water wastewater')
        self.component_name = 'water wastewater'
        self.cost_per_person  = self.comp_specs['average refit cost'] * \
      community_data.get_section('construction multipliers')[self.cd["region"]] 
       
        self.forecast = forecast
        
        self.hdd = self.cd["HDD"]
        #~ self.pop = self.cd["population"]
        self.pop = self.forecast.electricty_actuals['population'][7]
        self.system_type = self.comp_specs["system type"] 
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
        cost = self.savings_electricity * self.cd["res non-PCE elec cost"]
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
        fuel_cost = self.diesel_prices + self.cd['heating fuel premium']# $/gal
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
        fuel_cost = self.diesel_prices + self.cd['heating fuel premium'] #$/gal
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
        print self.comp_specs["start year"]
        print self.comp_specs["lifetime"]
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"])
        
        self.calc_electricity_consumption()
        hr_used = self.comp_specs['heat recovery used']
        hrm = self.comp_specs['heat recovery multiplier'][hr_used]
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
        
        self.calc_annual_costs(self.cd['interest rate'])
        self.calc_annual_net_benefit()
        
        self.calc_npv(self.cd['discount rate'], 2014)
    
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
        if self.comp_specs["energy use known"]:
            self.electricity = self.comp_specs["collected data"]['kWh/yr']
        else: #if not self.cd["w&ww_energy_use_known"]:
            self.electricity = \
(self.hdd * self.comp_specs['ww assumptions']['HDD kWh'][self.system_type] + \
     self.pop * self.comp_specs['ww assumptions']['pop kWh'][self.system_type])
            # update for 9/28 spread sheet 
            # forcast needs an update to get a range of years 
            self.forecast.forecast_population()
            self.electricity += (self.forecast.population[1:16] - \
                                 self.pop)*\
                 self.comp_specs['ww assumptions']['HDD kWh'][self.system_type]
                            
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
        if self.comp_specs["energy use known"]:
            self.electricity = self.comp_specs["collected data"]['HF used']
        else: #if not self.cd["energy_use_known"]:
            self.heating_fuel = \
   (self.hdd * self.comp_specs['ww assumptions']['HDD HF'][self.system_type] + \
   self.pop * self.comp_specs['ww assumptions']['pop HF'][self.system_type]) * \
                                 hr_coeff 
            # update for 9/28 spread sheet 
            # forcast needs an update to get a range of years 
            pop_fc = self.forecast.get_population(self.start_year,self.end_year)
            self.heating_fuel += (pop_fc - self.pop) * \
                 self.comp_specs['ww assumptions']['pop HF'][self.system_type]

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
        if  self.comp_specs["audit preformed"]:
            self.savings_electricity = \
                    self.cdself.comp_specs["collected data"]['kWh/yr w/ retro']
        else: # if not self.comp_sepcs["audit preformed"]:
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
        if  self.comp_specs["audit preformed"]:
            self.savings_electricity = \
                    self.cdself.comp_specs["collected data"]['HF w/Retro']
        else: # if not self.comp_sepcs["audit preformed"]:
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
        self.capital_costs = self.comp_specs["audit cost"]
        if not self.comp_specs["audit preformed"]:
            self.capital_costs = float(self.comp_specs["audit cost"]) + \
                                        self.pop *  self.cost_per_person
    
        
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
       
component = WaterWastewaterSystems
    
def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../data/community_data_template.csv",
                                "Manley Hot Springs")
    manley_data.load_input("test_case/manley_data.yaml",
                          "test_case/data_defaults.yaml")
    manley_data.get_csv_data()
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

