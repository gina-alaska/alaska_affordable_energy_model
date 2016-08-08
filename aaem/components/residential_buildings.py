"""
residential_bulidings.py
Ross Spicer
created 2015/09/30

    residential buildings tab.
"""
import numpy as np
from math import isnan
from pandas import DataFrame, read_csv

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants
import os


yaml = {'enabled': False,
        'min kWh per household': 6000,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'average refit cost': 11000,
        'data': 'IMPORT'}
        
yaml_defaults = {'enabled': True,
        'lifetime': 15,
        'start year': 2017,
        }
        
yaml_order = ['enabled', 'min kWh per household', 'lifetime', 'start year',
              'average refit cost', 'data']

yaml_comments = {'enabled': '',
        'min kWh per household': 
                'minimum average consumed kWh/year per house<int>',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>',
        'average refit cost': 'cost/refit <float>',
        'data': 'IMPORT'}

## list of prerequisites for module
prereq_comps = []
        
def process_data_import(data_dir):
    """
    """
    data_file = os.path.join(data_dir, "residential_data.csv")
    
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    
    data.ix["Notes"]['value'] = np.nan
    if data.ix["average kWh per house"]['value'] == "CALC_FOR_INTERTIE":
        data.ix["average kWh per house"]['value'] = np.nan
    data['value'] = data['value'].astype(float) 
    
    
    return data
        
yaml_import_lib = {'data': process_data_import}

class ResidentialBuildings(AnnualSavings):
    """
    for forecasting residential building consumption/savings   
    """
    
    def __init__ (self, community_data, forecast, 
                        diag = None, prerequisites = {}):
        """
        Class initialiser

        pre:
            community_data is a CommunityData object
        post:
            the model can be run
        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.cd = community_data.get_section('community')
        self.copied_elec = community_data.copies.\
                                    ix["yearly electric summary"].values[0]

        if self.cd["model electricity"]:
            self.elec_prices = community_data.electricity_price
        self.comp_specs = community_data.get_section('residential buildings')
        self.component_name = 'residential buildings'
        self.forecast = forecast
        self.refit_cost_rate = self.comp_specs['average refit cost'] * \
      community_data.get_section('construction multipliers')[self.cd["region"]]
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
                        
                     
        yr = self.comp_specs['data'].ix['year']
        self.base_pop = self.forecast.population.ix[yr].values[0][0]
        
        peps_per_house = float(self.base_pop) / \
            self.comp_specs['data'].ix['total_occupied']
        households = np.round(self.forecast.population / np.float64(peps_per_house))
        households.columns = ["HH"] 
        self.households = households.ix[self.start_year:self.end_year-1].T.values[0]
        
        
        val = self.forecast.get_population(self.start_year)
        HH =self.comp_specs['data'].ix['total_occupied']
        self.init_HH = int(round(HH*(val / self.base_pop)))
        
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
        self.run = True
        self.reason = "OK"
        
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1] != 'residential':
            self.run = False
            self.reason = "Not a residential project"
            return 
            
        # needed for electric or HF component and has a default value
        self.calc_avg_consumption()
        if self.cd["model electricity"]:
            
            self.calc_baseline_kWh_consumption()
            self.calc_refit_kWh_consumption()
        
        if self.cd["model heating fuel"]:
            #~ self.calc_init_HH()
            self.calc_savings_opportunities()
            self.calc_init_consumption()
            self.calc_baseline_fuel_consumption()
            self.calc_refit_fuel_consumption()
            self.set_forecast_columns()
        
        if self.cd["model financial"]:
            self.calc_capital_costs()
            
            self.get_diesel_prices()
            self.calc_baseline_fuel_cost() 
            self.calc_refit_fuel_cost()
            self.calc_baseline_kWh_cost() 
            self.calc_refit_kWh_cost()
            
            
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            self.calc_annual_total_savings()
            
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            
            self.calc_npv(self.cd['discount rate'], self.cd['current year'])
            self.calc_levelized_costs(0)
            
    def get_fuel_total_saved (self):
        """
        returns the total fuel saved in gallons
        """
        base_heat = \
            sum(self.baseline_fuel_Hoil_consumption[:self.actual_project_life])
        post_heat = \
            sum(self.refit_fuel_Hoil_consumption[:self.actual_project_life])
       
        ## same, so can ignore
        #~ base_elec =self.baseline_kWh_consumption 
        #~ post_elec =self.baseline_kWh_consumption 
        
        return base_heat - post_heat
                                
    def get_total_enery_produced (self):
        """
        returns the total energy produced saved
        """
        # no electric
        return sum(self.baseline_HF_consumption[:self.actual_project_life]) - \
               sum(self.refit_HF_consumption[:self.actual_project_life])
    
    def calc_avg_consumption (self):
        """ 
        get the average monthly consumption of electricity for a house
        
        pre:
        
        post: 
        """
        #   500 average energy use, 12 months in a year. That's whrer the 6000.0
        # comes from.
        con_threshold = self.comp_specs['min kWh per household']
        yr = int(self.comp_specs['data'].ix['year'])
        #~ houses = int(self.comp_specs['data'].ix['total_occupied'])
        #~ r_con = self.forecast.base_res_consumption
        avg_con = float(self.comp_specs['data'].ix['average kWh per house'])
        #~ self.avg_monthly_consumption = ave_con/12
        if (avg_con < con_threshold) or self.copied_elec or np.isnan(avg_con):
            avg_con = con_threshold
            self.diagnostics.add_note(self.component_name, 
                    ("Average residential Electric consumption"
                    " corrected to "+ str(con_threshold)+" kWh per year"))
        self.avg_kWh_consumption_per_HH = avg_con
        self.diagnostics.add_note(self.component_name,
                "Average consumption was " + str(self.avg_kWh_consumption_per_HH) +\
                " in " + str(yr))
        
    
    def calc_init_HH (self):
        """
        estimate the # Households for the first year of the project 
        pre:
            self.forecast should be able to return a population for a given
            year. 
            self.cd should be a properly loaded Community Data object 
        post:
            self.init_HH is an integer # of houses.
        """
        val = self.forecast.get_population(self.start_year)
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
        self.init_HF = self.calc_consumption_by_fuel(amnt, total, HH, 
                                                     constants.mmbtu_to_gal_HF)
        amnt = np.float64(rd["Wood"])
        percent_acconuted += amnt
        self.init_wood = self.calc_consumption_by_fuel(amnt, total, HH, 
                                                    constants.mmbtu_to_cords)
        
        amnt = np.float64(rd["Utility Gas"])
        percent_acconuted += amnt
        self.init_gas = self.calc_consumption_by_fuel(amnt, total, HH, 
                                                    constants.mmbtu_to_Mcf)
        
        amnt = np.float64(rd["LP"])
        percent_acconuted += amnt
        self.init_LP = self.calc_consumption_by_fuel(amnt, total, HH, 
                                                    constants.mmbtu_to_gal_LP)
        
        amnt = np.float64(rd["Electricity"])
        percent_acconuted += amnt
        self.init_kWh = self.calc_consumption_by_fuel(amnt, total, HH,
                                                      constants.mmbtu_to_kWh)
        #~ self.init_coal
        #~ self.init_solar
        #~ self.init_other
        
        msg = str(round(percent_acconuted * 100)) + \
              " of residential fuel sources accounted for"
        self.diagnostics.add_note(self.component_name, msg)
        
    def calc_savings_opportunities (self):
        """ 
        """
        rd = self.comp_specs['data'].T
        ##  #HH
        self.opportunity_HH = self.init_HH -rd["BEES_number"] -rd["post_number"]
        self.opportunity_HH = np.float64( self.opportunity_HH )
        #~ print self.opportunity_HH
        if self.opportunity_HH < 0:
            self.opportunity_HH = 0
            self.diagnostics.add_note(self.component_name, 
                "calculate Houses to retrofit was negative, setting to 0" )
        
        ## % as decimal 
        #~ self.percent_savings = rd["opportunity_total_percent_community_savings"]
        
        
        #~ self.percent_savings = np.float64( self.percent_savings)
        
        
        area = np.float64(rd["pre_avg_area"])
        EUI = np.float64(rd["pre_avg_EUI"])
        avg_EUI_reduction = np.float64(rd["post_avg_EUI_reduction"])
        
        total = area * EUI
        
        
        # the one in each of these function calls is an identity 
        amnt = np.float64(rd["Fuel Oil"])
        self.savings_HF = avg_EUI_reduction * self.opportunity_HH * \
                          self.calc_consumption_by_fuel(amnt, total, 1,
                          constants.mmbtu_to_gal_HF)
        
        amnt = np.float64(rd["Wood"])
        self.savings_wood = avg_EUI_reduction * self.opportunity_HH * \
                            self.calc_consumption_by_fuel(amnt, total, 1, 
                            constants.mmbtu_to_cords)
        
        amnt = np.float64(rd["Utility Gas"])
        self.savings_gas = avg_EUI_reduction * self.opportunity_HH * \
                           self.calc_consumption_by_fuel(amnt, total, 1, 
                           constants.mmbtu_to_Mcf)
        
        amnt = np.float64(rd["LP"])
        self.savings_LP = avg_EUI_reduction * self.opportunity_HH * \
                          self.calc_consumption_by_fuel(amnt, total, 1,
                          constants.mmbtu_to_gal_LP)
        
        amnt = np.float64(rd["Electricity"])
        self.savings_kWh = avg_EUI_reduction * self.opportunity_HH * \
                           self.calc_consumption_by_fuel(amnt, total, 1, 
                           constants.mmbtu_to_kWh)
        #~ self.savings_coal
        #~ self.savings_solar
        #~ self.savings_other
                           
        self.savings_mmbtu = self.savings_HF * (1/constants.mmbtu_to_gal_HF) +\
                             self.savings_wood * (1/constants.mmbtu_to_cords) +\
                             self.savings_gas * (1/constants.mmbtu_to_Mcf) +\
                             self.savings_kWh * (1/constants.mmbtu_to_kWh) +\
                             self.savings_LP* (1/constants.mmbtu_to_gal_LP)
        
        
    def calc_consumption_by_fuel (self, fuel_amnt, total_consumption, HH, cf):
        """ Function doc """
  
        HH_consumption = HH * self.avg_kWh_consumption_per_HH * \
                                                    constants.kWh_to_mmbtu
        return np.float64(fuel_amnt * (total_consumption - HH_consumption) * cf)
                            
    def calc_baseline_fuel_consumption (self):
        """
        """
        rd = self.comp_specs['data'].T
        self.fuel_oil_percent = rd["Fuel Oil"]
        HH = self.households
        #~ print HH
        area = np.float64(rd["pre_avg_area"])
        EUI = np.float64(rd["pre_avg_EUI"])
        
        scaler = (HH - self.init_HH) * area * EUI
        
        self.baseline_fuel_Hoil_consumption = \
                                    self.init_HF+np.float64(rd["Fuel Oil"])*\
                                    scaler * constants.mmbtu_to_gal_HF
        self.baseline_fuel_wood_consumption = \
                                       self.init_wood+np.float64(rd["Wood"])*\
                                       scaler * constants.mmbtu_to_cords
        self.baseline_fuel_gas_consumption = self.init_gas + \
                                        np.float64(rd["Utility Gas"]) * \
                                        scaler * constants.mmbtu_to_Mcf
        self.baseline_fuel_LP_consumption = self.init_LP+np.float64(rd["LP"])*\
                                       scaler * constants.mmbtu_to_gal_LP
        self.baseline_fuel_kWh_consumption = self.init_kWh+\
                                        np.float64(rd["Electricity"])*\
                                        scaler * constants.mmbtu_to_kWh
        #~ self.baseline_fuel_coal_consumption
        #~ self.baseline_fuel_solar_consumption
        #~ self.baseline_fuel_other_consumption
        if self.cd['natural gas price'] == 0:
            self.baseline_fuel_gas_consumption = 0
        
        self.baseline_HF_consumption = \
            self.baseline_fuel_Hoil_consumption * \
                (1/constants.mmbtu_to_gal_HF) +\
            self.baseline_fuel_wood_consumption * \
                (1/constants.mmbtu_to_cords) +\
            self.baseline_fuel_gas_consumption * (1/constants.mmbtu_to_Mcf) +\
            self.baseline_fuel_kWh_consumption * (1/constants.mmbtu_to_kWh) +\
            self.baseline_fuel_LP_consumption * (1/constants.mmbtu_to_gal_LP)
    
    def calc_baseline_kWh_consumption (self):
        """
        calculate the baseline kWh consumption for a community 
        """
        HH = self.households
        self.baseline_kWh_consumption = self.avg_kWh_consumption_per_HH * HH 
        
    def calc_baseline_fuel_cost (self):
        """
        caclulat base line heating fuel costs
        """
        HF_price = (self.diesel_prices + self.cd['heating fuel premium'])
        self.hoil_price = HF_price
        wood_price = self.cd['cordwood price'] 
        elec_price = self.elec_prices[self.start_year-self.start_year:
                                         self.end_year-self.start_year]
        LP_price = self.cd['propane price'] 
        gas_price = self.cd['natural gas price'] 
        
        
        self.baseline_HF_cost = \
            self.baseline_fuel_Hoil_consumption * HF_price + \
            self.baseline_fuel_wood_consumption * wood_price + \
            self.baseline_fuel_gas_consumption * gas_price + \
            self.baseline_fuel_LP_consumption * LP_price + \
            self.baseline_fuel_kWh_consumption * gas_price
        # coal,solar, other
        
    def calc_baseline_kWh_cost (self):
        """
        calculate base line electricity costs
        """
        kWh_cost = self.cd["electric non-fuel prices"].\
                                            ix[self.start_year:self.end_year-1]
        kWh_cost = kWh_cost.T.values[0]
        # kWh/yr*$/kWh
        self.baseline_kWh_cost = self.baseline_kWh_consumption * kWh_cost

    def calc_refit_fuel_consumption (self):
        """
        """
        self.refit_fuel_Hoil_consumption = \
            self.baseline_fuel_Hoil_consumption - self.savings_HF 
        self.refit_fuel_wood_consumption = \
            self.baseline_fuel_wood_consumption - self.savings_wood 
        self.refit_fuel_LP_consumption = \
            self.baseline_fuel_LP_consumption - self.savings_LP 
        self.refit_fuel_gas_consumption = \
            self.baseline_fuel_gas_consumption - self.savings_gas 
        self.refit_fuel_kWh_consumption = \
            self.baseline_fuel_kWh_consumption - self.savings_kWh 
                                     
        self.refit_HF_consumption = \
                    self.baseline_HF_consumption - self.savings_mmbtu
                    
        if self.cd['natural gas price'] == 0:
            self.refit_fuel_gas_consumption = 0
        # coal,solar, other
        
    def calc_refit_kWh_consumption (self):
        """
        calculate the baseline kWh consumption for a community 
        """
        self.refit_kWh_consumption = self.baseline_kWh_consumption 
        
    def calc_refit_fuel_cost (self):
        """
        """
        HF_price = (self.diesel_prices + self.cd['heating fuel premium'])
        wood_price = self.cd['cordwood price'] 
        elec_price = self.elec_prices[self.start_year-self.start_year:
                                         self.end_year-self.start_year]
        LP_price = self.cd['propane price'] 
        gas_price = self.cd['natural gas price'] 
        
        
        self.refit_HF_cost = self.refit_fuel_Hoil_consumption * HF_price + \
                             self.refit_fuel_wood_consumption * wood_price + \
                             self.refit_fuel_gas_consumption * gas_price + \
                             self.refit_fuel_LP_consumption * LP_price + \
                             self.refit_fuel_kWh_consumption * gas_price
        
    def calc_refit_kWh_cost (self):
        """
        calculate post retrofit electricity costs
        """
        kWh_cost = self.cd["electric non-fuel prices"].\
                                            ix[self.start_year:self.end_year-1]
        kWh_cost = kWh_cost.T.values[0]
        # kWh/yr*$/kWh
        self.refit_kWh_cost = self.refit_kWh_consumption * kWh_cost
    
    def calc_capital_costs (self):
        """
        caclulate the total cost of the project
        
        Pre:
            self.opportunity_HH, # occupied of houses  
            self.refit_fuel_cost_rate, cost / refit
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
            self.baseline_fuel_HF_cost, self.refit_HF_cost should be dollar 
        value  arrays over the project life time
        post: 
            self.annual_heating_savings array savings in HF cost
        """
        self.annual_heating_savings = self.baseline_HF_cost - \
                                      self.refit_HF_cost
                                      
    def set_forecast_columns (self):
        """ Function doc """
        years = range(self.start_year,self.end_year)
        self.forecast.add_heating_fuel_column(\
                            "heating_fuel_residential_consumed [gallons/year]",
                                 years, self.baseline_fuel_Hoil_consumption)
        self.forecast.add_heating_fuel_column(\
                "heating_fuel_residential_consumed [mmbtu/year]", years,
                self.baseline_fuel_Hoil_consumption/constants.mmbtu_to_gal_HF)
        
        self.forecast.add_heating_fuel_column(\
                                "cords_wood_residential_consumed [cords/year]",
                                 years, self.baseline_fuel_wood_consumption)
        self.forecast.add_heating_fuel_column(\
                "cords_wood_residential_consumed [mmbtu/year]", years, 
                self.baseline_fuel_wood_consumption/constants.mmbtu_to_cords)
        
        self.forecast.add_heating_fuel_column(\
                                 "gas_residential_consumed [Mcf/year]",
                                 years, self.baseline_fuel_gas_consumption)
        self.forecast.add_heating_fuel_column(\
                      "gas_residential_consumed [mmbtu/year]", years,
                      self.baseline_fuel_gas_consumption/constants.mmbtu_to_Mcf)
                                 
        self.forecast.add_heating_fuel_column(\
                                 "electric_residential_consumed [kWh/year]",
                                 years, self.baseline_fuel_kWh_consumption)
        self.forecast.add_heating_fuel_column(\
                    "electric_residential_consumed [mmbtu/year]", years,
                    self.baseline_fuel_kWh_consumption/constants.mmbtu_to_kWh)
        
        self.forecast.add_heating_fuel_column(\
                                "propane_residential_consumed [gallons/year]",
                                 years, self.baseline_fuel_LP_consumption)
        self.forecast.add_heating_fuel_column(\
                        "propane_residential_consumed [mmbtu/year]", years,
                    self.baseline_fuel_LP_consumption/constants.mmbtu_to_gal_LP)
        
        
        self.forecast.add_heat_demand_column(\
                                 "heat_energy_demand_residential [mmbtu/year]",
                                 years, self.baseline_HF_consumption)
                                 
    def save_component_csv (self, directory):
        """
            save the output from the component. Override the default version 
        because of the extra-fuel sources.
        """
        if not self.run:
            return
            
        if self.cd["model financial"]:
            HF_price = (self.diesel_prices + self.cd['heating fuel premium'])
            wood_price = self.cd['cordwood price'] 
            elec_price = self.elec_prices[self.start_year-self.start_year:
                                             self.end_year-self.start_year]
            LP_price = self.cd['propane price'] 
            gas_price = self.cd['natural gas price'] 
        else:
            HF_price = np.nan
            wood_price = np.nan
            elec_price = np.nan
            LP_price = np.nan
            gas_price = np.nan
        
        b_oil = self.baseline_fuel_Hoil_consumption/constants.mmbtu_to_gal_HF
        r_oil = self.refit_fuel_Hoil_consumption/constants.mmbtu_to_gal_HF
        s_oil = b_oil - r_oil
        b_oil_cost = self.baseline_fuel_Hoil_consumption * HF_price
        r_oil_cost = self.refit_fuel_Hoil_consumption * HF_price
        s_oil_cost = b_oil_cost - r_oil_cost
        
        b_bio = self.baseline_fuel_wood_consumption/constants.mmbtu_to_cords
        r_bio = self.refit_fuel_wood_consumption/constants.mmbtu_to_cords
        s_bio = b_bio - r_bio
        b_bio_cost = self.baseline_fuel_wood_consumption * wood_price
        r_bio_cost = self.refit_fuel_wood_consumption * wood_price
        s_bio_cost = b_bio_cost - r_bio_cost
        
        b_elec = self.baseline_fuel_kWh_consumption/constants.mmbtu_to_kWh
        r_elec = self.refit_fuel_kWh_consumption/constants.mmbtu_to_kWh
        s_elec = b_elec - r_elec
        b_elec_cost = self.baseline_fuel_kWh_consumption * elec_price
        r_elec_cost = self.refit_fuel_kWh_consumption * elec_price
        s_elec_cost = b_elec_cost - r_elec_cost
        
        b_LP = self.baseline_fuel_LP_consumption/constants.mmbtu_to_gal_LP
        r_LP = self.refit_fuel_LP_consumption/constants.mmbtu_to_gal_LP
        s_LP = b_LP - r_LP
        b_LP_cost = self.baseline_fuel_LP_consumption * LP_price
        r_LP_cost = self.refit_fuel_LP_consumption * LP_price
        s_LP_cost = b_LP_cost - r_LP_cost
        
        b_NG = self.baseline_fuel_gas_consumption/constants.mmbtu_to_Mcf
        r_NG = self.refit_fuel_gas_consumption/constants.mmbtu_to_Mcf
        s_NG = b_NG - r_NG
        b_NG_cost = self.baseline_fuel_gas_consumption * gas_price
        r_NG_cost = self.refit_fuel_gas_consumption * gas_price
        s_NG_cost = b_NG_cost - r_NG_cost
        
    
        
        years = np.array(range(self.project_life)) + self.start_year
        df = DataFrame({
        "Residential: Heating Fuel All (MMBtu/year) Consumption Baseline": 
                                    self.get_base_HF_use(),
        "Residential: Heating Fuel All (MMBtu/year) Consumption Post Retrofit": 
                                    self.get_refit_HF_use(),
        "Residential: Heating Fuel All (MMBtu/year) Consumption Savings": 
                                    self.get_base_HF_use() -\
                                    self.get_refit_HF_use(), 
        "Residential: Heating Fuel All (MMBtu/year) Cost Baseline": 
                                    self.get_base_HF_cost(),
        "Residential: Heating Fuel All (MMBtu/year) Cost Post Retrofit": 
                                    self.get_refit_HF_cost(),
        "Residential: Heating Fuel All (MMBtu/year) Cost Savings": 
                                    self.get_heating_savings_costs(),

        "Residential: Heating Oil (gallons/year) Consumption Baseline": 
                                    b_oil,
        "Residential: Heating Oil (gallons/year) Consumption Post Retrofit": 
                                    r_oil,
        "Residential: Heating Oil (gallons/year) Consumption Savings": 
                                    s_oil, 
        "Residential: Heating Oil (gallons/year) Cost Baseline": 
                                    b_oil_cost,
        "Residential: Heating Oil (gallons/year) Cost Post Retrofit": 
                                    r_oil_cost ,
        "Residential: Heating Oil (gallons/year) Cost Savings": 
                                    s_oil_cost,
        
        "Residential: Heating Biomass (cords/year) Consumption Baseline": 
                                    b_bio,
        "Residential: Heating Biomass (cords/year) Consumption Post Retrofit": 
                                    r_bio,
        "Residential: Heating Biomass (cords/year) Consumption Savings": 
                                    s_bio, 
        "Residential: Heating Biomass (cords/year) Cost Baseline": 
                                    b_bio_cost,
        "Residential: Heating Biomass (cords/year) Cost Post Retrofit": 
                                    r_bio_cost,
        "Residential: Heating Biomass (cords/year) Cost Savings": 
                                    s_bio_cost,
        
        "Residential: Electric Heat (kWh/year) Consumption Baseline": 
                                    b_elec,
        "Residential: Electric Heat (kWh/year) Consumption Post Retrofit":
                                    r_elec,
        "Residential: Electric Heat (kWh/year) Consumption Savings": 
                                    s_elec, 
        "Residential: Electric Heat (kWh/year) Cost Baseline": 
                                    b_elec_cost,
        "Residential: Electric Heat (kWh/year) Cost Post Retrofit":
                                    r_elec_cost,
        "Residential: Electric Heat (kWh/year) Cost Savings": 
                                    s_elec_cost,
        
        "Residential: Heating Propane (gallons/year) Consumption Baseline": 
                                    b_LP,
        "Residential: Heating Propane (gallons/year) Consumption Post Retrofit":
                                    r_LP,
        "Residential: Heating Propane (gallons/year) Consumption Savings": 
                                    s_LP, 
        "Residential: Heating Propane (gallons/year) Cost Baseline": 
                                    b_LP_cost,
        "Residential: Heating Propane (gallons/year) Cost Post Retrofit": 
                                    r_LP_cost,
        "Residential: Heating Propane (gallons/year) Cost Savings":
                                    s_LP_cost,
        
        "Residential: Heating Natural Gas (Mcf/year) Consumption Baseline": 
                                    b_NG,
        "Residential: Heating Natural Gas (Mcf/year) Consumption Post Retrofit": 
                                    r_NG,
        "Residential: Heating Natural Gas (Mcf/year) Consumption Savings":
                                    s_NG, 
        "Residential: Heating Natural Gas (Mcf/year) Cost Baseline": 
                                    b_NG_cost,
        "Residential: Heating Natural Gas (Mcf/year) Cost Post Retrofit": 
                                    r_NG_cost,
        "Residential: Heating Natural Gas (Mcf/year) Cost Savings": 
                                    s_NG_cost,

        "Residential: Total Cost Savings ($/year)": 
                                    self.get_total_savings_costs(),
        "Residential: Net Benefit ($/year)":
                                    self.get_net_beneft(),
            }, years)

        try:
            df = df.round().astype(int)
        except ValueError:
            pass
        df = df[[
        "Residential: Heating Oil (gallons/year) Consumption Baseline",
        "Residential: Heating Oil (gallons/year) Consumption Post Retrofit",
        "Residential: Heating Oil (gallons/year) Consumption Savings",
        "Residential: Heating Biomass (cords/year) Consumption Baseline",
        "Residential: Heating Biomass (cords/year) Consumption Post Retrofit",
        "Residential: Heating Biomass (cords/year) Consumption Savings",
        "Residential: Electric Heat (kWh/year) Consumption Baseline",
        "Residential: Electric Heat (kWh/year) Consumption Post Retrofit",
        "Residential: Electric Heat (kWh/year) Consumption Savings",
        "Residential: Heating Propane (gallons/year) Consumption Baseline",
        "Residential: Heating Propane (gallons/year) Consumption Post Retrofit",
        "Residential: Heating Propane (gallons/year) Consumption Savings",
        "Residential: Heating Natural Gas (Mcf/year) Consumption Baseline",
        "Residential: Heating Natural Gas (Mcf/year) Consumption Post Retrofit",
        "Residential: Heating Natural Gas (Mcf/year) Consumption Savings",
        "Residential: Heating Fuel All (MMBtu/year) Consumption Baseline",
        "Residential: Heating Fuel All (MMBtu/year) Consumption Post Retrofit",
        "Residential: Heating Fuel All (MMBtu/year) Consumption Savings",
        "Residential: Heating Oil (gallons/year) Cost Baseline",
        "Residential: Heating Oil (gallons/year) Cost Post Retrofit",
        "Residential: Heating Oil (gallons/year) Cost Savings",
        "Residential: Heating Biomass (cords/year) Cost Baseline",
        "Residential: Heating Biomass (cords/year) Cost Post Retrofit",
        "Residential: Heating Biomass (cords/year) Cost Savings",
        "Residential: Electric Heat (kWh/year) Cost Baseline",
        "Residential: Electric Heat (kWh/year) Cost Post Retrofit",
        "Residential: Electric Heat (kWh/year) Cost Savings",
        "Residential: Heating Propane (gallons/year) Cost Baseline",
        "Residential: Heating Propane (gallons/year) Cost Post Retrofit",
        "Residential: Heating Propane (gallons/year) Cost Savings",
        "Residential: Heating Natural Gas (Mcf/year) Cost Baseline",
        "Residential: Heating Natural Gas (Mcf/year) Cost Post Retrofit",
        "Residential: Heating Natural Gas (Mcf/year) Cost Savings",
        "Residential: Heating Fuel All (MMBtu/year) Cost Baseline",
        "Residential: Heating Fuel All (MMBtu/year) Cost Post Retrofit",
        "Residential: Heating Fuel All (MMBtu/year) Cost Savings",
        "Residential: Total Cost Savings ($/year)",
        "Residential: Net Benefit ($/year)"
                ]]
            
        
        df["community"] = self.cd['name']
        df["population"] = self.forecast.get_population(self.start_year,
                                                    self.end_year).astype(int)
        
        df = df[df.columns[-2:].tolist() + df.columns[:-2].tolist()]

        fname = os.path.join(directory,
                                   self.cd['name'] + '_' +\
                                   self.component_name + "_output.csv")
        fname = fname.replace(" ","_")
        # save to end of project(actual lifetime)
        df.ix[:self.actual_end_year].to_csv(fname, index_label="year")
        

component = ResidentialBuildings

def test ():
    """
    tests the class using the manley data.
    """
    manley_data = CommunityData("../test_case/input_data/",
                            "../test_case/baseline_results/config_used.yaml")
    
    fc = Forecast(manley_data)
    t = ResidentialBuildings(manley_data,fc)
    t.run()
    return t,fc
