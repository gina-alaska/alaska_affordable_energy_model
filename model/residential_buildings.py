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
#~ from community_data import manley_data
import community_data
reload(community_data)
manley_data = community_data.manley_data
import aea_assumptions as AEAA
reload(AEAA)
from forecast import Forecast


class ResidentialBuildings(AnnualSavings):
    """ Class doc """
    
    def __init__ (self, community_data):
        """ Class initialiser """
        self.cd = community_data
        self.forecast = Forecast(self.cd)
        self.set_project_life_details(self.cd["com_start_year"],
                                      self.cd["com_lifetime"])
    
    def run (self):
        """ Function doc """
        self.calc_init_hh()
        self.calc_opportunity_values()
        self.calc_init_HF_use()
    
    def calc_init_hh (self):
        """ Function doc """
        val = self.forecast.get_population(self.start_year,self.start_year+1)[0]
        self.init_hh = int(round(self.cd["households"]*\
                        (val / self.cd["population"])))
        
    def calc_opportunity_values (self):
        """ Function doc """
        rd = self.cd["res_model_data"]
        self.opportunity_hh = self.init_hh -rd["BEES_number"] -rd["post_number"]
        self.opportunity_savings = self.opportunity_hh * \
                                   rd["post_avg_EUI_reduction"] * \
                                   (rd["pre_avg_EUI"] * rd["pre_avg_area"] -\
                                    6000*0.00341) / 0.138 # numbers ??
        self.percent_savigns = rd["opportunity_total_percent_community_savings"]
        
        
    def calc_init_HF_use (self):
        """ Function doc """
        rd = self.cd["res_model_data"]
        self.init_HF_use = (rd["BEES_total_consumption"] + \
                                     rd["post_total_consumption"] + \
                    self.opportunity_hh*rd["pre_avg_area"]*rd["pre_avg_EUI"] - \
                        self.init_hh*6000*0.00341) / 0.138
        
    def calc_capital_costs (self):
        """ Function doc """
        pass
        
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
    t = ResidentialBuildings(manley_data)
    t.run()
    return t 
