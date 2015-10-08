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
from community_data import CommunityData
import aea_assumptions as AEAA
from forecast import Forecast


class CommunityBuildings (AnnualSavings):
    """
    for forecasting community building consumption/savings  
    """
    
    def __init__ (self, community_data, forecast):
        """
        Class initialiser

        pre:
            community_data is a CommunityData object
        post:
            the model can be run
        """
        self.cd = community_data
        self.forecast = forecast
        self.refit_cost_rate = AEAA.com_average_refit_cost * \
                            AEAA.construction_mulitpliers[self.cd["region"]]
        self.set_project_life_details(self.cd["com_start_year"],
                                      self.cd["com_lifetime"])
                                      
        self.additional_buildings = self.cd["com_num_buildings"] - \
np.sum(self.cd['com_benchmark_data'][['Number Of Building Type']].values) - 2
        
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
        
        self.forecast.set_com_HF_fuel_forecast(self.pre_retrofit_HF_use, 
                                                self.start_year)
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
            self.cd should be a community data object 
        
        post:
          self.refit_sqft_total, self.benchmark_sqft, self.additional_sqft are
        floating-point square feet values 
        """
        self.benchmark_sqft = \
            np.sum(self.cd['com_benchmark_data'][['Total Square Feet']].values) 
        pop = self.cd['population']  
        if pop < 300:
            key = "Average sf<300"
        elif pop < 1200:
            key = "Average sf>300,<1200"
        else: 
            key = "Average sf>1200"
        
        
        self.additional_sqft = self.additional_buildings * \
                               AEAA.com_building_estimates['Other'][key]
        self.refit_sqft_total = self.additional_sqft + self.benchmark_sqft
        

    def calc_refit_cost (self):
        """ 
        calc refit cost 
          
        pre:
            self.additional_sqft should be a float in square feet
        
        post:
            self.refit_cost_total, self.benchmark_cost, self.additional_cost are
        floating-point dollar values 
        """
        self.benchmark_cost = \
            np.sum(self.cd['com_benchmark_data']\
                        [['Cohort Implementation Cost']].values) 
        self.additional_cost = self.additional_sqft * self.refit_cost_rate
        self.refit_cost_total = self.benchmark_cost + self.additional_cost
        
    def calc_refit_pre_HF (self):
        """ 
        calculate pre refit kWh use
        
        pre:
            tbd
        post: 
            self.refit_pre_hf_total, self.benchmark_hf, self.additional_hf are
        floating-point HF values
        """
        pop = self.cd['population']  
        if pop < 300:
            key = "Av Gal/sf<300"
        elif pop < 1200:
            key = "Av Gal/sf>300,<1200"
        else: 
            key = "Av Gal/sf>1200"
        
        hf_sqft_yr = AEAA.com_building_estimates['Other'][key]

        
        self.benchmark_HF = \
            np.sum(self.cd['com_benchmark_data'][['Current Fuel Oil']].values) 

        self.additional_HF = self.additional_sqft * hf_sqft_yr
        
            # multiple building types 
        self.refit_pre_HF_total = self.benchmark_HF + self.additional_HF

                
        
    def calc_refit_pre_kWh (self):
        """ 
        calculate pre refit kWh use
        
        pre:
            tbd
        post: 
            self.refit_pre_kWh_total, self.benchmark_kWh, 
        self.additional_kWh are floating-point kWh values
        """
        pop = self.cd['population']  
        if pop < 300:
            key = "Avg kWh/sf<300"
        elif pop < 1200:
            key = "Avg kWh/sf>300,<1200"
        else: 
            key = "Avg kWh/sf>1200"
        
        kWh_sqft_yr = AEAA.com_building_estimates['Other'][key]

        
        self.benchmark_kWh = \
            np.sum(self.cd['com_benchmark_data'][['Current Electric']].values) 
        
        self.additional_kWh = self.additional_sqft * kWh_sqft_yr
        
            # multiple building types 
        self.refit_pre_kWh_total = self.benchmark_kWh + self.additional_kWh
    
    def calc_refit_savings_HF (self):
        """ 
        calculate refit HF savings
        
        pre:
            tbd
        post: 
            self.refit_savings_HF, self.benchmark_savings_HF,
        self.additional_savings_HF, are floating-point HF values
        """
        self.benchmark_savings_HF = \
                np.sum(self.cd['com_benchmark_data']["Current Fuel Oil"] -\
                    self.cd['com_benchmark_data']["Post-Retrofit Fuel Oil"])
        self.additional_savings_HF = self.additional_HF * \
                                 AEAA.com_cohort_savings_multiplier
        self.refit_savings_HF_total = self.benchmark_savings_HF +\
                                      self.additional_savings_HF
        
    def calc_refit_savings_kWh (self):
        """ 
        calculate refit kWh savings
        
        pre:
            tbd
        post: 
            self.refit_savings_kWh, self.benchmark_savings_kWh,
        self.additional_savings_kWh, are floating-point kWh values
        """
        self.benchmark_savings_kWh = \
                np.sum(self.cd['com_benchmark_data']["Current Electric"] -\
                    self.cd['com_benchmark_data']["Post-Retrofit Electric"])
        self.additional_savings_kWh = self.additional_kWh * \
                                 AEAA.com_cohort_savings_multiplier
        self.refit_savings_kWh_total = self.benchmark_savings_kWh +\
                                      self.additional_savings_kWh
        
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
    manley_data = CommunityData("community_data_template.csv",
                                "Manley Hot Springs")
    fc = Forecast(manley_data)
    cb = CommunityBuildings(manley_data, fc)
    cb.run()
    print "total sq. ft to retrofit: " + str(round(cb.refit_sqft_total,0))
    print "kWh/yr pre: " + str(round(cb.refit_pre_kWh_total,0))
    print "HF/yr pre: " + str(round(cb.refit_pre_HF_total,0))
    print "kWh/yr savings: " + str(round(cb.refit_savings_kWh_total,2))
    print "HF/yr savings: " + str(round(cb.refit_savings_HF_total,0))
    print "kWh/yr post: " + str(round(cb.refit_post_kWh_total,0))
    print "HF/yr post: " + str(round(cb.refit_post_HF_total,0))
    print "retro fit cost: " + str(round(cb.refit_cost_total,2))
    return cb,fc # return the object for further testing
