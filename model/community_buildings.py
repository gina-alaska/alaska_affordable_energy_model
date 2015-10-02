"""
community_buildings.py
ross spicer
created 2015/09/25

    community buildings tab.
    
GLOSSARY:
    HF
        -- Heating Fuel, a measurement in gallons
    Building Library 
        -- a python library of values with the Building Types as string keys. 
    Building Types:
        -- the types of buildings used as keys (strings): 
           "education", "health care","office","other","public_assembly",
           "public_order","warehouse", "unknown"
    CommunityData Object:
        -- defied in community_data.py
    Output Values: 
        -- The values that the model out puts:
            benefit_npv 
            cost_npv
            benefit_cost_ratio 
            net_npv
                -- needs df'n, of define in annual_savings?
            Pre Retrofit HF Use (CommunityBuildings.pre_retrofit_HF_use):
                -- an array of HF fuel values over the project life time 
                containing the assumed HF use before any kind of project 
                is implemented. 
            Pre Retrofit HF Use (CommunityBuildings.post_retrofit_HF_use):
                -- an array of HF fuel values over the project life time 
                containing the assumed HF use after some project 
                is implemented. 


"""
import numpy as np
from math import isnan

from annual_savings import AnnualSavings
#~ # for live testing ---
#~ import annual_savings
#~ reload(annual_savings)
#~ AnnualSavings = annual_savings.AnnualSavings
#---------------------
#~ from community_data import CommunityData
import community_data
reload(community_data)
CommunityData = community_data.CommunityData
import aea_assumptions as AEAA
reload(AEAA)


class CommunityBuildings (AnnualSavings):
    """
    for forecasting community building consumption/savings  
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
        # $/sf
        self.refit_cost_rate = AEAA.com_average_refit_cost * \
                            AEAA.construction_mulitpliers[self.cd["region"]]
        self.set_project_life_details(self.cd["com_start_year"],
                                      self.cd["com_lifetime"])
        
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
        self.calc_refit_values()
        
        self.pre_retrofit_HF_use = np.zeros(self.project_life) + \
                                                    self.refit_pre_HF_total  
        self.calc_post_refit_use()

        self.post_retrofit_HF_use = np.zeros(self.project_life) + \
                                                    self.refit_post_HF_total   
        
        self.get_diesel_prices()
        
        self.calc_capital_costs()
        self.calc_annual_electric_savings()
        self.calc_annual_heating_savings()
        self.calc_annual_total_savings()
        
        self.calc_annual_costs(AEAA.interest_rate)
        self.calc_annual_net_benefit()
        
        self.calc_npv(AEAA.discount_rate, 2014)

    def calc_refit_values (self):
        """
        calculate the forecast input values related to refit buildings
        
        pre:
            None
        
        post:
            TODO: define this better
            refit forecast inputs are calculated.
        """
        self.calc_refit_sqft()
        self.calc_refit_cost()
        self.calc_refit_pre_HF()
        self.calc_refit_pre_kWh()
        self.calc_refit_savings_HF()
        self.calc_refit_savings_kWh()
        
    def calc_refit_sqft (self):
        """ 
        calc refit square feet 
          
        pre:
            AEAA.estimated energy use is a thing? TODO: Define this.
            self.cd should be a community data object 
        
        post:
            refit square feet is calculated by and stored by building type as 
        the key in self.refit_sqft, and totaled in refit_sqft_total
        """
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
        try:
            # multiple building types 
            self.refit_sqft_total += \
                    np.sum(self.cd['com_benchmark_data']['sqft'].values) 
        except AttributeError:
            # single building type
            self.refit_sqft_total += self.cd['com_benchmark_data']['sqft']


    def calc_refit_cost (self):
        """ 
        calc refit cost 
          
        pre:
            self.refit_sqft need to be building library of numbers. 
                (call calc_refit_sqft to do this)
        
        post:
            refit square feet is calculated by and stored by building type as 
        the key in self.refit_cost, and a total in refit_cost_total
        """
        total = 0 
        self.refit_cost = {}
        for key in self.refit_sqft:
            self.refit_cost[key] = self.refit_cost_rate * self.refit_sqft[key]
            #~ total += self.refit_cost[key]
        self.refit_cost_total = self.refit_sqft_total * self.refit_cost_rate
        
    def calc_refit_pre_HF (self):
        """ 
        calculate pre refit kWh use
        
        pre:
            tbd
        post: 
            refit_pre_HF_total is the total number of HF used before a 
        refit(float)
        """
        hf_sqft_yr = AEAA.com_estimated_enegery_use["gal/sf/yr<300"]
        total = 0 
        #gal/yr
        self.refit_pre_HF = {}
        for key in self.refit_sqft:
            #gal/yr
            self.refit_pre_HF[key] = self.refit_sqft[key]*hf_sqft_yr[key]
            total += self.refit_pre_HF[key]
        self.refit_pre_HF_total = total #gal/yr
        try:
            # multiple building types 
            self.refit_pre_HF_total +=\
                np.sum(self.cd['com_benchmark_data']['fuel_oil_1'].values) + \
                np.sum(self.cd['com_benchmark_data']['fuel_oil_2'].values) 
        except AttributeError:
            # single building type
            self.refit_pre_HF_total += \
                                self.cd['com_benchmark_data']['fuel_oil_1'] + \
                                self.cd['com_benchmark_data']['fuel_oil_2']

                
        
    def calc_refit_pre_kWh (self):
        """ 
        calculate pre refit kWh use
        
        pre:
            tbd
        post: 
            refit_pre_kWh_total is the total number of kWh used before a 
        refit(float)
        """
        kWh_sqft_yr = AEAA.com_estimated_enegery_use["kWh/sf/yr<300"]
        total = 0 
        #kWh/yr
        self.refit_pre_kWh = {}
        for key in self.refit_sqft:
            #kWh/yr
            self.refit_pre_kWh[key]=self.refit_sqft[key]*kWh_sqft_yr[key]
            total += self.refit_pre_kWh[key]
        self.refit_pre_kWh_total = total #kWh/yr
        try:
            # multiple building types 
            self.refit_pre_kWh_total += \
                    np.sum(self.cd['com_benchmark_data']['electric'].values) 
        except AttributeError:
            # single building type
            self.refit_pre_kWh_total += \
                                self.cd['com_benchmark_data']['electric']
    
    def calc_refit_savings_HF (self):
        """ 
        calculate refit HF savings
        
        pre:
            tbd
        post: 
            refit_savings_HF_total is the total number of Hf saved by
        refit(float)
        """
        total = 0 
        self.refit_savings_HF = {}
        for key in self.refit_pre_HF:
            self.refit_savings_HF[key] = self.refit_pre_HF[key] * \
                                    AEAA.com_cohort_savings_multiplier
            #~ total += self.refit_savings_HF[key]
        self.refit_savings_HF_total = self.refit_pre_HF_total *\
                                    AEAA.com_cohort_savings_multiplier
        
    def calc_refit_savings_kWh (self):
        """ 
        calculate refit kWh savings
        
        pre:
            tbd
        post: 
            refit_savings_kWh_total is the total number of kWh saved by
        refit(float)
        """
        total = 0 
        self.refit_savings_kWh = {}
        for key in self.refit_pre_kWh:
            self.refit_savings_kWh[key] = self.refit_pre_kWh[key] * \
                                    AEAA.com_cohort_savings_multiplier
            #~ total += self.refit_savings_kWh[key]
        self.refit_savings_kWh_total = self.refit_pre_kWh_total *\
                                    AEAA.com_cohort_savings_multiplier
        
    def calc_post_refit_use (self):
        """ 
        calculate post refit HF and kWh use
        
        pre:
            pre refit and savigns values should be calculated
        post: 
            refit_pre_kWh_total is the total number of kWh used after a 
        refit(float)
            same  for self.refit_post_HF_total but with HF
        """
        self.refit_post_HF_total = self.refit_pre_HF_total - \
                                                self.refit_savings_HF_total
        self.refit_post_kWh_total = self.refit_pre_kWh_total - \
                                                self.refit_savings_kWh_total
    def calc_capital_costs (self):
        """
        pre:
            self.refit_cost_total is a dollar value
        post:
            self.captial_costs is the refit cost
        """
        self.capital_costs = self.refit_cost_total
    
    def calc_annual_electric_savings (self):
        """
        forecast the electric savings
        
        pre:
            self.refit_savings_kWh_total, self.diesel_prices, should be
        available 
            AEAA.diesel_generation_eff: TODO
        post:
            self.annual_electric_savings containt the projected savings
        """
        self.annual_electric_savings = np.zeros(self.project_life) + \
                                       self.refit_savings_kWh_total* \
                            (self.cd["elec_non-fuel_cost"]+\
                            self.diesel_prices/AEAA.diesel_generation_eff)
        
    def calc_annual_heating_savings (self):
        """
        forecast the electric savings
        
        pre:
            self.refit_savings_HF_total, self.diesel_prices, should be
        available 
            AEAA.diesel_generation_eff: TODO
        post:
            self.annual_heating_savings containt the projected savings
        """
        self.annual_heating_savings = np.zeros(self.project_life) + \
                                       self.refit_savings_HF_total* \
                                       (self.diesel_prices + \
                                       AEAA.heating_fuel_premium)
        
    
        
def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("community_data_template.csv","Manley Hot Springs")
    cb = CommunityBuildings(manley_data)
    cb.run()
    print "total sq. ft to retrofit: " + str(round(cb.refit_sqft_total,0))
    print "kWh/yr pre: " + str(round(cb.refit_pre_kWh_total,0))
    print "HF/yr pre: " + str(round(cb.refit_pre_HF_total,0))
    print "kWh/yr savings: " + str(round(cb.refit_savings_kWh_total,2))
    print "HF/yr savings: " + str(round(cb.refit_savings_HF_total,0))
    print "kWh/yr post: " + str(round(cb.refit_post_kWh_total,0))
    print "HF/yr post: " + str(round(cb.refit_post_HF_total,0))
    print "retro fit cost: " + str(round(cb.refit_cost_total,2))
    return cb # return the object for further testing
