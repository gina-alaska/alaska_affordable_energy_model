"""
residential_bulidings.py
Ross Spicer
created 2015/09/30

    residential buildings tab.
"""
import numpy as np
from math import isnan
from pandas import DataFrame

from annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants
import os

class ResidentialBuildings(AnnualSavings):
    """
    for forecasting residential building consumption/savings   
    """
    
    def __init__ (self, community_data, forecast, diag=None):
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
        self.elec_prices = community_data.electricity_price
        self.comp_specs = community_data.get_section('residential buildings')
        self.component_name = 'residential buildings'
        self.forecast = forecast
        self.refit_cost_rate = self.comp_specs['average refit cost'] * \
      community_data.get_section('construction multipliers')[self.cd["region"]]
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
    
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
        self.calc_avg_consumption()
        self.calc_init_HH()
        self.calc_savings_opportunities()
        self.calc_init_consumption()
        
        self.calc_capital_costs()
        
        
        self.calc_baseline_fuel_consumption()
        
        
        self.calc_refit_fuel_consumption()
        
        self.set_forecast_columns()
        
        if self.cd["model financial"]:
            self.get_diesel_prices()
            self.calc_baseline_fuel_cost() 
            self.calc_refit_fuel_cost()
            
            
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            self.calc_annual_total_savings()
            
            self.calc_annual_costs(self.cd['interest rate'])
            self.calc_annual_net_benefit()
            
            self.calc_npv(self.cd['discount rate'], self.cd['current year'])
    
    def calc_avg_consumption (self, con_threshold = 6000.0):
        """ 
        get the average monthly consumption
        
        pre:
        
        post: 
        """
        #   500 average energy use, 12 months in a year. That's whrer the 6000.0
        # comes from.
        
        yr = int(self.comp_specs['data'].ix['year'])
        houses = int(self.comp_specs['data'].ix['total_occupied'])
        r_con = self.forecast.base_res_consumption
        avg_con = r_con/houses
        #~ self.avg_monthly_consumption = ave_con/12
        if avg_con < con_threshold:
            avg_con = con_threshold
        self.avg_consumption = avg_con
        
        self.diagnostics.add_note(self.component_name,
                    "Average consumption was " + str(self.avg_consumption) +\
                    " in " + str(yr))
        
        #~ print self.avg_consumption
    
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
  
        HH_consumption = HH * self.avg_consumption * constants.kWh_to_mmbtu
        return np.float64(fuel_amnt * (total_consumption - HH_consumption) * cf)
                            
    def calc_baseline_fuel_consumption (self):
        """
        """
        rd = self.comp_specs['data'].T
        self.fuel_oil_percent = rd["Fuel Oil"]
        HH = self.forecast.get_households(self.start_year,self.end_year)
        
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
        
        
        self.baseline_HF_consumption = \
            self.baseline_fuel_Hoil_consumption * \
                (1/constants.mmbtu_to_gal_HF) +\
            self.baseline_fuel_wood_consumption * \
                (1/constants.mmbtu_to_cords) +\
            self.baseline_fuel_gas_consumption * (1/constants.mmbtu_to_Mcf) +\
            self.baseline_fuel_kWh_consumption * (1/constants.mmbtu_to_kWh) +\
            self.baseline_fuel_LP_consumption * (1/constants.mmbtu_to_gal_LP)
        

    def calc_baseline_fuel_cost (self):
        """
        """
        HF_price = (self.diesel_prices + self.cd['heating fuel premium'])
        wood_price = self.cd['biomass price'] 
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
        # coal,solar, other
        
    def calc_refit_fuel_cost (self):
        """
        """
        HF_price = (self.diesel_prices + self.cd['heating fuel premium'])
        wood_price = self.cd['biomass price'] 
        elec_price = self.elec_prices[self.start_year-self.start_year:
                                         self.end_year-self.start_year]
        LP_price = self.cd['propane price'] 
        gas_price = self.cd['natural gas price'] 
        
        
        self.refit_HF_cost = self.refit_fuel_Hoil_consumption * HF_price + \
                             self.refit_fuel_wood_consumption * wood_price + \
                             self.refit_fuel_gas_consumption * gas_price + \
                             self.refit_fuel_LP_consumption * LP_price + \
                             self.refit_fuel_kWh_consumption * gas_price
    
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
        HF_price = (self.diesel_prices + self.cd['heating fuel premium'])
        wood_price = 250 # TODO: change to mutable
        elec_price = self.elec_prices[self.start_year-self.start_year:
                                         self.end_year-self.start_year]
        LP_price = 0 # TODO: find
        gas_price = 0 # TODO: find
        
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
            "Heating Fuel (All) Consumption Baseline": self.get_base_HF_use(),
            "Heating Fuel (All) Consumption Retrofit": self.get_refit_HF_use(),
            "Heating Fuel (All) Consumption Savings": self.get_base_HF_use() -\
                                        self.get_refit_HF_use(), 
            "Heating Fuel (All) Cost Baseline": self.get_base_HF_cost(),
            "Heating Fuel (All) Cost Retrofit": self.get_refit_HF_cost(),
            "Heating Fuel (All) Cost Savings": 
                                    self.get_heating_savings_costs(),
    
            "Heating Fuel (Oil) Consumption Baseline": b_oil,
            "Heating Fuel (Oil) Consumption Retrofit": r_oil,
            "Heating Fuel (Oil) Consumption Savings": s_oil, 
            "Heating Fuel (Oil) Cost Baseline": b_oil_cost,
            "Heating Fuel (Oil) Cost Retrofit": r_oil_cost ,
            "Heating Fuel (Oil) Cost Savings": s_oil_cost,
            
            "Heating Fuel (Biomass) Consumption Baseline": b_bio,
            "Heating Fuel (Biomass) Consumption Retrofit": r_bio,
            "Heating Fuel (Biomass) Consumption Savings": s_bio, 
            "Heating Fuel (Biomass) Cost Baseline": b_bio_cost,
            "Heating Fuel (Biomass) Cost Retrofit": r_bio_cost,
            "Heating Fuel (Biomass) Cost Savings": s_bio_cost,
            
            "Heating Fuel (Electric) Consumption Baseline": b_elec,
            "Heating Fuel (Electric) Consumption Retrofit": r_elec,
            "Heating Fuel (Electric) Consumption Savings": s_elec, 
            "Heating Fuel (Electric) Cost Baseline": b_elec_cost,
            "Heating Fuel (Electric) Cost Retrofit": r_elec_cost,
            "Heating Fuel (Electric) Cost Savings": s_elec_cost,
            
            "Heating Fuel (Propane) Consumption Baseline": b_LP,
            "Heating Fuel (Propane) Consumption Retrofit": r_LP,
            "Heating Fuel (Propane) Consumption Savings": s_LP, 
            "Heating Fuel (Propane) Cost Baseline": b_LP_cost,
            "Heating Fuel (Propane) Cost Retrofit": r_LP_cost,
            "Heating Fuel (Propane) Cost Savings": s_LP_cost,
            
            "Heating Fuel (Natural Gas) Consumption Baseline": b_NG,
            "Heating Fuel (Natural Gas) Consumption Retrofit": r_NG,
            "Heating Fuel (Natural Gas) Consumption Savings": s_NG, 
            "Heating Fuel (Natural Gas) Cost Baseline": b_NG_cost,
            "Heating Fuel (Natural Gas) Cost Retrofit": r_NG_cost,
            "Heating Fuel (Natural Gas) Cost Savings": s_NG_cost,
    
            "Total Cost Savings": self.get_total_savings_costs(),
            "Net Benefit": self.get_net_beneft(),
            }, years)

        df = df.round().astype(int)
        df = df[[
                "Heating Fuel (Oil) Consumption Baseline",
                "Heating Fuel (Oil) Consumption Retrofit",
                "Heating Fuel (Oil) Consumption Savings",
                "Heating Fuel (Biomass) Consumption Baseline",
                "Heating Fuel (Biomass) Consumption Retrofit",
                "Heating Fuel (Biomass) Consumption Savings",
                "Heating Fuel (Electric) Consumption Baseline",
                "Heating Fuel (Electric) Consumption Retrofit",
                "Heating Fuel (Electric) Consumption Savings",
                "Heating Fuel (Propane) Consumption Baseline",
                "Heating Fuel (Propane) Consumption Retrofit",
                "Heating Fuel (Propane) Consumption Savings",
                "Heating Fuel (Natural Gas) Consumption Baseline",
                "Heating Fuel (Natural Gas) Consumption Retrofit",
                "Heating Fuel (Natural Gas) Consumption Savings",
                "Heating Fuel (All) Consumption Baseline",
                "Heating Fuel (All) Consumption Retrofit",
                "Heating Fuel (All) Consumption Savings",
                "Heating Fuel (Oil) Cost Baseline",
                "Heating Fuel (Oil) Cost Retrofit",
                "Heating Fuel (Oil) Cost Savings",
                "Heating Fuel (Biomass) Cost Baseline",
                "Heating Fuel (Biomass) Cost Retrofit",
                "Heating Fuel (Biomass) Cost Savings",
                "Heating Fuel (Electric) Cost Baseline",
                "Heating Fuel (Electric) Cost Retrofit",
                "Heating Fuel (Electric) Cost Savings",
                "Heating Fuel (Propane) Cost Baseline",
                "Heating Fuel (Propane) Cost Retrofit",
                "Heating Fuel (Propane) Cost Savings",
                "Heating Fuel (Natural Gas) Cost Baseline",
                "Heating Fuel (Natural Gas) Cost Retrofit",
                "Heating Fuel (Natural Gas) Cost Savings",
                "Heating Fuel (All) Cost Baseline",
                "Heating Fuel (All) Cost Retrofit",
                "Heating Fuel (All) Cost Savings",
                "Total Cost Savings",
                "Net Benefit"
                ]]
            
        
        df["community"] = self.cd['name']
        df["population"] = self.forecast.get_population(self.start_year,
                                                        self.end_year).astype(int)

        df = df[df.columns[-2:].tolist() + df.columns[:-2].tolist()]

        fname = os.path.join(directory,
                                   self.component_name + "_output.csv")
        fname = fname.replace(" ","_")
        
        
        fin_str = "Enabled" if self.cd["model financial"] else "Disabled"
        fd = open(fname, 'w')
        fd.write(("# " + self.component_name + " model outputs\n"
          "# year: year for projection \n"
          "# consumption columns are the are"
                    " the ammout of fuel used by type(mmbtu)\n"
          "# cost columns are in dollars"
          "# Project Capital Cost: Cost of retrofits \n"
          "# Total Cost Savings: savings from retrofits\n"
          "# Net Benefit: benefit from retrofits\n"
                  )) 
        fd.close()
        
        # save npv stuff
        df2 = DataFrame([self.get_NPV_benefits(),self.get_NPV_costs(),
                            self.get_NPV_net_benefit(),self.get_BC_ratio()],
                       ['NPV Benefits','NPV Cost',
                            'NPV Net Benefit','Benefit Cost Ratio'])
        df2.to_csv(fname, header = False, mode = 'a')
        
        # save to end of project(actual lifetime)
        df.ix[:self.actual_end_year].to_csv(fname, index_label="year", 
                                                                    mode = 'a')
        

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
