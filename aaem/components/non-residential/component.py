"""
component.py

    Non-Residential Building Efficiency component body
"""
import numpy as np
from pandas import DataFrame, concat
import os
from copy import deepcopy

from aaem.components.annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import diagnostics
import aaem.constants as constants
from config import COMPONENT_NAME, UNKNOWN

from inputs import load_building_data
from inputs import load_num_buildings
from inputs import load_building_estimates 


class CommunityBuildings (AnnualSavings):
    """
    for forecasting community building consumption/savings  
    """
    
    def __init__ (self, community_data, forecast, 
                        diag = None, prerequisites = {}):
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
        self.comp_specs =community_data.get_section(COMPONENT_NAME)
        
        self.intertie = community_data.intertie
        if self.intertie is None:
            self.intertie = 'none'
        else:
            # get the intertie building inventory
            self.get_intertie_builing_inventory(community_data)
        
        self.comp_specs =community_data.get_section(COMPONENT_NAME)
        self.percent_diesel = community_data.percent_diesel 
        self.component_name = COMPONENT_NAME
        self.forecast = forecast
        #~ print self.comp_specs['average refit cost']
        #~ print community_data.get_section('construction multipliers')[self.cd["region"]]
        #~ print self.comp_specs['average refit cost'] * \
      #~ community_data.get_section('construction multipliers')[self.cd["region"]]
        
        self.refit_cost_rate = self.comp_specs['average refit cost'] * \
                community_data.get_item('community','construction multiplier')
        self.set_project_life_details(self.comp_specs["start year"],
                                      self.comp_specs["lifetime"],
                        self.forecast.end_year - self.comp_specs["start year"])
         
        #~ print self.refit_cost_rate 
        self.buildings_df = deepcopy(self.comp_specs["com building data"])
        freq = {}
        for item in self.buildings_df.index.tolist():
            try:
                freq[item] += 1
            except KeyError:
                freq[item] = 1
        df = DataFrame(freq.values(),freq.keys(),["count"])
        self.buildings_df = \
                    self.buildings_df.groupby(self.buildings_df.index).sum()
        self.buildings_df = concat([df,self.buildings_df],axis=1)
        
    def get_intertie_builing_inventory(self, community_data):
        """
        for interties we need to load the entire building inventory
        """
        data_dir = os.path.split(community_data.data_dir)[0]
        parent = community_data.parent
        it_path = os.path.join(data_dir, parent.replace(' ','_') + '_intertie')
        ## function is at top of this file
        self.intertie_inventory = load_building_data(it_path)
        self.intertie_estimates = load_building_estimates(it_path)
        self.intertie_count = load_num_buildings(it_path)
        
        
        
        #add extra buildings
        additional_buildings = \
            max(self.intertie_count - len(self.intertie_inventory),0)
       
        if additional_buildings > 0:
            l = []
            for i in range(additional_buildings):
                l.append(DataFrame({"Square Feet":np.nan,}, 
                                                        index = ["Average"]))
            self.intertie_inventory = self.intertie_inventory.append(l)
            
        ### estimate the square footage for the intertie inventory
        keys = set(self.intertie_inventory.T.keys())
        #~ print keys
        sqft_ests = self.intertie_estimates["Sqft"]
        #~ print sqft_ests
        measure = "Square Feet"
        for k in keys:
            try:
                # more than one item for each k 
                self.intertie_inventory.loc[:,measure].loc[k] = \
                            self.intertie_inventory.loc[:,measure].loc[k].\
                                                        fillna(sqft_ests.ix[k])
            except AttributeError:
                # only one item 
                if np.isnan(self.intertie_inventory.ix[k][measure]):
                    try:
                        self.intertie_inventory[measure][k] = sqft_ests.ix[k]
                    except KeyError:
                        self.diagnostics.add_note(self.component_name, 
                            "Building Type: " + k +\
                            " not valid. Using 'other's estimates")
                        #~ print sqft_ests
                        self.intertie_inventory.ix[k][measure] = \
                                                    sqft_ests.ix['Other']
            except KeyError:
                self.diagnostics.add_note(self.component_name, 
                 "Building Type: " + k + " not valid. Using 'other's estimates")
                self.intertie_inventory.loc[:,measure].loc[k] = \
                    self.intertie_inventory.loc[:,measure].loc[k].\
                                                fillna(sqft_ests.ix['Other'])        
       
        
        
    def save_building_summay(self, file_name):
        """
        """
        if not self.run:
            return
            
        with_estimates = deepcopy(self.comp_specs["com building data"])
        try:
            if 'Average' in set(with_estimates.ix['Average'].index) :
                num = len(with_estimates.ix['Average'])
            else:
                num = 1
        except KeyError:
            pass
        
        with_estimates = with_estimates.groupby(with_estimates.index).sum()
        with_estimates.columns = \
                [c+" with estimates" for c in with_estimates.columns]
        
        summary = concat([self.buildings_df,with_estimates],axis=1)
        cols = self.buildings_df.columns[1:]
        cols = list(set(cols).difference("Water & Sewer"))
        order = ["count"] 
        for col in cols:
            if col in ["Retrofits Done", "Audited"]:
                order += [col]
                continue
            order += [col, col+" with estimates"] 
        
        try:
            summary.ix["Unknown"] =  summary.ix["Average"] 
            summary = summary[summary.index != "Average"]
        
            summary.ix["Unknown"]['count'] = num
        except KeyError:
            pass
        try:
            
            summary[order].to_csv(file_name)
        except KeyError:
            self.diagnostics.add_note(self.component_name, 
                        ("in saving the building list the "
                         "standard order could not be used"))
            summary.to_csv(file_name)
        
    
    def save_additional_output(self, path):
        """
        """
        if not self.run:
            return
        self.save_building_summay(os.path.join(path, self.cd['name'] + '_' +\
                                self.component_name.lower().replace(' ','_') + \
                                "_buildings_summary.csv"))
        
    
    def run (self, scalers = {'capital costs':1.0}):
        """
        run the forecast model
        
        pre:
            self.cd should be the community library from a community data object
        post:
            TODO: define output values. 
            the model is run and the output values are available
        """
        self.run = True
        self.reason = "OK"
        
        tag = self.cd['name'].split('+')
        if len(tag) > 1 and tag[1] != 'non-residential':
            self.run = False
            self.reason = "Not a non-residential project"
            return 
        
        self.update_num_buildings()
        #~ self.calc_refit_values()
        
        if len(self.comp_specs['com building data']) == 0:
            self.run = False
            self.reason = "No Buildings"
            return 
        
        self.calc_total_sqft_to_retrofit()
        
        
        self.calc_baseline_kWh_consumption()
        self.calc_proposed_kWh_consumption()
        
        self.calc_baseline_HF_consumption()
        self.calc_proposed_HF_consumption()
        
        #~ print self.comp_specs['com building data']
        #~ import sys
        #~ sys.exit()
        #~ self.pre_retrofit_HF_use = np.zeros(self.project_life) + \
                                                    #~ self.baseline_HF_consumption 
                                                    
        
        #~ self.post_retrofit_HF_use = np.zeros(self.project_life) + \
                                                    #~ self.proposed_HF_consumption  
                                                
        years = range(self.start_year,self.end_year)
        self.forecast.add_heating_fuel_column(\
                    "heating_fuel_non-residential_consumed [gallons/year]",
                    years, 
                    self.baseline_HF_consumption * constants.mmbtu_to_gal_HF)
        self.forecast.add_heating_fuel_column(\
                    "heating_fuel_non-residential_consumed [mmbtu/year]", years,
                     self.baseline_HF_consumption)
        
        self.forecast.add_heat_demand_column(\
                    "heat_energy_demand_non-residential [mmbtu/year]",
                 years, self.baseline_HF_consumption)
        
        if self.cd["model financial"]:
            self.get_diesel_prices()
            self.get_electricity_prices() 
            
            self.calc_capital_costs()
            self.calc_annual_electric_savings()
            self.calc_annual_heating_savings()
            self.calc_annual_total_savings()
            
            self.calc_annual_costs(self.cd['interest rate'],
                                            scalers['capital costs'])
            self.calc_annual_net_benefit()
            
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
            
            ## no maintaince cost
            self.calc_levelized_costs(0)
            heating_cost_percent = self.comp_specs['heating cost precent']
            #scale by heating_cost_percent
            self.break_even_cost *= heating_cost_percent

    def update_num_buildings (self):
        """
            This function compares the counted buildings with the estimated 
        buildings
        
        pre:
            'com building data' is a DataFrame, and "number buildings" is 
        an integer 
        post:
            a warning may be added to self.diagnostics 
        """
        self.num_buildings = self.comp_specs["number buildings"]
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
                
                self.add_additional_buildings()
            
    def add_additional_buildings (self, num_not_heated = 0):
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
        
    #~ def calc_refit_values (self):
        #~ """
        #~ calculate the forecast input values related to refit buildings
        
        #~ pre:
            #~ None
        
        #~ post:
            #~ TODO: define this better
            #~ refit forecast inputs are calculated.
        #~ """
        #~ self.calc_refit_sqft()
        #~ self.calc_refit_cost()
        #~ self.calc_baseline_HF_consumption()
        #~ self.calc_baseline_kWh_consumption()
        #~ self.calc_refit_savings_HF()
        #~ self.calc_refit_savings_kWh()
        
        
    def calc_total_sqft_to_retrofit (self):
        """ 
        calc refit square feet 
          
        pre:
            self.comp_specs["com building estimates"]["Sqft"] is a Pandas series
        indexed by building type of sqft. estimates for the community. 
        self.comp_specs['com building data'] is a Pandas DataFrame containing 
        the actual data on buildings in the community, indexed by building type
        post:
            self.total_sqft_to_retrofit is the total sqft. that can retrofitted in
        the community. self.comp_specs['com building data']['Square Feet'] has
        been updated with square footage estimates. 
        """
        sqft_ests = self.comp_specs["com building estimates"]["Sqft"]
        data = self.comp_specs['com building data']
        
        keys = set(data.T.keys())
        #~ print keys
        measure = "Square Feet"
        
        for k in keys:
            try:
                # more than one item for each k 
                data.loc[:,measure].loc[k] = \
                            data.loc[:,measure].loc[k].fillna(sqft_ests.ix[k])
            except AttributeError:
                # only one item 
                if np.isnan(data.ix[k][measure]):
                    try:
                        data[measure][k] = sqft_ests.ix[k]
                    except KeyError:
                        self.diagnostics.add_note(self.component_name, 
                            "Building Type: " + k +\
                            " not valid. Using 'other's estimates")
                        #~ print sqft_ests
                        data.ix[k][measure] = sqft_ests.ix['Other']
            except KeyError:
                self.diagnostics.add_note(self.component_name, 
                 "Building Type: " + k + " not valid. Using 'other's estimates")
                data.loc[:,measure].loc[k] = \
                    data.loc[:,measure].loc[k].fillna(sqft_ests.ix['Other'])
        self.total_sqft_to_retrofit = data[measure].sum()
        
    
    def calc_capital_costs (self):
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
        self.capital_costs = data[measure].sum()
        
    def calc_baseline_HF_consumption (self):
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
        keys = set(keys)
        
        data["HDD ESTS"] = 0
        data["GAL/SF"] = 0
        for key in keys:
            try:
                data["HDD ESTS"].ix[key] = self.cd["HDD"]/HDD_ests[key]
                data["GAL/SF"].ix[key] = gal_sf_ests.ix[key] 
            except KeyError:
                data["HDD ESTS"].ix[key] = self.cd["HDD"]/HDD_ests.ix['Other'] # unitless
                data["GAL/SF"].ix[key] = gal_sf_ests.ix['Other'] # (gal)/sqft
        
        
        idx = data[['Fuel Oil', "Natural Gas",
                    'HW District','Propane',"Biomass"]].isnull().all(1)
        if not self.cd['natural gas used']:
            data['Fuel Oil'].ix[idx] = data[idx]['Square Feet'] * \
                                       data[idx]['HDD ESTS'] * \
                                       data[idx]['GAL/SF']
        else:
            data['Natural Gas'].ix[idx] = data[idx]['Square Feet'] * \
                                       data[idx]['HDD ESTS'] * \
                                       data[idx]['GAL/SF'] / \
                                       constants.mmbtu_to_gal_HF *\
                                       constants.mmbtu_to_Mcf
        del data["GAL/SF"]
        del data["HDD ESTS"]
        

                                           
        self.baseline_fuel_Hoil_consumption = data['Fuel Oil'].fillna(0).sum()
        self.baseline_fuel_lng_consumption = data['Natural Gas'].fillna(0).sum()
        self.baseline_fuel_hr_consumption = data['HW District'].fillna(0).sum()
        self.baseline_fuel_propane_consumption = data['Propane'].fillna(0).sum()
        self.baseline_fuel_biomass_consumption = data['Biomass'].fillna(0).sum()
        
        
        self.baseline_HF_consumption = \
            self.baseline_fuel_Hoil_consumption / constants.mmbtu_to_gal_HF +\
            self.baseline_fuel_hr_consumption/constants.mmbtu_to_gal_HF+\
            self.baseline_fuel_lng_consumption/constants.mmbtu_to_Mcf+\
            self.baseline_fuel_propane_consumption/constants.mmbtu_to_gal_LP+\
            self.baseline_fuel_biomass_consumption/constants.mmbtu_to_cords

            
        
    def calc_baseline_kWh_consumption (self):
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
        local_inv = data[["Square Feet", measure]].T.values.tolist()
        local_inv.insert(0,keys.values.tolist())
        local_inv = np.array(local_inv).T
        inv = local_inv
        #~ print inv
        #~ print self.intertie 
        if self.intertie != 'none':
            keys = self.intertie_inventory.T.keys()
            #~ print keys
            it_inv = self.intertie_inventory[["Square Feet", 
                                                measure]].T.values.tolist()
            it_inv.insert(0,keys.values.tolist())
            it_inv = np.array(it_inv).T
            kwh_sf_ests = self.intertie_estimates["kWh/sf"]
            
            inv = it_inv
        #~ print inv
        keys = set(keys)
        keys.add('Average')
        
        kwh_buildings = deepcopy(local_inv)
        #~ print kwh_buildings
        
        #~ print kwh_sf_ests
        
        
        # step 0a: find total estmated + known consumption
        #~ print keys
        for k in keys:
            try:
                kwh_sf = kwh_sf_ests.ix[k] # (kWh)/sqft
            except KeyError:
                kwh_sf = kwh_sf_ests.ix['Other'] # (kwh)/sqft
            
            idx = np.logical_and(local_inv[:,0] == k, 
                                np.isnan(local_inv[:,2].astype(float)))
            sqft = local_inv[idx, 1].astype(np.float64) #sqft
            local_inv[idx, 2] = sqft * kwh_sf # kWh
            
        if self.intertie != 'none':
            for k in keys:
                try:
                    kwh_sf = kwh_sf_ests.ix[k] # (kWh)/sqft
                except KeyError:
                    kwh_sf = kwh_sf_ests.ix['Other'] # (kwh)/sqft
                     
                idx = np.logical_and(inv[:,0] == k, 
                                    np.isnan(inv[:,2].astype(float)))
                sqft = inv[idx, 1].astype(np.float64) #sqft
                inv[idx, 2] = sqft * kwh_sf # kWh
        else:
            inv = local_inv
        
            
          
        #~ print inv
        # step 0b: find Ratio
        # Inventory total
        estimated_total = inv[:,2].astype(np.float64).sum()
        # Trend total
        try:
            fc_total = float(self.forecast.\
                                        consumption_to_save.ix[self.start_year]\
                                                        ['non-residential kWh'])
        except AttributeError:
            fc_total = estimated_total

        #~ print fc_total, estimated_total
        ratio =  fc_total/estimated_total
        #~ print ratio
        #~ print kwh_buildings
        # step 1 & 2: loop if consumption known use; other wise scale:
        for idx in range(len(kwh_buildings)):
            if np.isnan(kwh_buildings[idx, 2].astype(float)):
                kwh_buildings[idx, 2] = ratio * local_inv[idx, 2].astype(float)
                
                
        #~ print kwh_buildings
        data[measure] =  kwh_buildings[:,2].astype(np.float64)  
        self.baseline_kWh_consumption = data[measure].sum()
        #~ print self.baseline_kWh_consumption
        
    def calc_proposed_HF_consumption (self):
        """ 
        """
        building_data = self.comp_specs['com building data']
        percent_savings = self.comp_specs['cohort savings multiplier']
        #~ fuel_type = 'Fuel Oil'
        #~ try:
        fuel_types = ['Fuel Oil',
                      'Natural Gas', 
                      'HW District',
                      'Propane',
                      'Biomass']
        for fuel_type in fuel_types:
            fuel_vals = building_data[fuel_type + ' Post']
            idx = fuel_vals.isnull()
            fuel_vals[idx] = building_data[fuel_type][idx] *\
                                                (1 - percent_savings)
       
        #~ except TypeError:
            
            
            
            #~ self.comp_specs['com building data']["Fuel Oil Post"] = \
                        #~ self.comp_specs['com building data']["Fuel Oil"]*\
                        #~ self.comp_specs['cohort savings multiplier']
        
        
        
        
        # by fuel type
        self.proposed_fuel_Hoil_consumption = \
                            building_data['Fuel Oil Post'].sum()
        self.proposed_fuel_lng_consumption = \
                            building_data['Natural Gas Post'].fillna(0).sum()
        self.proposed_fuel_hr_consumption = \
                            building_data['HW District Post'].fillna(0).sum()
        self.proposed_fuel_propane_consumption = \
                            building_data['Propane Post'].fillna(0).sum()
        self.proposed_fuel_biomass_consumption = \
                            building_data['Biomass Post'].fillna(0).sum()
          
        # mmbtu 
        self.proposed_HF_consumption = \
            self.proposed_fuel_Hoil_consumption / constants.mmbtu_to_gal_HF +\
            self.proposed_fuel_hr_consumption/constants.mmbtu_to_gal_HF+\
            self.proposed_fuel_lng_consumption/constants.mmbtu_to_Mcf+\
            self.proposed_fuel_propane_consumption/constants.mmbtu_to_gal_LP+\
            self.proposed_fuel_biomass_consumption/constants.mmbtu_to_cords              
        
    def calc_proposed_kWh_consumption (self):
        """ 
        calculate refit kWh savings
        
        pre:
            tbd
        post: 
            self.refit_savings_kWh, self.benchmark_savings_kWh,
        self.additional_savings_kWh, are floating-point kWh values
        """
        building_data = self.comp_specs['com building data']
        percent_savings = self.comp_specs['cohort savings multiplier']
    
        elec_vals = building_data['Electric Post']
        idx = elec_vals.isnull()
        elec_vals[idx] = building_data['Electric'][idx] * (1 - percent_savings)
        
        #kWh
        
        self.proposed_kWh_consumption = elec_vals.sum()
        
    #~ def calc_post_refit_use (self):
        #~ """ 
        #~ calculate post refit HF and kWh use
        
        #~ pre:
            #~ pre refit and savigns values should be calculated
        #~ post: 
            #~ refit_pre_kWh_total is the total number of kWh used after a 
        #~ refit(float)
            #~ same  for self.refit_HF_consumption but with HF
        #~ """
        
        #~ self.refit_HF_consumption = self.baseline_HF_consumption - \
                                                #~ self.refit_savings_HF_total
        #~ self.refit_fuel_Hoil_consumption = \
                #~ self.refit_HF_consumption*constants.mmbtu_to_gal_HF
        #~ self.refit_kWh_consumption = self.baseline_kWh_consumption - \
                                                #~ self.refit_savings_kWh_total
                                                
    def get_fuel_total_saved (self):
        """
        returns the total fuel saved in gallons
        """
        #~ gen_eff = self.cd["diesel generation efficiency"]
        
        HF_savings = \
            (self.baseline_HF_consumption - self.proposed_HF_consumption) *\
            constants.mmbtu_to_gal_HF
        return HF_savings #+ \
                #~ self.refit_savings_kWh_total / gen_eff
                                
    def get_total_enery_produced (self):
        """
        returns the total energy saved 
        """
        kWh_savings = self.baseline_kWh_consumption - \
                        self.proposed_kWh_consumption
        HF_savings = self.baseline_HF_consumption - \
                        self.proposed_HF_consumption
        heating_cost_percent = self.comp_specs['heating cost precent']
        return {'kWh': (kWh_savings, 1 - heating_cost_percent), 
                'MMBtu': (HF_savings, heating_cost_percent)
               }
        
    #~ def calc_capital_costs (self):
        #~ """
        #~ pre:
            #~ self.refit_cost_total is a dollar value
        #~ post:
            #~ self.capital_costs is the refit cost
        #~ """
        #~ self.capital_costs = self.refit_cost_total
    
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
        elec_price = self.electricity_prices.ix[self.start_year:\
                                                    self.end_year-1]
        self.elec_price = elec_price.T.values[0]


        #~ print self.elec_price
        #~ print 
        
        #~ print self.intertie
        #~ if self.intertie == "child":
            #~ self.baseline_kWh_cost = [0]
            #~ self.proposed_kWh_cost = [0]
            #~ self.annual_electric_savings = [0]
            #~ return
        
        self.baseline_kWh_cost = self.baseline_kWh_consumption * self.elec_price
                    
        self.proposed_kWh_cost = self.proposed_kWh_consumption * self.elec_price
        
        self.annual_electric_savings = self.baseline_kWh_cost - \
                                        self.proposed_kWh_cost
        
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
        self.hoil_price = (self.diesel_prices + self.cd['heating fuel premium'])
        
        hr_price = self.hoil_price * self.comp_specs['HW District price %']
        
        wood_price = self.cd['cordwood price'] 
        LP_price = self.cd['propane price'] 
        LNG_price = self.cd['natural gas price']

        # heating oil
        self.baseline_fuel_Hoil_cost = \
                self.baseline_fuel_Hoil_consumption * self.hoil_price
        self.proposed_fuel_Hoil_cost = \
                self.proposed_fuel_Hoil_consumption * self.hoil_price
        self.annual_fuel_Hoil_savings = self.baseline_fuel_Hoil_cost - \
                                            self.proposed_fuel_Hoil_cost
        
        # all fuels
        self.baseline_HF_cost = \
            self.baseline_fuel_Hoil_consumption * self.hoil_price + \
            self.baseline_fuel_hr_consumption * hr_price + \
            self.baseline_fuel_lng_consumption * LNG_price + \
            self.baseline_fuel_propane_consumption * LP_price + \
            self.baseline_fuel_biomass_consumption * wood_price
    
        self.proposed_HF_cost = \
            self.baseline_fuel_Hoil_consumption * self.hoil_price + \
            self.baseline_fuel_hr_consumption * hr_price  + \
            self.baseline_fuel_lng_consumption * LNG_price + \
            self.baseline_fuel_propane_consumption * LP_price + \
            self.baseline_fuel_biomass_consumption * wood_price
        
        self.annual_heating_savings = self.baseline_HF_cost - \
                                            self.proposed_HF_cost
        
    
