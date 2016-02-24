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
            "Education - K - 12", "Education - University",
            "Food Service and Drinking Places", "Health Care - Hospitals", 
            "Health Care - Nursing/Residential Care", "Office","Other",
            "Public Assembly", "Public Safety", "Residential - Multi-Family",
            "Retail - Other", "Warehousing", "Average", "Water & Sewer"
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
from pandas import DataFrame

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants

class CommunityBuildings (AnnualSavings):
    """
    for forecasting community building consumption/savings  
    """
    
    def __init__ (self, community_data, forecast, diag = None):
        """
        Class initialiser

        pre:
            community_data is a CommunityData object. diag (if provided) should 
        be a Diagnostics object
        post:
            the model can be run
        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.cd = community_data.get_section('community')
        self.comp_specs = community_data.get_section('community buildings')
        self.component_name = 'community buildings'
        self.forecast = forecast
        self.refit_cost_rate = self.comp_specs['average refit cost'] * \
      community_data.get_section('construction multipliers')[self.cd["region"]]
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"])
                                      
        
        
    def run (self):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        self.compare_num_buildings()
        self.calc_refit_values()
        self.pre_retrofit_HF_use = np.zeros(self.project_life) + \
                                                    self.baseline_HF_consumption 
                                                    
        
        self.calc_post_refit_use()
        self.post_retrofit_HF_use = np.zeros(self.project_life) + \
                                                    self.refit_HF_consumption   
                                                
        years = range(self.start_year,self.end_year)
        self.forecast.add_heating_fuel_column(\
                        "heating_fuel_non-residential_consumed [gallons/year]",
                        years, self.baseline_HF_consumption)
        self.forecast.add_heating_fuel_column(\
                    "heating_fuel_non-residential_consumed [mmbtu/year]", years,
                     self.baseline_HF_consumption/constants.mmbtu_to_gal_HF)
        
        self.forecast.add_heat_demand_column(\
                    "heat_energy_demand_non-residential [mmbtu/year]",
                 years, self.baseline_HF_consumption/constants.mmbtu_to_gal_HF)
        
        if self.cd["model financial"]:
            self.get_diesel_prices()
            
            self.calc_capital_costs()
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            self.calc_annual_total_savings()
            
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])

    def compare_num_buildings (self):
        """
            This function compares the counted buildings with the estimated 
        buildings
        
        pre:
            'com building data' is a DataFrame, and "number buildings" is 
        an integer 
        post:
            a warning may be added to self.diagnostics 
        """
        self.additional_buildings = self.comp_specs["number buildings"] - \
                            len(self.comp_specs['com building data']) 

        if len(self.comp_specs['com building data']) != \
                self.comp_specs["number buildings"]:
            self.diagnostics.add_note(self.component_name, 
            "# buildings estimated does not match # buildings actual. "+\
            "Estimated: " + str(self.comp_specs["number buildings"]) +\
            ". Actual: " + str(len(self.comp_specs['com building data'])) + ".")
            
            if len(self.comp_specs['com building data']) < \
                self.comp_specs["number buildings"]:
                
                self.add_additional_buildigns()
                
            
    def add_additional_buildigns (self, num_not_heated = 2):
        """
            adds additional buildings to the building dataframe 
        (self.comp_specs['com building data'])
        
        pre:
            self.additional_buildings and num_not_heated are integers
        where self.additional_buildings > num_not_heated
        post:
            self.comp_specs['com building data'] extra buildings,
            a diagnostic message is added
        """
        l = []
        if self.additional_buildings <= num_not_heated:
            self.diagnostics.add_note(self.component_name, 
                            "Not adding additional buildings")
            return
        for i in range(self.additional_buildings - num_not_heated):
            l.append(DataFrame({"Square Feet":np.nan,}, index = ["Average"]))
        self.comp_specs['com building data'] = \
                                self.comp_specs['com building data'].append(l)
        
        self.diagnostics.add_note(self.component_name, "Adding " + str(len(l))+\
                          " additional buildings with average square footage. ") 
        
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
            self.comp_specs["com building estimates"]["Sqft"] is a Pandas series
        indexed by building type of sqft. estimates for the community. 
        self.comp_specs['com building data'] is a Pandas DataFrame containing 
        the actual data on buildings in the community, indexed by building type
        post:
            self.refit_sqft_total is the total sqft. that can retrofitted in
        the community. self.comp_specs['com building data']['Square Feet'] has
        been updated with square footage estimates. 
        """
        sqft_ests = self.comp_specs["com building estimates"]["Sqft"]
        data = self.comp_specs['com building data']
        keys = set(data.T.keys())
        measure = "Square Feet"
        
        for k in keys:
            try:
                # more than one item for each k 
                data.loc[:,measure].loc[k] = \
                            data.loc[:,measure].loc[k].fillna(sqft_ests.ix[k])
            except AttributeError:
                # only one item 
                if np.isnan(data.ix[k][measure]):
                    data.ix[k][measure] = sqft_ests.ix[k]
        
        self.refit_sqft_total = data[measure].sum()
        
    
    def calc_refit_cost (self):
        """ 
        calc refit cost 
          
        pre:
            self.comp_specs['com building data'] is a Pandas DataFrame 
        containing the actual data on buildings in the community, indexed by 
        building type. self.refit_cost_rate is the $$/sqft. for preforming a 
        refit to the building. 
        post:
            self.refit_cost_total is the total cost to refit buildings in the 
        community ($$). 
        self.comp_specs['com building data']['implementation cost'] has been 
        updated with  cost estimates. 
        """
        measure = "implementation cost"
        data = self.comp_specs['com building data']
        keys = data.T.keys()
        d2 = data[["Square Feet", measure]].T.values.tolist()
        d2.insert(0,keys.values.tolist())
        d2 = np.array(d2).T # [key, sqft, $$]
        keys = set(keys) # filter unique keys
        
        for k in keys:
            idx = np.logical_and(d2[:,0] == k, np.isnan(d2[:,2].astype(float)))
            sqft = d2[idx,1].astype(np.float64)
            d2[idx,2] = sqft * self.refit_cost_rate  #sqft * $$/sqft = $$
        
        data[measure] = d2[:,2].astype(np.float64)  
        self.refit_cost_total = data[measure].sum()
        
    def calc_refit_pre_HF (self):
        """ 
        calculate pre refit kWh use
        
        pre:
            self.comp_specs["com building estimates"]["HDD"] is a Pandas
        series of heating degree day values (deg. C/day) with the building 
        types as keys. self.comp_specs["com building estimates"]["Gal/sf"] is
        a Pandas series of Gal/sqft. values building types as keys. 
        self.comp_specs['com building data'] is a Pandas DataFrame containing 
        the actual data on buildings in the community, indexed by building type
        post: 
            self.baseline_HF_consumption is the base line heating fuel 
        consumption for the community (pre-refit). 
        self.comp_specs['com building data']['Fuel Oil'] has been updated with 
        square fuel oil use estimates (gal/yr). 
        """
        HDD_ests = self.comp_specs["com building estimates"]["HDD"]
        gal_sf_ests = self.comp_specs["com building estimates"]["Gal/sf"]
        
        measure = "Fuel Oil"
        data = self.comp_specs['com building data']
        keys = data.T.keys()
        d2 = data[["Square Feet", measure]].T.values.tolist()
        d2.insert(0,keys.values.tolist())
        d2 = np.array(d2).T
        keys = set(keys)

        for k in keys:
            HDD_ratio = self.cd["HDD"]/HDD_ests.ix[k] # unitless
            gal_sf = gal_sf_ests.ix[k] # (gal)/sqft
            
            idx = np.logical_and(d2[:,0] == k, np.isnan(d2[:,2].astype(float)))
            sqft = d2[idx,1].astype(np.float64) # sqft
            d2[idx,2] = sqft * HDD_ratio * gal_sf # gal/yr
        
        data[measure] = d2[:,2].astype(np.float64)                                                 
        self.baseline_HF_consumption = data[measure].sum()
        
    def calc_refit_pre_kWh (self):
        """ 
        calculate pre refit kWh use
        
        pre:
            self.comp_specs["com building estimates"]["kWh/sf"] is a Pandas 
        series of kWh/sqft. values building types as keys. 
        self.comp_specs['com building data'] is a Pandas DataFrame containing 
        the actual data on buildings in the community, indexed by building type
        post: 
            self.baseline_kWh_consumption is the base line electricity
        consumption for the community (pre-refit). 
        self.comp_specs['com building data']['Electric'] has been updated with 
        square fuel oil use estimates (kWh/yr). 
        """
        kwh_sf_ests = self.comp_specs["com building estimates"]["kWh/sf"]
        
        measure = "Electric"
        data = self.comp_specs['com building data']
        keys = data.T.keys()
        d2 = data[["Square Feet", measure]].T.values.tolist()
        d2.insert(0,keys.values.tolist())
        d2 = np.array(d2).T
        keys = set(keys)
        
        for k in keys:
            kwh_sf = kwh_sf_ests.ix[k] # (kWh)/sqft
            
            idx = np.logical_and(d2[:,0] == k, np.isnan(d2[:,2].astype(float)))
            sqft = d2[idx, 1].astype(np.float64) #sqft
            d2[idx, 2] = sqft * kwh_sf # kWh

        data[measure] = d2[:,2].astype(np.float64)  
        self.baseline_kWh_consumption = data[measure].sum()
    
    def calc_refit_savings_HF (self):
        """ 
        calculate refit HF savings
        
        pre:
            tbd
        post: 
            self.refit_savings_HF, self.benchmark_savings_HF,
        self.additional_savings_HF, are floating-point HF values
        """
        #~ self.benchmark_savings_HF = \
            #~ np.sum(self.comp_specs['com building data']["Current Fuel Oil"] -\
                #~ self.comp_specs['com building data']["Post-Retrofit Fuel Oil"])
        #~ self.additional_savings_HF = self.additional_HF * \
                                 #~ self.comp_specs['cohort savings multiplier']
        #~ self.refit_savings_HF_total = self.benchmark_savings_HF +\
                                      #~ self.additional_savings_HF
        #~ self.refit_savings_HF_total = self.baseline_HF_consumption * \
                                    #~ self.comp_specs['cohort savings multiplier']
        try:
            idx = np.isnan(self.comp_specs['com building data']["Fuel Oil Post"])
            self.comp_specs['com building data']["Fuel Oil Post"][idx] = \
                        self.comp_specs['com building data']["Fuel Oil"][idx]*\
                        self.comp_specs['cohort savings multiplier']
        except TypeError:
            self.comp_specs['com building data']["Fuel Oil Post"] = \
                        self.comp_specs['com building data']["Fuel Oil"]*\
                        self.comp_specs['cohort savings multiplier']
        
        
        
        
        self.refit_savings_HF_total = \
                    self.comp_specs['com building data']["Fuel Oil Post"].sum()
        
        
    def calc_refit_savings_kWh (self):
        """ 
        calculate refit kWh savings
        
        pre:
            tbd
        post: 
            self.refit_savings_kWh, self.benchmark_savings_kWh,
        self.additional_savings_kWh, are floating-point kWh values
        """
        #~ self.benchmark_savings_kWh = \
            #~ np.sum(self.comp_specs['com building data']["Current Electric"] -\
                #~ self.comp_specs['com building data']["Post-Retrofit Electric"])
        #~ self.additional_savings_kWh = self.additional_kWh * \
                                 #~ self.comp_specs['cohort savings multiplier']
        #~ self.refit_savings_kWh_total = self.benchmark_savings_kWh +\
                                      #~ self.additional_savings_kWh
        #~ self.refit_savings_kWh_total = self.baseline_kWh_consumption * \
                                    #~ self.comp_specs['cohort savings multiplier']
        try:
            idx = np.isnan(self.comp_specs['com building data']["Electric Post"])
            self.comp_specs['com building data']["Electric Post"][idx] = \
                        self.comp_specs['com building data']["Electric"][idx]*\
                        self.comp_specs['cohort savings multiplier']
        except TypeError:
            self.comp_specs['com building data']["Electric Post"] = \
                        self.comp_specs['com building data']["Electric"]*\
                        self.comp_specs['cohort savings multiplier']
        
        self.refit_savings_kWh_total = \
                    self.comp_specs['com building data']["Electric Post"].sum()
        
    def calc_post_refit_use (self):
        """ 
        calculate post refit HF and kWh use
        
        pre:
            pre refit and savigns values should be calculated
        post: 
            refit_pre_kWh_total is the total number of kWh used after a 
        refit(float)
            same  for self.refit_HF_consumption but with HF
        """
        self.refit_HF_consumption = self.baseline_HF_consumption - \
                                                self.refit_savings_HF_total
        self.refit_kWh_consumption = self.baseline_kWh_consumption - \
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
        elec_price = self.cd["elec non-fuel cost"]+\
                    self.diesel_prices/self.cd['diesel generation efficiency']
        self.baseline_kWh_cost = self.baseline_kWh_consumption * elec_price
                    
        self.refit_kWh_cost = self.refit_kWh_consumption * elec_price
        
        self.annual_electric_savings = np.zeros(self.project_life) + \
                                       self.refit_savings_kWh_total* elec_price
        
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
        fuel_price = (self.diesel_prices + self.cd['heating fuel premium'])
        self.baseline_HF_cost = self.baseline_HF_consumption * fuel_price
                    
        self.refit_HF_cost = self.refit_HF_consumption * fuel_price
        
        self.annual_heating_savings = np.zeros(self.project_life) + \
                                       self.refit_savings_HF_total* (fuel_price)
        
    
component = CommunityBuildings

def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../test_case/input_data/","../test_case/baseline_results/config_used.yaml")
    fc = Forecast(manley_data)
    cb = CommunityBuildings(manley_data, fc)
    cb.run()
    return cb,fc # return the object for further testing
