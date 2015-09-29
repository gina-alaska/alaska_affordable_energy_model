"""
community_buildings.py
ross spicer
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


class CommunityBuildings (AnnualSavings):
    """ Class doc """
    
    def __init__ (self, community_data):
        """ Class initialiser """
        self.cd = community_data
        # $/sf
        self.refit_cost_rate = AEAA.com_average_refit_cost * \
                            AEAA.construction_mulitpliers[self.cd["region"]]
        self.set_project_life_details(self.cd["com_start_year"],
                                      self.cd["com_lifetime"])
        
    def run (self):
        """ Function doc """
        self.calc_refit_values()
        self.calc_post_refit_savings()
        self.get_diesel_prices()
        
        self.calc_capital_costs()
        self.calc_annual_electric_savings()
        self.calc_annual_heating_savings()
        self.calc_annual_total_savings()
        
        self.calc_annual_costs(AEAA.interest_rate)
        self.calc_annual_net_benefit()
        
        self.calc_npv(AEAA.discount_rate, 2014)

    #~ def calc_refit_values_known_buildings (self):
    def calc_refit_values (self):
        """ Function doc """
        self.calc_refit_sqft()
        self.calc_refit_cost()
        self.calc_refit_pre_HF()
        self.calc_refit_pre_kWh()
        self.calc_refit_savings_HF()
        self.calc_refit_savings_kWh()
        
    def calc_refit_sqft (self):
        """ Function doc """
        num_buildings = self.cd['com_buildings']
        sqft_act = self.cd["com_sqft_to_retofit"]
        sqft_est = AEAA.com_estimated_enegery_use["est.sf<300"]
        
        total = 0 
        self.refit_sqft = {}
        for key in sqft_act.keys():
            value = sqft_act[key]
            if isnan(value):
                value = sqft_est[key] * num_buildings[key]
            self.refit_sqft[key] = value
            total += value
        self.refit_sqft_total = total

    def calc_refit_cost (self):
        """ Function doc """
        total = 0 
        self.refit_cost = {}
        for key in self.refit_sqft:
            self.refit_cost[key] = self.refit_cost_rate * self.refit_sqft[key]
            total += self.refit_cost[key]
        self.refit_cost_total = total
        
    def calc_refit_pre_HF (self):
        """ Function doc """
        hf_sqft_yr = AEAA.com_estimated_enegery_use["gal/sf/yr<300"]
        total = 0 
        #gal/yr
        self.refit_pre_HF = {}
        for key in self.refit_sqft:
            #gal/yr
            self.refit_pre_HF[key] = self.refit_sqft[key]*hf_sqft_yr[key]
            total += self.refit_pre_HF[key]
        self.refit_pre_HF_total = total #gal/yr
        
    def calc_refit_pre_kWh (self):
        """ Function doc """
        kWh_sqft_yr = AEAA.com_estimated_enegery_use["kWh/sf/yr<300"]
        total = 0 
        #kWh/yr
        self.refit_pre_kWh = {}
        for key in self.refit_sqft:
            #kWh/yr
            self.refit_pre_kWh[key]=self.refit_sqft[key]*kWh_sqft_yr[key]
            total += self.refit_pre_kWh[key]
        self.refit_pre_kWh_total = total #kWh/yr
    
    def calc_refit_savings_HF (self):
        """ Function doc """
        total = 0 
        self.refit_savings_HF = {}
        for key in self.refit_pre_HF:
            self.refit_savings_HF[key] = self.refit_pre_HF[key] * \
                                    AEAA.com_cohort_savings_multiplier
            total += self.refit_savings_HF[key]
        self.refit_savings_HF_total = total
        
    def calc_refit_savings_kWh (self):
        """ Function doc """
        total = 0 
        self.refit_savings_kWh = {}
        for key in self.refit_pre_kWh:
            self.refit_savings_kWh[key] = self.refit_pre_kWh[key] * \
                                    AEAA.com_cohort_savings_multiplier
            total += self.refit_savings_kWh[key]
        self.refit_savings_kWh_total = total
        
    def calc_post_refit_savings (self):
        """ """
        self.refit_post_HF_total = self.refit_pre_HF_total - \
                                                self.refit_savings_HF_total
        self.refit_post_kWh_total = self.refit_pre_kWh_total - \
                                                self.refit_savings_kWh_total
    def calc_capital_costs (self):
        self.capital_costs = self.refit_cost_total
    
    def calc_annual_electric_savings (self):
        self.annual_electric_savings = np.zeros(self.project_life) + \
                                       self.refit_savings_kWh_total* \
                            (self.cd["elec_non-fuel_cost"]+\
                            self.diesel_prices/AEAA.diesel_generation_eff)
        
    def calc_annual_heating_savings (self):
        """ Function doc """
        self.annual_heating_savings = np.zeros(self.project_life) + \
                                       self.refit_savings_HF_total* \
                                       (self.diesel_prices + \
                                       AEAA.heating_fuel_premium)
        
    
        
def test ():
    """
    tests the class using the manley data.
    """
    cb = CommunityBuildings(manley_data)
    cb.run()
    print "total sq. ft to retrofit: " + str(round(cb.refit_sqft_total,0))
    print "kWh/yr pre: " + str(round(cb.refit_pre_kWh_total,0))
    print "HF/yr pre: " + str(round(cb.refit_pre_HF_total,0))
    print "kWh/yr savings: " + str(round(cb.refit_savings_kWh_total,0))
    print "HF/yr savings: " + str(round(cb.refit_savings_HF_total,0))
    print "kWh/yr post: " + str(round(cb.refit_post_kWh_total,0))
    print "HF/yr post: " + str(round(cb.refit_post_HF_total,0))
    print "retro fit cost: " + str(round(cb.refit_cost_total,2))
    return cb # return the object for further testing
