"""
residential_bulidings.py
Ross Spicer
created 2015/09/30

    residential buildings tab.
"""
import numpy as np
from math import isnan

from annual_savings import AnnualSavings
from community_data import CommunityData
from forecast import Forecast


class ResidentialBuildings(AnnualSavings):
    """
    for forecasting residential building consumption/savings   
    """
    
    def __init__ (self, community_data, forecast):
        """
        Class initialiser

        pre:
            community_data is a CommunityData object
        post:
            the model can be run
        """
        self.cd = community_data.get_section('community')
        self.comp_specs = community_data.get_section('residential buildings')
        self.component_name = 'residential buildings'
        self.forecast = forecast
        self.refit_cost_rate = self.comp_specs['average refit cost'] * \
      community_data.get_section('construction multipliers')[self.cd["region"]]
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"])
    
    def run (self):
        """ 
        
        run the forecast model
        
        pre:
            AEAA should provide interest and discount rates as floats 0<rate<=1
            self.cd should be a community data object 
        post:
            TODO: define output values. 
            the model is run and the output values are available
        
        """
        self.calc_init_HH()
        self.calc_savings_opportunities()
        self.calc_init_consumption()
        
        self.calc_capital_costs()
        self.get_diesel_prices()
        
        #~ self.calc_baseline_HF_consumption()
        #~ self.forecast.set_res_HF_fuel_forecast(self.baseline_HF_consumption,
                                                #~ self.start_year)
        #~ self.calc_refit_HF_consumption()
        
        #~ self.calc_baseline_HF_cost()
        #~ self.calc_refit_HF_cost()
        
        
        #~ self.calc_annual_electric_savings()
        #~ self.calc_annual_heating_savings()
        #~ self.calc_annual_total_savings()
        
        #~ self.calc_annual_costs(self.cd['interest rate'])
        #~ self.calc_annual_net_benefit()
        
        #~ self.calc_npv(self.cd['discount rate'], 2014)
    
    def calc_init_HH (self):
        """
        estimate the # Housholds for the firet year o the project 
        pre:
            self.forecast should be able to return a population for a given
            year. 
            self.cd should be a properly loaded Community Data object 
        post:
            self.init_HH is an integer # of houses.
        """
        val = self.forecast.get_population(self.start_year)
        
        #TODO:(2) do something with population, also HH
        #  want somthing like pop = self.cd["base pop"]
        # need to up date cd to get it 
        HH =self.comp_specs['data'].ix['total_occupied']
        pop = self.forecast.base_pop
                            
        self.init_HH = int(round(HH*(val / pop)))

    def calc_init_consumption (self):
        """
        """
        rd = self.comp_specs['data'].T
        ## total consumption
        total = rd["post_total_consumption"] + rd["BEES_total_consumption"] + \
                rd["pre_avg_area"] * rd["pre_avg_EUI"] * self.opportunity_HH
        HH = self.init_HH
        
        percent_acconuted = 0
        
        amnt = np.float64(rd["Fuel Oil"])
        percent_acconuted += amnt
        self.init_HF = self.calc_consumption_by_fuel(amnt, total, HH, (1/.138))
        
        amnt = np.float64(rd["Wood"])
        percent_acconuted += amnt
        self.init_wood = self.calc_consumption_by_fuel(amnt, total, HH, 1/20.0)
        
        amnt = np.float64(rd["Utility Gas"])
        percent_acconuted += amnt
        self.init_gas = self.calc_consumption_by_fuel(amnt, total, HH, 0.967)
        
        amnt = np.float64(rd["LP"])
        percent_acconuted += amnt
        self.init_LP = self.calc_consumption_by_fuel(amnt, total, HH, 1/.092)
        
        amnt = np.float64(rd["Electricity"])
        percent_acconuted += amnt
        self.init_kWh = self.calc_consumption_by_fuel(amnt, total, HH, 293.0)
        #~ self.init_coal
        #~ self.init_solar
        #~ self.init_other
        
        print str(round(percent_acconuted * 100)) + \
              " of residential fuel sources accounted for"
        
    def calc_savings_opportunities (self):
        """ 
        """
        rd = self.comp_specs['data'].T
        ##  #HH
        self.opportunity_HH = self.init_HH -rd["BEES_number"] -rd["post_number"]
        ## % as decimal 
        self.percent_savings = rd["opportunity_total_percent_community_savings"]
        
        self.opportunity_HH = np.float64( self.opportunity_HH )
        self.percent_savings = np.float64( self.percent_savings)
        
        
        area = np.float64(rd["pre_avg_area"])
        EUI = np.float64(rd["pre_avg_EUI"])
        avg_EUI_reduction = np.float64(rd["post_avg_EUI_reduction"])
        
        total = area * EUI
        
        
        # the one in each of these function calls is an identity 
        amnt = np.float64(rd["Fuel Oil"])
        self.savings_HF = avg_EUI_reduction * self.opportunity_HH * \
                          self.calc_consumption_by_fuel(amnt, total, 1, 1/.138)
        
        amnt = np.float64(rd["Wood"])
        self.savings_wood = avg_EUI_reduction * self.opportunity_HH * \
                            self.calc_consumption_by_fuel(amnt, total, 1, 1/20.)
        
        amnt = np.float64(rd["Utility Gas"])
        self.savings_gas = avg_EUI_reduction * self.opportunity_HH * \
                           self.calc_consumption_by_fuel(amnt, total, 1, 0.967)
        
        amnt = np.float64(rd["LP"])
        self.savings_LP = avg_EUI_reduction * self.opportunity_HH * \
                          self.calc_consumption_by_fuel(amnt, total, 1, 1/.092)
        
        amnt = np.float64(rd["Electricity"])
        self.savings_kWh = avg_EUI_reduction * self.opportunity_HH * \
                           self.calc_consumption_by_fuel(amnt, total, 1, 293.0)
        #~ self.init_coal
        #~ self.init_solar
        #~ self.init_other
        
    def calc_consumption_by_fuel (self, fuel_amnt, total_consumption, HH, cf):
        """ Function doc """
        kWh_to_mmbtu = 0.003412
        # 500 average energy use, 12 months in a year
        HH_consumption = HH * 500 * 12 * kWh_to_mmbtu
        return np.float64(fuel_amnt * (total_consumption - HH_consumption) * cf)
                            
    def calc_baseline_HF_consumption (self):
        """
        forecast the fuel consumption with no project upgrades
        
        pre:
            self.cd["res_model_data"] should be valid residential data
            self.init_HF_use should be an amount of gallons HF
            self.forecast should be able to forecast the #HH
        post:
            self.baseline_HF_consumption is an array of gallons HF used for
        each year of the forecast. 
        """
        rd = self.comp_specs['data'].T
        self.baseline_HF_consumption = self.init_HF_use + \
        ((self.forecast.get_households(self.start_year,self.end_year)-\
        self.init_HH)*rd['pre_avg_area']*rd['pre_avg_EUI']/.138)

    def calc_refit_HF_consumption (self):
        """
        forecast the fuel consumption with project upgrades
        
        pre:
            self.baseline_HF_consumption is an array of gallons HF used for
        each year of the forecast. 
            self.init_HF_use should be an amount of gallons HF
            self.forecast should be able to forecast the #HH
            self.opportunity_HH is an int
        post:
            self.refit_HF_consumption is an array of gallons HF used for
        each year of the forecast. 
        """
        self.refit_HF_consumption = []
        for idx in range(len(self.baseline_HF_consumption)):
            if idx == 0:
                self.refit_HF_consumption.append(\
                    self.baseline_HF_consumption[idx] - self.init_HF_savings)
                continue
            
            val = self.baseline_HF_consumption[idx] - self.init_HF_savings
            if self.baseline_HF_consumption[idx] < \
               self.baseline_HF_consumption[idx-1]:
                HH_estimate = self.forcast.get_households(self.start_year + idx)
                val -= (HH_estimate - self.init_HH)*\
                        self.init_HF_savings/self.opportunity_HH 
            self.refit_HF_consumption.append(val)
            
    def calc_baseline_HF_cost (self):
        """
        forecast the baseline cost of HF ($/yr for each year)
        
        pre:
            self.diesel_prices is a price(float) for each year. the heating fuel
        premium is price(float). self.baseline_HF_consumption is an array 
        of gallon values over the project life time 
        post:
            self.baseline_HF_cost is an array of costs over the project life
        """
        fuel_price = (self.diesel_prices + self.cd['heating fuel premium'])
        self.baseline_HF_cost = fuel_price * self.baseline_HF_consumption
                
    def calc_refit_HF_cost (self):
        """
        forecast the post-refit cost of HF ($/yr for each year)
        
        pre:
            self.diesel_prices is a price(float) for each year. the heating fuel
        premium is price(float). self.refit_HF_consumption is an array 
        of gallon values over the project life time 
        post:
            self.refit_HF_cost is an array of costs over the project life
        """
        fuel_price = (self.diesel_prices + self.cd['heating fuel premium'])
        self.refit_HF_cost = fuel_price * self.refit_HF_consumption
        
    
    def calc_capital_costs (self):
        """
        caclulate the total cost of the project
        
        Pre:
            self.opportunity_HH, # occupied of houses  
            self.refit_cost_rate, cost / refit
        post:
            self.capital_costs the total cost of the project
        """
        self.capital_costs = self.opportunity_HH * self.refit_cost_rate
        
    def calc_annual_electric_savings (self):
        """
        calculate the savings in electricity cost
        
        post: 
            self.annual_electric_savings array of zeros dollar values
        """
        self.annual_electric_savings = np.zeros(self.project_life)
        
    def calc_annual_heating_savings (self):
        """
        calculate the savings in HF cost
        
        pre: 
            self.baseline_HF_cost, self.refit_HF_cost should be dollar value 
        arrays over the project life time
        post: 
            self.annual_heating_savings array savings in HF cost
        """
        self.annual_heating_savings = self.baseline_HF_cost - \
                                      self.refit_HF_cost
        

component = ResidentialBuildings

def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../data","../test_case/manley_data.yaml")
    
    fc = Forecast(manley_data)
    t = ResidentialBuildings(manley_data,fc)
    t.run()
    return t,fc
