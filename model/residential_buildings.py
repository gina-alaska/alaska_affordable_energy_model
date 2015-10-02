"""
residential_bulidings.py
Ross Spicer
created 2015/09/30

    residential buildings tab.
"""
import numpy as np
from math import isnan

from annual_savings import AnnualSavings
#~ # for live testing ---
#~ import annual_savings
#~ reload(annual_savings)
#~ AnnualSavings = annual_savings.AnnualSavings
#---------------------
from community_data import CommunityData
import aea_assumptions as AEAA
reload(AEAA)
from forecast import Forecast


class ResidentialBuildings(AnnualSavings):
    """
    for forecasting residential building consumption/savings   
    """
    
    def __init__ (self, community_data):
        """
        Class initialiser

        pre:
            community_data is a CommunityData object
        post:
            the model can be run
        """
        self.cd = community_data
        self.forecast = Forecast(self.cd)
        self.refit_cost_rate = AEAA.res_average_refit_cost * \
                            AEAA.construction_mulitpliers[self.cd["region"]]
        self.set_project_life_details(self.cd["res_start_year"],
                                      self.cd["res_lifetime"])
    
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
        self.calc_opportunity_values()
        self.calc_init_HF_use()
        
        self.calc_capital_costs()
    
    def calc_init_HH (self):
        """ Function doc """
        val = self.forecast.get_population(self.start_year)
        
        
        self.init_HH = int(round(self.cd["households"]*\
                        (val / self.cd["population"])))
        
    def calc_opportunity_values (self):
        """ Function doc """
        rd = self.cd["res_model_data"]
        ##  #HH
        self.opportunity_HH = self.init_HH -rd["BEES_number"] -rd["post_number"]
        ## cell L15 = K15*S8*(P8*O8-6000*0.00341)/0.138
        ## gal = #HH*(%)*((MMBtu/sqft)*sqft-(#*#))/# 
        ## gal = #*(MMBtu - (#*#))/#  ???
        self.init_hf_savings = self.opportunity_HH * \
                                   rd["post_avg_EUI_reduction"] * \
                                   (rd["pre_avg_EUI"] * rd["pre_avg_area"] -\
                                    6000*0.00341) / 0.138 # numbers ??
        ## % as decimal 
        self.percent_savigns = rd["opportunity_total_percent_community_savings"]
        
        
    def calc_init_HF_use (self):
        """ Function doc """
        rd = self.cd["res_model_data"]
        ## cell J15 = (M8+U8+K15*O8*P8-I8*6000*0.00341)/0.138
        ##  gal = (MMBtu + MMBtu + (#HH*sqft*MMBTU/sqft) - (#HH*#*#))/#  
        ##  gal = (MMBtu + (MMBtu) - (#HH*#*#))/#
        ##  gal = (MMBTU - (#HH*#*#))/#  ????  
        self.init_HF_use = (rd["BEES_total_consumption"] + \
                                     rd["post_total_consumption"] + \
                    self.opportunity_HH*rd["pre_avg_area"]*rd["pre_avg_EUI"] - \
                        self.init_HH*6000*0.00341) / 0.138
        
    
    def calc_baseline_HF_consumption (self):
        rd = self.cd["res_model_data"]
        self.baseline_HF_consumption = self.init_HF_use + \
        ((self.forecast.get_households(self.start_year,self.end_year)-\
        self.init_HH)*rd['pre_avg_area']*rd['pre_avg_EUI']/.138)

    
    
    def calc_capital_costs (self):
        """ Function doc """
        self.captial_costs = self.opportunity_HH * self.refit_cost_rate
        
    def calc_annual_electric_savings (self):
        """ Function doc """
        pass
        
    def calc_annual_heating_savings (self):
        """ Function doc """
        pass
        
        
def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("community_data_template.csv","Manley Hot Springs")
    t = ResidentialBuildings(manley_data)
    t.run()
    return t 
