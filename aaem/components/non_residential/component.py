"""
Non-residential Efficiency component body
-----------------------------------------

"""
import numpy as np
from pandas import DataFrame, concat
import os
from copy import deepcopy

from aaem.components.annual_savings import AnnualSavings
from aaem.community_data import CommunityData
from aaem.forecast import Forecast
from aaem.diagnostics import Diagnostics
import aaem.constants as constants
from config import COMPONENT_NAME, UNKNOWN

class CommunityBuildings (AnnualSavings):
    """Non-residential Efficiency component of the Alaska Affordable Eenergy 
    Model

    Parameters
    ----------
    commnity_data : CommunityData
        CommintyData Object for a community
    forecast : Forecast
        forcast for a community 
    diagnostics : diagnostics, optional
        diagnostics for tracking error/warining messeges
    prerequisites : dictionary of components, optional
        prerequisite component data this component has no prerequisites 
        leave empty
        
    Attributes
    ----------
    diagnostics : diagnostics
        for tracking error/warining messeges
        initial value: diag or new diagnostics object
    forecast : forecast
        community forcast for estimating future values
        initial value: forecast
    cd : dictionary
        general data for a community.
        Initial value: 'community' section of community_data
    comp_specs : dictionary
        component specific data for a community.
        Initial value: 'Non-Residential Buildings' section of community_data
        
    See also
    --------
    aaem.community_data : 
        community data module, see for information on CommintyData Object
    aaem.forecast : 
        forecast module, see for information on Forecast Object
    aaem.diagnostics :
        diagnostics module, see for information on diagnostics Object

    """
    
    def __init__ (self, community_data, forecast, 
                        diag = None, prerequisites = {}):
        """Class initialiser
        
        Parameters
        ----------
        commnity_data : CommunityData
            CommintyData Object for a community
        forecast : Forecast
            forcast for a community 
        diagnostics : diagnostics, optional
            diagnostics for tracking error/warining messeges
        prerequisites : dictionary of components, optional
            prerequisite component data

        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.cd = community_data.get_section('community')
        self.intertie_data = community_data.intertie_data
        self.comp_specs =community_data.get_section(COMPONENT_NAME)

        
        self.comp_specs =community_data.get_section(COMPONENT_NAME)
        self.percent_diesel = self.cd['percent diesel generation']
        self.component_name = COMPONENT_NAME
        self.forecast = forecast
        
        self.refit_cost_rate = self.comp_specs['average refit cost'] * \
                community_data.get_item('community',
                    'regional construction multiplier')
        self.set_project_life_details(
            self.comp_specs["start year"],
            self.comp_specs["lifetime"])
         
        self.buildings_df = deepcopy(self.comp_specs["building inventory"])
        self.buildings_df = self.buildings_df.set_index('Building Type')
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
        
    def save_building_summay(self, file_name):
        """save builing summary for community
        
        Parameters
        ----------
        file_name: path
            name of file to save (.csv)
        """
        if not self.run:
            return
            
        with_estimates = deepcopy(self.comp_specs["building inventory"])
        with_estimates = with_estimates.set_index('Building Type')
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
        #~ print summary
        #~ summary = summary
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
        """save additional out put for component
        
        Parameters
        ----------
        path : path 
            location to save files at
        """
        if not self.run:
            return
        self.save_building_summay(os.path.join(path, self.cd['name'] + '_' +\
                                self.component_name.lower().replace(' ','_') + \
                                "_buildings_summary.csv"))
        
    
    def run (self, scalers = {'capital costs':1.0, 'kWh consumption':1.0},
        calc_sqft_only = False):
        """runs the component. The Annual Total Savings,Annual Costs, 
        Annual Net Benefit, NPV Benefits, NPV Costs, NPV Net Benefits, 
        Benefit Cost Ratio, Levelized Cost of Energy, 
        and Internal Rate of Return will all be calculated. There must be a 
        known Heat Recovery project for this component to run.
        
        Parameters
        ----------
        scalers: dictionay of valid scalers, optional
            Scalers to adjust normal run variables. 
            See note on accepted  scalers
        
        Attributes
        ----------
        run : bool
            True in the component runs to completion, False otherwise
        reason : string
            lists reason for failure if run == False
            
        Notes
        -----
            Accepted scalers: capital costs.
        """
        self.run = True
        self.reason = "OK"
        
        tag = self.cd['file id'].split('+')
        if len(tag) > 1 and tag[1] != 'non-residential':
            self.run = False
            self.reason = "Not a non-residential project."
            return 
        
        self.update_num_buildings()
        self.comp_specs['building inventory'] = \
            self.comp_specs['building inventory'].set_index('Building Type')
        self.comp_specs['building inventory'] = \
            self.comp_specs['building inventory'].astype(float)
        self.comp_specs["consumption estimates"] = \
            self.comp_specs["consumption estimates"].astype(float)
        
        
        #~ self.calc_refit_values()
        
        if len(self.comp_specs['building inventory']) == 0:
            self.run = False
            self.reason = "No buildings in community."
            return 
        
        self.calc_total_sqft_to_retrofit()
        
        if calc_sqft_only:
            self.comp_specs['building inventory']['Building Type'] = \
                self.comp_specs['building inventory'].index
            self.comp_specs['building inventory'].index = \
                range(len(self.comp_specs['building inventory']))
            self.comp_specs['building inventory'].index.name = "int_index"
            return
        
        
        self.calc_baseline_kWh_consumption(scalers)
        self.calc_proposed_kWh_consumption()
        
        self.calc_baseline_HF_consumption()
        self.calc_proposed_HF_consumption()
        
        #~ print self.comp_specs['building inventory']
        #~ import sys
        #~ sys.exit()
        #~ self.pre_retrofit_HF_use = np.zeros(self.project_life) + \
                                                    #~ self.baseline_HF_consumption 
                                                    
        
        #~ self.post_retrofit_HF_use = np.zeros(self.project_life) + \
                                                    #~ self.proposed_HF_consumption  
                                                
        #~ years = range(self.start_year,self.end_year)
        #~ self.forecast.add_heating_fuel_column(\
                    #~ "heating_fuel_non-residential_consumed [gallons/year]",
                    #~ years, 
                    #~ self.baseline_HF_consumption * constants.mmbtu_to_gal_HF)
        #~ self.forecast.add_heating_fuel_column(\
                    #~ "heating_fuel_non-residential_consumed [mmbtu/year]", years,
                     #~ self.baseline_HF_consumption)
        
        #~ self.forecast.add_heat_demand_column(\
                    #~ "heat_energy_demand_non-residential [mmbtu/year]",
                 #~ years, self.baseline_HF_consumption)
        
        if self.cd["model financial"]:
            self.get_diesel_prices()
            self.get_electricity_prices() 
            
            self.calc_capital_costs()
            self.calc_annual_electric_savings(scalers)
            self.calc_annual_heating_savings()
            self.calc_annual_total_savings()
            
            self.calc_annual_costs(self.cd['interest rate'],
                                            scalers['capital costs'])
            self.calc_annual_net_benefit()
            
            self.calc_npv(self.cd['discount rate'], self.cd["current year"])
            
            ## no maintaince cost
            self.calc_levelized_costs(0)
            heating_cost_percent = self.comp_specs['heating percent']/100.0
            #scale by heating_cost_percent
            self.break_even_cost *= heating_cost_percent
            
        ## revert building invertory structure
        
        self.comp_specs['building inventory']['Building Type'] = \
            self.comp_specs['building inventory'].index
        self.comp_specs['building inventory'].index = \
            range(len(self.comp_specs['building inventory']))
        self.comp_specs['building inventory'].index.name = "int_index"
        
    def update_num_buildings (self):
        """ This function compares the counted buildings with the estimated 
        buildings
        
        Attributes
        ----------
        num_buildings : int 
            # buildings estimated
        additional_buildings : int 
            difference in estimated buildings as # in iventory
            
        """
        self.num_buildings = self.comp_specs["number buildings"]
        self.additional_buildings = self.comp_specs["number buildings"] - \
                            len(self.comp_specs['building inventory']) 

        if len(self.comp_specs['building inventory']) != \
                self.comp_specs["number buildings"]:
            self.diagnostics.add_note(self.component_name, 
            "# buildings estimated does not match # buildings actual. "+\
            "Estimated: " + str(self.comp_specs["number buildings"]) +\
            ". Actual: " + str(len(self.comp_specs['building inventory']))+ ".")
            
            if len(self.comp_specs['building inventory']) < \
                self.comp_specs["number buildings"]:
                
                self.add_additional_buildings()
            
    def add_additional_buildings (self, num_not_heated = 0):
        """adds additional buildings to the building dataframe 
        (self.comp_specs['building inventory']) if needed.
        
        """
        l = []
        if self.additional_buildings <= num_not_heated:
            self.diagnostics.add_note(self.component_name, 
                            "Not adding additional buildings")
            return
        for i in range(self.additional_buildings - num_not_heated):
            l.append(DataFrame({"Square Feet":np.nan,}, index = ["Average"]))
        self.comp_specs['building inventory'] = \
                                self.comp_specs['building inventory'].append(l)
                                
        ## reindex and add building type
        self.comp_specs['building inventory'].index = \
            range(len(self.comp_specs['building inventory']))
        self.comp_specs['building inventory']['Building Type'] =\
            self.comp_specs['building inventory']\
            ['Building Type'].fillna('Average')
        
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
        """estimates(updates values for each building) building squarefootage 
        were needed, and total calulate retrofit square feet.
          
        Attributes
        ----------
        total_sqft_to_retrofit : float
            sum of all building square footage 
        """
        sqft_ests = self.comp_specs["consumption estimates"]["Sqft"]
        data = self.comp_specs['building inventory']
        
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
        """Calculate the capital costs. Taken as sum of known building refit 
        costs and estimated refit costs (updates values for each building).
            
        Attributes
        ----------
        capital_costs : float
             total cost of improvments ($)
        """
        measure = "implementation cost"
        data = self.comp_specs['building inventory']
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
        """Calculate base line heating fuel consumptions by type from known
        values and estimates(updates values for each building). 
        Estimates are assumed to be from heating oil, except where natural gas
        is used.
        
        Attributes
        ----------
        baseline_HF_consumption : float
            total heating consumption (mmbtu/year)
        baseline_fuel_Hoil_consumption : float
            heaitng oil consumption for heating (gal/year)
        baseline_fuel_hr_consumption : float
            heat recovery consumption for heating (gal/year)
        baseline_fuel_lng_consumption : float
            natural gas consumption for heating (Mcf/year)
        baseline_fuel_propane_consumption : float
            propane consumption for heating (gal/year)
        baseline_fuel_biomass_consumption : float
            biomass consumption for heating (cords/year)
        """
        HDD_ests = self.comp_specs["consumption estimates"]["HDD"]
        gal_sf_ests = self.comp_specs["consumption estimates"]["Gal/sf"]
        
        measure = "Fuel Oil"
        data = self.comp_specs['building inventory']
        keys = data.T.keys()
        keys = set(keys)
        
        data["HDD ESTS"] = 0
        data["GAL/SF"] = 0
        for key in keys:
            try:
                data["HDD ESTS"].ix[key] = \
                    self.cd["heating degree days"]/HDD_ests[key]
                data["GAL/SF"].ix[key] = gal_sf_ests.ix[key] 
            except KeyError:
                data["HDD ESTS"].ix[key] = \
                    self.cd["heating degree days"]/HDD_ests.ix['Other']#unitless
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

            
        
    def calc_baseline_kWh_consumption (self, scalers):
        """calculate baseline electricity use from all buildings in community
        (or intertie) from measured values and 
        estimates(updates values for each building)
        
        Attributes
        ----------
        baseline_kWh_consumption : float
            baseline electricity consumption (kWh/year). 
        """
        kwh_sf_ests = self.comp_specs["consumption estimates"]["kWh/sf"]
        
        measure = "Electric"
        data = self.comp_specs['building inventory']
        keys = data.T.keys()
        local_inv = data[["Square Feet", measure]].T.values.tolist()
        local_inv.insert(0,keys.values.tolist())
        local_inv = np.array(local_inv).T
        inv = local_inv


        if not self.intertie_data is None:
            #~ print 'Loading intertie' 
            intertie_component = CommunityBuildings(
                self.intertie_data,
                self.forecast, 
                self.diagnostics,
                scalers
            )
            intertie_component.run(calc_sqft_only = True)
            
            it_inv = intertie_component.comp_specs['building inventory']
            keys = it_inv['Building Type'].values
    
            it_inv = it_inv[["Square Feet", measure]].T.values.tolist()
            it_inv.insert(0,keys)
            it_inv = np.array(it_inv).T
            kwh_sf_ests = \
                intertie_component.comp_specs['consumption estimates']["kWh/sf"]
            
            inv = it_inv

        #~ print inv
        keys = set(keys)
        keys.add('Average')
        
        kwh_buildings = deepcopy(local_inv)

        for k in keys:
            try:
                kwh_sf = kwh_sf_ests.ix[k] # (kWh)/sqft
            except KeyError:
                #~ print 'KeyError', k
                kwh_sf = kwh_sf_ests.ix['Other'] # (kwh)/sqft
            
            idx = np.logical_and(local_inv[:,0] == k, 
                                np.isnan(local_inv[:,2].astype(float)))
            sqft = local_inv[idx, 1].astype(np.float64) #sqft
            local_inv[idx, 2] = sqft * kwh_sf # kWh
        
        ## *** possibly could be done better, but is fine    
        if not self.intertie_data is None:
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
        ### end ***

        
        estimated_total = inv[:,2].astype(np.float64).sum()
        # Trend total
        try:
            if self.intertie_data is None:
                forecast = self.forecast.consumption
            else:
                forecast = Forecast(
                    self.intertie_data,
                    self.diagnostics,
                    scalers
                ).consumption
            fc_total = \
                forecast.ix[self.start_year]['consumption non-residential']
            #~ print forecast
        except AttributeError:
            fc_total = estimated_total
        
        #~ print fc_total, estimated_total
        ratio = fc_total/estimated_total
        #~ print ratio
        #~ print ratio
        #~ print kwh_buildings
        # step 1 & 2: loop if consumption known use; other wise scale:
        for idx in range(len(kwh_buildings)):
            if np.isnan(kwh_buildings[idx, 2].astype(float)):
                kwh_buildings[idx, 2] = ratio * local_inv[idx, 2].astype(float)
                
                
        #~ print kwh_buildings
        data[measure] =  kwh_buildings[:,2].astype(np.float64)  
        self.baseline_kWh_consumption = data[measure].sum()
        
    def calc_proposed_HF_consumption (self):
        """Calculate proposed HF  consumption from known values and 
        estimates(updates values for each building)
        
        Attributes
        ----------
        proposed_HF_consumption : float
            total heating consumption (mmbtu/year)
        proposed_fuel_Hoil_consumption : float
            heaitng oil consumption for heating (gal/year)
        proposed_fuel_hr_consumption : float
            heat recovery consumption for heating (gal/year)
        proposed_fuel_lng_consumption : float
            natural gas consumption for heating (Mcf/year)
        proposed_fuel_propane_consumption : float
            propane consumption for heating (gal/year)
        proposed_fuel_biomass_consumption : float
            biomass consumption for heating (cords/year)
        """
        building_data = self.comp_specs['building inventory']
        percent_savings = self.comp_specs['cohort savings percent'] / 100.0
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
            
            
            
            #~ self.comp_specs['building inventory']["Fuel Oil Post"] = \
                        #~ self.comp_specs['building inventory']["Fuel Oil"]*\
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
        """Calculate proposed electric  consumption from known values and 
        estimates(updates values for each building)
        
        Attributes
        ----------
        proposed_kWh_consumption : float
            (kWh/year)
        """
        building_data = self.comp_specs['building inventory']
        percent_savings = self.comp_specs['cohort savings percent'] / 100.0
    
        elec_vals = building_data['Electric Post']
        idx = elec_vals.isnull()
        elec_vals[idx] = building_data['Electric'][idx] * (1 - percent_savings)
        
        #kWh
        
        self.proposed_kWh_consumption = elec_vals.sum()
                                                
    def get_fuel_total_saved (self):
        """get total fuel saved
        
        Returns 
        -------
        float
            the total fuel saved in gallons
        """
        #~ gen_eff = self.cd["diesel generation efficiency"]
        
        HF_savings = \
            (self.baseline_HF_consumption - self.proposed_HF_consumption) *\
            constants.mmbtu_to_gal_HF
        return HF_savings #+ \
                #~ self.refit_savings_kWh_total / gen_eff
                                
    def get_total_enery_produced (self):
        """get total energy produced
        
        Returns
        ------- 
        dict
            electric 'kWh', and heating 'MMBtu' savings keys with tuple 
        (savings, % of energy used) values
        """
        kWh_savings = self.baseline_kWh_consumption - \
                        self.proposed_kWh_consumption
        HF_savings = self.baseline_HF_consumption - \
                        self.proposed_HF_consumption
        heating_cost_percent = self.comp_specs['heating percent'] / 100.0
        return {'kWh': (kWh_savings, 1 - heating_cost_percent), 
                'MMBtu': (HF_savings, heating_cost_percent)
               }
    
    def calc_annual_electric_savings (self, scalers):
        """calculate annual electric savings created by the project
            
        Attributes
        ----------
        baseline_kWh_cost : np.array
            baseline cost ($/year)
        proposed_kWh_cost : np.array
            proposed cost ($/year)
        annual_electric_savings : np.array
            electric savings ($/year) are the difference in the base 
        and proposed fuel costs
        """
        elec_price = self.electricity_prices
        if not self.intertie_data is None:
            #~ print 'Loading intertie' 
            intertie_component = CommunityBuildings(
                self.intertie_data,
                self.forecast, 
                self.diagnostics,
                scalers
            )
            intertie_component.get_electricity_prices()
            elec_price = intertie_component.electricity_prices
        self.elec_price = elec_price

        #~ print self.elec_price
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
        """calculate annual heating savings created by the project
            
        Attributes
        ----------
        baseline_HF_cost : np.array
            baseline heating cost ($/year)
        proposed_HF_cost : np.array
            proposed heating cost ($/year)
        annual_heating_savings : np.array
            heating savings ($/year) 
        """
        self.hoil_price = (self.diesel_prices + self.cd['heating fuel premium'])
        #~ print self.hoil_price
        hr_price = self.hoil_price * \
            (self.comp_specs['waste oil cost percent'] / 100.0)
        
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
        
        #~ print self.baseline_HF_cost,  self.proposed_HF_cost
        self.annual_heating_savings = self.baseline_HF_cost - \
                                            self.proposed_HF_cost
        
    
