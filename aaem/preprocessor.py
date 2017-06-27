"""
preprocessor
------------

process data into a format for the model to use
"""
from pandas import DataFrame,read_csv, concat
import shutil
import os.path
from diagnostics import Diagnostics
import numpy as np
#~ from forecast import growth
from datetime import datetime
from collections import Counter
from importlib import import_module
import copy

import yaml


from aaem.components import comp_lib, comp_order
import aaem.yaml_dataframe as yd
import aaem.constants as constants
from aaem.config_IO import save_config
from aaem.defaults import base_order

GENERATION_AVG = .03


from config_IO import merge_configs

class PreprocessorError(Exception):
    def __init__(self, value):
         self.value = value
    def __str__(self):
        return repr(self.value)




def growth(xs, ys , x):
    """
    growth function

    pre:
        xs,ys are arrays of known x and y values. x is a scaler or np.array
    of values to calculate new y values for

    post:
        return new y values
    """
    xs = np.array(xs)
    ys = np.log(np.array(ys))

    xy_bar = np.average(xs*ys)
    x_bar = np.average(xs)
    y_bar = np.average(ys)
    x_sq_bar = np.average(xs**2)

    beta = (xy_bar - x_bar*y_bar)/(x_sq_bar- x_bar**2)
    alpha = y_bar - beta* x_bar
    return np.exp(alpha  + beta * x)


class Preprocessor (object):
    """
    """
    def __init__ (self, community, data_dir, diag = None, 
        process_intertie = False):
        """
        
        note on intertie_status and community, GNIS, etc attributes
        if intertie_status == 'not in intertie'
            the ID attributes are each a list with the value for the community
            i.e. for Adak community = ['Adak']
        if intertie_status == 'parent'
            the ID attributes are a list of Parent, child, ..,  child
            i.e. for bethel community = ['Bethel', 'Oscarville', 'Napakiak']
        if intertie_status == 'child'
            the ID attributes are a list of
            Parent, Current child, other child,...,other child
            i.e. for Oscarville community = ['Bethel', 'Oscarville', 'Napakiak']
            i.e. for Napakiak community = ['Bethel', 'Napakiak', 'Oscarville']
        
        """
        self.community = community # community of interest
        if diag == None:
            diag = Diagnostics()
        self.diagnostics = diag
        self.data_dir = os.path.join(os.path.abspath(data_dir),"")


        self.intertie_status = self.detrmine_intertie_status(community)
        
        if process_intertie == True and self.intertie_status != 'parent':
            raise PreprocessorError, \
                "Cannot Preprocess as interite not a parent"
            
        self.process_intertie = process_intertie
        
        if self.intertie_status == "not in intertie":
            self.intertie = [community]
        else:
            self.intertie = self.get_all_intertie_communties(
                community
            )

        ## all communities on the interties to make loading more standard
        self.communities, self.regions ,self.GNIS_ids, self.FIPS_ids, \
            self.aliases = self.load_ids(self.intertie)
        self.data = {}
        self.projects = {}
        
    def run (self, **kwargs):
        """Run the preprocessor
        
        """
        if 'show' in kwargs and kwargs['show'] == True:
            print self.community, 'Intertie' if self.process_intertie else ''
        
        data = self.load_pce()
        if len(data) == 0:
            data = self.load_eia()
            #~ print data
            if len(data[0]) == 0 and len(data[1]) == 0:
                source = 'none'
            elif len(data[0]) == 0 and len(data[1]) != 0:
                source = 'eia-sales-only'
                self.diagnostics.add_note('Generation Data',
                    "Using Generation data in EIA data, sales only"
                )
            else:
                source = 'eia'
                self.diagnostics.add_note('Generation Data',
                    "Using Generation data in EIA data"
                )
        else:
            source = 'pce'
            self.diagnostics.add_note('Generation Data',
                "Using Generation data in PCE data"
            )
            
        ## need to fix Valdez
        if self.community == 'Valdez':
            source = 'none'
        ## try paret if source is none and a child
        if source == 'none':
            # TODO, do i use parent or all interttie ?
            ids_to_use = [self.communities[0],self.aliases[0]]
            data = self.load_pce(ids_to_use=ids_to_use) 
            if len(data) == 0:
                data = self.load_eia(ids_to_use=ids_to_use)
                if len(data[0]) == 0 and len(data[1]) == 0:
                    #~ print "No generation data found"
                    source = 'none'
                    #~ raise PreprocessorError, "No generation data found"
                elif len(data[0]) == 0 and len(data[1]) != 0:
                    source = 'eia-sales-only'
                    self.diagnostics.add_note('Generation Data',
                        "Using Generation data in EIA data, sales only"
                    )
                else:
                    source = 'eia'
                    self.diagnostics.add_note('Generation Data',
                        "Using Generation data in EIA data"
                    )
            else:
                source = 'pce'
                self.diagnostics.add_note('Generation Data',
                    "Using Generation data in PCE data"
                )
            #~ print "ids used", ids_to_use
        
        #~ print source
        if source == 'pce':
            generation_data = self.process_generation(pce_data = data) 
            sales_data = self.process_prices(pce_data = data) 
        elif source == 'eia': # 'eia'
            generation_data = self.process_generation(
                eia_generation = data[0],
                eia_sales = data[1],
            ) 
            sales_data = self.process_prices(
                eia_sales = data[1],
            ) 
        elif source == 'eia-sales-only':
            generation_data = self.process_generation(
                eia_sales = data[1],
            ) 
            sales_data = self.process_prices(
                eia_sales = data[1],
            ) 
        elif source == 'none':
            generation_data = self.process_generation()
            sales_data = self.process_prices()
        else:
            raise PreprocessorError, "serious Issues"
        
        #~ print len(generation_data)
        #~ print sales_data
        self.data = merge_configs(self.data, self.create_community_section())
        #~ self.data = merge_configs(self.data, self.create_forecast_section())
        self.data = merge_configs(self.data, generation_data)
        self.data = merge_configs(self.data, sales_data)
        self.data = merge_configs(self.data, 
            self.process_diesel_powerhouse_data() )
            
        self.data = merge_configs(self.data,
            self.load_measured_heating_fuel_prices())
            
        ## caclulate 'electric non-fuel prices'
        if not source == 'none':
            efficiency = self.data['community']['diesel generation efficiency']
            #~ print efficiency
            percent_diesel = \
                self.data['community']['utility info']['generation diesel']\
                .fillna(0)\
                /self.data['community']['utility info']['net generation']
            #~ print self.data['community']['utility info'][['generation diesel', 'net generation']]
            percent_diesel = float(percent_diesel.iloc[-1])
            #~ print percent_diesel
            #~ print self.data['community']['diesel prices'].iloc[0]
            adder = percent_diesel * \
                self.data['community']['diesel prices'] / efficiency
            adder = adder.fillna(0)
            
            #~ print self.data['community']['electric non-fuel price'] 
            self.data['community']['electric non-fuel prices'] = \
                self.data['community']['electric non-fuel price'] + adder
          
        else:
            percent_diesel = 0
            self.data['community']['electric non-fuel prices'] = \
                self.data['community']['electric non-fuel price'] + \
                (self.data['community']['diesel prices'] * percent_diesel)
            
        if self.data['community']["region"] == "North Slope":
            N_slope_price = .15
            self.data['community']['electric non-fuel prices'] = \
                (self.data['community']['electric non-fuel prices'] * 0) +\
                 N_slope_price
        
        self.data = merge_configs(self.data,
            {'community': {'percent diesel generation': percent_diesel * 100}})
            
            
        for comp in comp_lib:
            #~ print comp
            module = self.import_component(comp_lib[comp])
            
            data = self.preprocess_component(module.preprocessing, **kwargs)
            #~ print data
            if len(data) == 1:
                try:
                    data = data['no project']
                except KeyError:
                    pass
                self.data = merge_configs(self.data, data)
                
            else:
                self.data = merge_configs(self.data, data['no project'])
                del data['no project']
                self.projects.update( data )
            #~ del data
            
        if 'ng_com' in kwargs and kwargs['ng_com']:
            self.data['community']['natural gas price'] = 3.0
            self.data['community']['natural gas used'] = True
            
    def save_config (self, out_dir, keys_to_split = {}):
        """Save the configuration yaml file
        
        parameters
        ----------
        out_dir: path
            path to directory to save the config in 
        keys_to_split: dict of lists
            sections and thier keys to split
        """
        if len(self.projects) == 0:
            self.save_single(out_dir, keys_to_split )
        else:
            self.save_projects(out_dir, keys_to_split )
            
    def save_projects (self, out_dir, keys_to_split  ={}):
        """Save the configuration yaml file for each project
        
        parameters
        ----------
        out_dir: path
            path to directory to save the config in 
        keys_to_split: dict of lists
            sections and thier keys to split
        """
        original_tag = self.data['community']['file id']
        self.save_single(out_dir, keys_to_split )
        my_copy = copy.deepcopy(self.data)
        for project in self.projects:
            self.data['community']['file id'] = original_tag + '+' + project
            #~ print self.projects[project]
            self.data = merge_configs(self.data, self.projects[project])
            self.save_single(out_dir, keys_to_split)
        
        self.data = my_copy
        #~ self.data['community']['file id'] = original_tag
        
    def split_config(self, keys):
        """split confing into to, usefull for creating global config
        
        parameters
        ----------
        keys: dict of lists
            sections and thier keys to split
        """
        with_keys = {}
        without_keys = {}
        
        
        for section in keys:
            with_keys[section] = {}
            for item in keys[section]:
                with_keys[section][item] = self.data[section][item]
        
        for section in self.data:
            without_keys[section] = {}
            
            try:
                community_keys = \
                    set(self.data[section].keys()) ^ set(keys[section])
            except KeyError:
                community_keys = self.data[section].keys()
            for item in community_keys:
                without_keys[section][item] = self.data[section][item]
                
                
        return with_keys, without_keys
        
    def save_global_congfig(self, f_name, keys_to_split={}):
        """Save the global configuration yaml file
        
        parameters
        ----------
        f_name: path
            path to save file with
        keys_to_split: dict of lists
            sections and thier keys to split
        """
        gc, data = self.split_config(keys_to_split)
        
        s_order = ['community'] + comp_order
        i_order = {'community': base_order}
        comments = {}
        for comp in comp_lib:
            module = self.import_component(comp_lib[comp])
            i_order[comp] = module.config.order
            comments[comp] = module.config.comments

        save_config(f_name,
            gc,
            comments = comments,
            s_order = s_order,
            i_orders = i_order,
            header = ''
        )
        
        
    def save_single (self, out_dir, keys_to_split={}):
        """Save the configuration yaml file
        
        parameters
        ----------
        out_dir: path
            path to directory to save the config in 
        keys_to_split: dict of lists
            sections and thier keys to split
        """
        community = self.data['community']['file id']\
            .replace(' ', '_').replace("'", '')
        #~ if self.process_intertie == True:
            #~ community += '_intertie'
            
        s_order = ['community'] + comp_order
        i_order = {'community': base_order}
        comments = {}
        for comp in comp_lib:
            module = self.import_component(comp_lib[comp])
            i_order[comp] = module.config.order
            comments[comp] = module.config.comments
        
        gc, data = self.split_config(keys_to_split)
        
        out_path = os.path.join(out_dir, community+'.yaml')
        save_config(out_path,
            data,
            comments = comments,
            s_order = s_order,
            i_orders = i_order,
            header = ''
        )

    def import_component(self, component):
        """import a component
        
        Parameters
        ----------
        component: str
            name of the component
        
        Returns
        -------
        an AAEM component
        """
        try:
            return self.components_modules[component]
        except AttributeError:
            self.components_modules = {}
        except KeyError:
            pass
        
        #~ print component
        #~ print 'aaem.components.' + component
        self.components_modules[component] = \
            import_module('aaem.components.' + component)
        return self.components_modules[component]
        
    def preprocess_component ( self, component, **kwargs):
        """Run the prerocess function for a component
        
        Parameters
        ----------
        component: a components preprocessing submodule
            
        Returns
        -------
        data: dict
            the preprocessed data
        """
        data = component.preprocess(self, **kwargs)
        return data
        
        
    def load_ids (self, communities):
        """get a communities id information from "community_list.csv"
        
        Parameters
        ----------
        communities: list of str
            communities to load ids for
            
        Returns
        -------
        ids: list of str
            primary ids (community names)
        regions: list of str
            energy regions 
        gins_ids: list of int
            GNIS ids
        fips_ids: list of int
            FIPS ids
        aliases: list of str
            any other names for communities
        """
        datafile = os.path.join(self.data_dir, "community_list.csv")
        data = read_csv(datafile, comment = '#')
        id_cols = [c for c in data.columns if c != 'Energy Region']
        ids = data[data[id_cols].isin(self.intertie).any(axis=1)]
        if len(ids) != len(communities):
            #~ print ids, communities
            raise PreprocessorError, "Could not find community ID info"
        ids = ids.set_index('Community').ix[self.intertie]
        return list(ids.index), \
            list(ids['Energy Region'].values), \
            list(ids['GNIS'].values), \
            list(ids['FIPS'].values), \
            [str(i).replace('nan','') for i in ids['Alias'].values] 
            
    def detrmine_intertie_status (self, community):
        """detrmine if commiunity is parent, child, or not in intertie
        
        Parameters
        ----------
        community: str
            the community of interest
        
        Returns
        -------
        status: str
            the status of the intertie 'parent', 'child', or 'not in intertie'
        """
        ## load file
        datafile = os.path.join(self.data_dir,"current_interties.csv")
        data = read_csv(datafile, index_col=0, comment = "#").fillna("''")
        
        ### TODO: figure this out
        if community in ['Klukwan']:
            return "not in intertie"
        
        ## is community a parent
        if community in data.index: 
            plant = data.ix[community]['Plant Intertied']
            other_communities = data.ix[community]['Other Community on Intertie']
            if plant.lower()  == 'yes' and other_communities != "''":
                status = "parent"
            else: 
                # if 'Plant Intertied' not yes or no communities listed
                # in interite, community is not part of intertie
                status = "not in intertie"
        ## is it a child
        elif (data == community).any().any():
            status = 'child'
        else:
            status = "not in intertie"
        return status
    
    def get_all_intertie_communties (self, community):
        """get all communities in the intertie
        
        Parameters
        ----------
        community: str
            the community of interest
        
        Returns
        -------
        list:
            list of the intertied communities. Format will be
            [parent, child 1, ... , child n] where the community of 
            intrest is either the parent or child 1 if the community is 
            the parent or a child in the community respectably
        """
        ## load file
        datafile = os.path.join(self.data_dir,"current_interties.csv")
        data = read_csv(datafile, index_col=0, comment = "#").fillna("''")
        
        ## community is parent
        if community in data.index: 
            intertie = [community] +\
                list(data.ix[community].drop('Plant Intertied'))
            intertie = [c for c in intertie  if c != "''"]
        ## community is child
        else:
            children = data.ix[data.index[data.T[data.T==community].any()]]
            parent = children.index[0]
            children = children.drop('Plant Intertied', axis = 1)
            children = list(children.values.flatten())
            children = [ community ] + [ c for c in children if c != community]
            intertie = [ parent ] + [c for c in children  if c != "''"]
        return intertie
            
    def create_community_section (self, **kwargs):
        """create community section
        
        Returns
        -------
        dict: 
            the community section of a confinguration object
        """
        senate, house = self.load_election_divisions()
        
        if self.intertie_status != "not in intertie":
            intertie = self.communities 
        else:
            intertie = "not in intertie"
        
        population = self.load_population(**kwargs)
        
        c_goals, r_goals = self.load_goals()
        data = {
            'community': {
                'model electricity': True,
                'model heating fuel': True,
                'model financial': True,
                'model as intertie': self.process_intertie,
                'file id': self.community.replace(' ','_'),
                'natural gas used': False,
                'current year': 2016,
                
                'name': self.community,
                'alternate name': self.aliases[0],
                'region': self.regions[0],
                'regional construction multiplier':
                     self.load_construction_multiplier(),
                'GNIS ID': self.GNIS_ids[0],
                'FIPS ID': self.FIPS_ids[0],
                'intertie': intertie,
                'senate district': senate,
                'house district': house,
                'community goals': c_goals, 
                'regional goals': r_goals,
                
                'population':population,
                
                'interest rate': .05 * 100,
                'discount rate': .03 * 100,
                
                'heating degree days': self.load_heating_degree_days(),
                'heating fuel premium': self.load_heating_fuel_premium(),
                'on road system': self.load_road_system_status(),
                
                'max wind generation percent': 20,
                
                'percent excess energy': 15,
                'percent excess energy capturable': 70,
                'efficiency electric boiler': 0.99,
                'efficiency heating oil boiler': 0.8,
                
                'diesel generator o&m cost percent': 2,
                'switchgear cost': 150000,
                
                'assumed percent non-residential sqft heat displacement': 30,
                'heating oil efficiency': 0.75, # % as decimal <float>
                
            },
        }
        
        if self.process_intertie == True:
            data['community']['file id'] += '_intertie'
        
        data = merge_configs(data, self.process_renewable_capacities())
        return data
        
        
    def load_population (self, **kwargs):
        """load population for the community
        
        Parameters
        ----------
        population_threshold: int, optional, default 20
            lower limit on population, a warning will be logged if 
            any population values fall below this
        start_year: int, otional, default 2003
            the first year to load from population data. 
        max_population_change: float otional, default .02
            the percent as a decimal that gives the max chage in population 
            that can occur with out a warning being issued
            
            
        Returns
        -------
        population: DataFrame
            the population in the community from start_year to the end of the
            forecast
        
        """
        datafile = os.path.join(self.data_dir, "population_projections.csv")
        ## process kwargs
        threshold = kwargs['population_threshold'] \
            if 'population_threshold' in kwargs else 20
        ## TODO: Needs better mor unique name
        start_year = kwargs['start_year'] if 'start_year' in kwargs else 2003
        #change to support 1 as one percent as opposed to .01
        percent = kwargs['max_population_change'] if \
            'max_population_change' in kwargs else .02
        
        ids = self.GNIS_ids
        
        get_it_ids = kwargs['get_it_ids'] if 'get_it_ids' in kwargs else False
        
        if not get_it_ids:
            if not self.process_intertie:
                if self.intertie_status == 'child':
                    ids = [ids[1]]
                else:
                    ids = [ids[0]]
            
            
        if 'population_ids_to_use' in kwargs:
            ids = kwargs['population_ids_to_use']
       
        ## load data & remove name of town
        pops = read_csv(datafile, index_col = 1)
        pops = pops.ix[ids].drop('place_name', axis = 1).sum()
    
        ## set index to integers
        pops.index = pops.index.astype(int)

        ## interpolate missing values
        if pops[ pops.isnull()].size != 0:
            self.diagnostics.add_warning("Forecast: Population",
                "Missing values were found, interpolation may occur")
        
            pops = pops.interpolate()
        
        ## convert to dataframe & format
        pops = DataFrame(pops.ix[2003:])
        pops.columns  = ["population"]
        ## check threshold
        if (pops.values < threshold).any():
            self.diagnostics.add_warning("Forecast: Population",
                "less than threshold (" + str(threshold) + ")")
        
        ## check change between years
        for year in pops.index[1:-1]:
            current = pops['population'].ix[year]
            previous = pops['population'].ix[year - 1]
            hi = previous * (1.0 + percent)
            lo = previous * (1.0 - percent)
            if (current > hi or current < lo):
                self.diagnostics.add_note("Forecast: Population",
                    "population changes more than " + str(percent * 100) +\
                    "% from " + str(previous) + " to " + str(current)
                )
                
        ## all data is from input 
        pops["population_qualifier"] = 'I'
        
        pops.index.name = 'year'
        
        return pops
        
    def load_pce (self, **kwargs):
        """load PCE data
        
        Parameters
        ----------
        ids_to_use
        
        Returns
        -------
        pce_data: DataFrame
            the PCE Data for the community (or intertie if 
            process_intertie is True)
        """
        ###
        datafile = os.path.join(self.data_dir, 
            "power-cost-equalization-pce-data.csv")
        data = read_csv(datafile, index_col=1, comment = "#")
        ## clean up index
        data.index = [i.split(',')[0] for i in data.index]
        
        ## get ids
        if "ids_to_use" in kwargs:
            ids = kwargs["ids_to_use"]
        else:
            ids = self.communities + self.aliases
            #~ print ids
            if not self.process_intertie:
                ## parent community or only community 
                if self.intertie_status in ['not in intertie']:
                    ids = [self.communities[0], self.aliases[0]]
                #~ else:
                    #~ ## name and ailias of first child (community of interest)
                    #~ ids = [self.communities[1], self.aliases[1]]
        ## cleanup ids
        ids = [i for i in ids if i != ""]
        ## Klukwan fix - see not at top of function
        if 'Klukwan' in ids:
            ids += ["Chilkat Valley"]   
            
        ## dumb 'Iliamna, Newhalen, Nondalton' workaround
        if 'Newhalen' in ids and not "Iliamna" in ids:
            ids += ["Iliamna"]
        
        ## get data
        data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
        
        # filter out 'Purchased Power' from child communities as they
        # buy it from the parent so its counted there
        if self.intertie_status in ['parent', 'child'] :
            children = self.communities[1:] +  self.aliases[1:]
            for child in children:
                try: 
                    data['kwh_purchased'].ix[[child]] = 0
                except KeyError:
                    pass # no data for child
        
        return data
        
    def helper_pce_prices (self, pce_data, **kwargs):
        """process the PCE electric prices
        
        Parameters
        ----------
        pce_data: DataFrame
            the pce data to process prices for
            
        Returns
        -------
        res_nonPCE_price: float
            residential Non pce electric price
        elec_nonFuel_cost : float
            electric non fuel cost
        """
        ## get_columns
        data = pce_data[[
            "year","month","residential_rate",
            "pce_rate","effective_rate","residential_kwh_sold",
            "commercial_kwh_sold",
            "community_kwh_sold",
            "government_kwh_sold",
            "unbilled_kwh", "fuel_cost"
        ]]
        coms = list(set(data.index))
        #~ print len(data)
        ## get last year with full data
        last_year = data["year"].max()
        while len(data[data["year"] == last_year])%12 != 0:
            last_year -= 1
        
        ## get last years electric fuel cost
        cols = [
            "residential_kwh_sold", "commercial_kwh_sold", 
            "community_kwh_sold", "government_kwh_sold", "unbilled_kwh"
        ]
        
        elec_fuel_cost = 0
        res_nonPCE_price = 0
        total_sold = data[data["year"] == last_year][cols].sum(axis = 1).mean()
        
        #~ print (data[data["year"] == last_year]['fuel_cost']/\
                #~ data[data["year"] == last_year][cols].sum(axis = 1)).mean()
        
        for com in  coms:
            #~ print data[data["year"] == last_year].ix[com]['fuel_cost']
            #~ print data[data["year"] == last_year].ix[com][cols].sum(axis = 1)
            
            com_elec_fuel_cost = (
                data[data["year"] == last_year].ix[com]['fuel_cost'].fillna(0)/\
                data[data["year"] == last_year].ix[com][cols].sum(axis = 1)
            ).mean()
            weight = \
                data[data["year"] == last_year].\
                ix[com][cols].sum(axis = 1).mean()/\
                total_sold
            elec_fuel_cost += (com_elec_fuel_cost * weight)
            
            res_pce = \
                data[data["year"] == last_year].ix[com]\
                ["residential_rate"].mean()
        
            res_nonPCE_price += (res_pce * weight)
        
        #~ print elec_fuel_cost
        
        if np.isnan(elec_fuel_cost):
            elec_fuel_cost = 0.0
            self.diagnostics.add_note("Community: Electric Prices(PCE)",
                "electric fuel price not available, seting to 0")
                
        res_nonPCE_price = data[data["year"] == \
                                last_year]["residential_rate"].mean()
        
                                
        elec_nonFuel_cost = res_nonPCE_price - elec_fuel_cost
        
        self.diagnostics.add_note("Community: Electric Prices(PCE)",
            "calculated res non-PCE elec cost: " + str(res_nonPCE_price))
        self.diagnostics.add_note("Community: Electric Prices(PCE)",
            "calculated elec non-fuel cost: " + str(elec_nonFuel_cost))
            
        return res_nonPCE_price, elec_nonFuel_cost 
    
    def load_purchased_power_lib (self, **kwargs):
        """load pruchaced power lib for pce data
        
        Returns
        -------
        dict:
            dictionary of utilities and the type of generation they supply
        """
        ## get ids
        ids = self.communities + self.aliases
        #~ if not self.process_intertie:
            #~ ids = [self.communities[0], self.aliases[0]]
        ids = [i for i in ids if i != ""]
        
        ## TODO: weird
        if 'Klukwan' in ids:
            ids += ["Chilkat Valley"]
            
        ## setup data
        datafile = os.path.join(self.data_dir, "purchased_power_lib.csv")
        data = read_csv(datafile, index_col=0, comment = '#')
        data.index = [i.split(',')[0] for i in data.index] # reindex
        data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
        data= data.set_index('purchased_from')
        
        ### create purchased power lib
        lib = {}
        for utility in set(data.index):
            source = data.ix[utility]['Energy Source']
            if not type(source) is str:
                if 1 != len(set(data.ix[utility]['Energy Source'].values)):
                    self.diagnostics.add_warning('PCE preprocessing',
                        "More Than One Energy Source in Purcased power lib, " +\
                        "defaulting to first in list alphabeticaly"
                    )
                    source = sorted(data.ix[utility]['Energy Source'].values)[0]    
                    
                else:
                    source = data.ix[utility]['Energy Source'].values[0]
            
            lib[utility] = source
            
        return lib
    
    def helper_pce_generation (self, pce_data, **kwargs):
        """process PCE data into a dataframe with yearly data for:
        "generation", "consumption", "fuel used", "efficiency", "line loss",
        "net generation", "consumption residential",
        "consumption non-residential", "kwh_purchased", "residential_rate",
        "diesel_price", "generation diesel", "generation hydro",
        "generation natural gas", "generation wind", "generation solar",
        "generation biomass"
        
        Parameters
        ----------
        pce_data: DataFrame
            data as loaded from the PCE data file
        power_house_consumption_percent: float
            a percentage > 0 of the gross generation used by power house
            
        Returns 
        -------
        DataFrame
            yearly electic data for pce
        """
        ### read kwargs
        phc_percent = kwargs['power_house_consumption_percent']/ 100 if \
            'power_house_consumption_percent' in kwargs else .03
        
        data = pce_data[[
            "year","month","diesel_kwh_generated", "powerhouse_consumption_kwh",
            "hydro_kwh_generated", "other_1_kwh_generated", "other_1_kwh_type",
            "other_2_kwh_generated", "other_2_kwh_type", 'purchased_from',
            'kwh_purchased', "fuel_used_gal", "residential_kwh_sold",
            "commercial_kwh_sold", "community_kwh_sold", "government_kwh_sold",
            "unbilled_kwh", "residential_rate", "fuel_price"
        ]]
        
        ## check purchased power
        purchased_power_lib = self.load_purchased_power_lib()
        if len (purchased_power_lib) == 0 :
            purchase_type = None
        elif len(set(purchased_power_lib.values())) == 1:
            purchase_type = set(purchased_power_lib.values()).pop().lower()
            self.diagnostics.add_note("Community: generation(PCE)",
                "All utilities power is purchased from provided " +\
                 purchase_type + " Power"
            )
        else:
            if 'hydro' in set(purchased_power_lib.values()):
                purchase_type = 'hydro'
                self.diagnostics.add_note("Community: generation(PCE)",
                    "Hydro is a type of power utilities  purchase from" +\
                    " provider, so it is assumed hydro is the main type"
                )
            else:
                purchase_type = set(purchased_power_lib.values()).pop().lower()
                self.diagnostics.add_note("Community: generation(PCE)",
                    "Guessing main purchase type as " + purchase_type
                )

        ### check other sources 1
        other_sources_1 = sorted(
            data[data['other_1_kwh_type'].notnull()]["other_1_kwh_type"].values
        )

        if len(other_sources_1) == 0 :
            other_type_1 = None
        else: 
            other_type_1, count = Counter(other_sources_1).most_common(1)[0]
            other_type_1 = other_type_1.lower()
            self.diagnostics.add_note("Community: generation(PCE)",
                "Other energy type no. 1 is being set as " + other_type_1 +\
                " as it occured most as the type for other generatio no. 1 (" +
                str(count) + " out of "+ str(len(other_sources_1)) + " times."
            )
            
            if other_type_1 not in ('diesel', 'natural gas','wind', 'solar'):
                other_type_1 = None
                self.diagnostics.add_warning("Community: generation(PCE)",
                    ("Other energy type no. 1 is being set as None because "
                    "povided type is not 'diesel', 'natural gas', "
                    "'wind', or 'solar'.")
                )
                
        ### check other sources 2
        other_sources_2 = sorted(
            data[data['other_2_kwh_type'].notnull()]["other_2_kwh_type"].values
        )

        if len(other_sources_2) == 0 :
            other_type_2 = None
        else: 
            other_type_2, count = Counter(other_sources_2).most_common(1)[0]
            try:
                other_type_2 = other_type_2.lower()
            except AttributeError:
                other_type_2 = ''
            self.diagnostics.add_note("Community: generation(PCE)",
                "Other energy type no. 2 is being set as " + other_type_2 +\
                " as it occured most as the type for other generatio no. 2 (" +
                str(count) + " out of "+ str(len(other_sources_2)) + " times."
            )
            
            if other_type_2 not in ('diesel', 'natural gas','wind', 'solar'):
                other_type_2 = None
                self.diagnostics.add_warning("Community: generation(PCE)",
                    ("Other energy type no. 2 is being set as None because "
                    "povided type is not 'diesel', 'natural gas', "
                    "'wind', or 'solar'.")
                )
        #~ print purchase_type, other_type_1, other_type_2 
        ## reindex by year
        data = data.set_index('year')
        data_by_year = []
        ## merge each year 
        for year in data.index.unique():
            ## make sure every month is present in the year
            if set(data.ix[year]['month'].values) != set(range(1,13)):
                #~ print year
                continue
                
            ## set up current years data
            years_data = data.ix[year].sum()
            years_data['year'] = year
            years_data = years_data.fillna(0)
            
            years_data['residential rate'] = \
                data.ix[year]['residential_rate'].mean()
            years_data["diesel price"] = data.ix[year]["fuel_price"].mean()
                
            years_data["kwh purchased"] = years_data["kwh_purchased"]
            
            
            ## add total generation
            years_data['generation'] = years_data[['diesel_kwh_generated',
                "powerhouse_consumption_kwh", "hydro_kwh_generated",
                "other_1_kwh_generated", "other_2_kwh_generated",
                "kwh_purchased"]].sum()
                
            # add generation from diesel, hydro, etc
            years_data['generation diesel'] = years_data['diesel_kwh_generated']
            years_data['generation hydro'] = years_data['hydro_kwh_generated']
            years_data['generation solar'] = 0
            years_data['generation wind'] = 0
            years_data['generation natural gas'] = 0
            years_data['generation biomass'] = 0
            
            #~ print years_data
            ## add generation from purchases
            if not purchase_type is None:
                #~ print years_data["kwh_purchased"]
                years_data['generation ' + purchase_type ] += \
                    years_data["kwh_purchased"]
            
            ## add generation from other type 1        
            if not other_type_1 is None:
                years_data['generation ' + other_type_1 ] += \
                    years_data["other_1_kwh_generated"]
            
            ## add generation from other type 2        
            if not other_type_2 is None:
                years_data['generation ' + other_type_2 ] += \
                    years_data["other_2_kwh_generated"]
                    
            ## get total consumption
            years_data['consumption'] = years_data[["residential_kwh_sold",
                                        "commercial_kwh_sold",
                                        "community_kwh_sold",
                                        "government_kwh_sold",
                                        "unbilled_kwh"]].sum()
            ### get residential and non-resedential consumptions
            years_data['consumption residential'] = \
                years_data["residential_kwh_sold"]
            years_data['consumption non-residential'] = \
                years_data['consumption'] - \
                years_data['consumption residential']
                
            ### get the net generation
            phc = data.ix[year]["powerhouse_consumption_kwh"].sum()
            if np.isnan(phc):
                phc = years_data['generation diesel'] * phc_percent
                self.diagnostics.add_note("PCE Electricity",
                        "Powerhouse consumption not found for " + \
                        str(year) +" assuming to be " +\
                        str(phc_percent*100) + "% of gross generation.")
                years_data['net generation'] = years_data['generation'] 
                years_data['generation'] = years_data['generation'] + phc
            else:
                years_data['net generation'] = years_data['generation'] - phc
            #~ print years_data['generation diesel'], years_data['net generation']
            # other values
            years_data['fuel used'] = years_data['fuel_used_gal']
            years_data['line loss'] = \
                1.0 - years_data['consumption']/years_data['net generation']
            
            ### diesel efficiency
            try:
                years_data['efficiency'] = \
                    years_data['generation diesel'] /\
                    years_data['fuel_used_gal']
            except ZeroDivisionError:
                years_data['efficiency'] = np.nan
                
            if np.isinf(years_data['efficiency']):
                years_data['efficiency'] = np.nan
                
            ### these nead a mean
            years_data['residential_rate'] = \
                data.ix[year]['residential_rate'].mean()
            years_data['diesel_price'] = data.ix[year]['fuel_price'].mean()
            
            data_by_year.append(years_data)
            
        ### clean up
        columns = ["year","generation","consumption","fuel used",
            "efficiency","line loss","net generation","consumption residential",
            "consumption non-residential","kwh_purchased","residential rate",
            "diesel_price","generation diesel","generation hydro",
            "generation natural gas","generation wind","generation solar",
            "generation biomass", "diesel price"]
        processed_data = DataFrame(data_by_year)[columns]
        
        return processed_data
        
    def load_eia (self, **kwargs):
        """Load EIA Data, for a community or intertie
        
        Returns
        -------
        Generation: DataFrame
            Data fram of EIA generation data, grouped by type and year
        Sales: DataFrame
            Data fram of EIA sales data, grouped by year
        """
        datafile_generation = os.path.join(self.data_dir, 'eia_generation.csv')
        datafile_sales = os.path.join(self.data_dir, 'eia_sales.csv')
        
        ## get ids
        if "ids_to_use" in kwargs:
            ids = kwargs["ids_to_use"]
        else:
            ids = self.communities + self.aliases
            #~ print ids
            if not self.process_intertie:
                ## parent community or only community 
                if self.intertie_status in ['parent', 'not in intertie']:
                    ids = [self.communities[0], self.aliases[0]]
                else:
                    ## name and ailias of first child (community of interest)
                    ids = [self.communities[1], self.aliases[1]]
            ## cleanup ids
        ids = [i for i in ids if i != ""]
                
        if 'Glennallen' in ids:
            ids.append( "Copper Valley" )
        #~ print ids
        
        
        generation = read_csv(datafile_generation, comment = '#', index_col=3)
        
        generation = generation.ix[ids]
        if any(generation['NET GENERATION (megawatthours)'] < 0):
            self.diagnostics.add_note("EIA Electricity",
                "Negative generation values have been set to 0")
            idx = generation['NET GENERATION (megawatthours)'] < 0
            generation['NET GENERATION (megawatthours)'][idx] = 0
            
        
        generation = generation.ix[ids].\
            groupby(['Year','Reported Fuel Type Code']).sum()[[
                'TOTAL FUEL CONSUMPTION QUANTITY',
                'ELECTRIC FUEL CONSUMPTION QUANTITY',
                'TOTAL FUEL CONSUMPTION MMBTUS',
                'ELEC FUEL CONSUMPTION MMBTUS',
                'NET GENERATION (megawatthours)'
            ]]
        
        sales = read_csv(datafile_sales, comment = '#', index_col=2)

        sales = sales.ix[ids].groupby('Data Year').sum()[[
            'Residential Thousand Dollars','Residential Megawatthours',
            'Total Thousand Dollars','Total Megawatthours']]
            
        return generation, sales
        
    def helper_eia_prices (self, eia_sales, **kwargs):
        """ Function doc """
        data = eia_sales
        #~ print len(data)
        data.iloc[-1] 
        try:
            res_nonPCE_price = \
                float(data.iloc[-1]['Residential Thousand Dollars']) /\
                float(data.iloc[-1]['Residential Megawatthours'])
        except ZeroDivisionError:
            self.diagnostics.add_note('Community Electricity Prices EIA',
                "no residental sales")
            res_nonPCE_price = 0
            
        elec_nonFuel_cost = float(data.iloc[-1]['Total Thousand Dollars']) /\
            float(data.iloc[-1]['Total Megawatthours'])
        
        return res_nonPCE_price, elec_nonFuel_cost 
    
    def helper_electric_prices(self, **kwargs):
        """Calculates the electric prices
        
        Parameters
        ----------
        pce_data: DataFrame
            PCE data
        eia_sales:
            EIA Sales Data
        
        Returns
        -------
        dict
            configuration values in community section with keys
            residential non-PCE electric price and electric non-fuel price
        """
        if 'pce_data' in kwargs:
            process_function = self.helper_pce_prices
            data = kwargs['pce_data']
        elif 'eia_sales' in kwargs:
            process_function = self.helper_eia_prices
            data = kwargs['eia_sales']
        else:
            process_function = lambda x: (np.nan, np.nan)
            data = None
            #~ raise PreprocessorError, "No electric price data avaialbe"
            
        res_nonPCE_price, elec_nonFuel_cost = process_function(data)

        return {
            'community': {
                'residential non-PCE electric price' :  res_nonPCE_price, 
                'electric non-fuel price': elec_nonFuel_cost, 
            }
        }
        
    def helper_eia_generation(self, eia_generation, eia_sales, **kwargs):
        """process EIA data into a dataframe with yearly data for:
        "generation", "consumption", "fuel used", "efficiency", "line loss",
        "net generation", "consumption residential",
        "consumption non-residential", "kwh_purchased", "residential_rate",
        "diesel_price", "generation diesel", "generation hydro",
        "generation natural gas", "generation wind", "generation solar",
        "generation biomass". For both generation and sales data 
        
        Parameters
        ----------
        eia_generation: DataFrame
            data as loaded from the eia generation data file
        eia_sales: DataFrame
            data as loaded from the eia sales data file
            
        Returns 
        -------
        DataFrame
            yearly electic data for EIA
        """
        ### read kwargs
        phc_percent = kwargs['power_house_consumption_percet'] if \
            'power_house_consumption_percet' in kwargs else .03
        
        generation = eia_generation
        sales = eia_sales
        
        power_type_lib = {"WAT":"hydro",
                          "DFO":"diesel",
                          "WND":"wind",
                          "NG": "natural gas",
                          "WO":"diesel",
                          "OBL":"biomass",
                          "SUB":"coal",
                          "WDS":"biomass",
                          "JF": "diesel", # jet fuel
                          "OG": "natural gas", 
                          "LFG": "other", # land fill gass
                            }
                          
        data_by_year = []
        for year in generation.index.levels[0]:
            
            years_data = generation.sum(level=0).ix[year]
            years_data['year'] = year
            
            years_data["residential rate"] = np.nan
            years_data["diesel price"] = np.nan
            
            ## setup generation from diesel, hydro, etc
            years_data['generation diesel'] = 0
            years_data['generation hydro'] = 0
            years_data['generation solar'] = 0
            years_data['generation wind'] = 0
            years_data['generation natural gas'] = 0
            years_data['generation biomass'] = 0
            years_data['fuel used'] = 0
            # add any generation to types
            for type_code in generation.ix[year].index:
                if type_code in ["LFG", "SUB"]:
                    continue
                ## convert from MWh to kWh
                fuel_for_year = generation.ix[year].ix[type_code]
                type_generation = \
                    fuel_for_year['NET GENERATION (megawatthours)'] * 1000.0
                fuel_type = power_type_lib[type_code]
                years_data['generation ' + fuel_type] += type_generation
                
                ## if diesel add fuel used
                if fuel_type == 'diesel':
                    dfo = fuel_for_year['TOTAL FUEL CONSUMPTION QUANTITY'] *\
                        constants.barrels_to_gallons 
                    years_data['fuel used'] += dfo
            
            ## set net_generation and (gross_)generation
            years_data['net generation'] = \
                years_data['NET GENERATION (megawatthours)'] * 1000.0
                
            years_data['generation'] = years_data['net generation'] + \
                years_data['generation diesel'] * phc_percent
                
            self.diagnostics.add_note(
                "Community Generation(EIA)",
                "Gross generation assumed to be total net genetation plus " + \
                str((1+phc_percent)*100) + "% of diesel generation"
            )
            try:
                years_data["consumption"] = \
                    sales.ix[year]["Total Megawatthours"] * 1000.0
                years_data["consumption residential"] = \
                    sales.ix[year]["Residential Megawatthours"] * 1000.0
                years_data["consumption non-residential"] = \
                    years_data["consumption"] - \
                    years_data["consumption residential"]
            except KeyError:
                years_data["consumption"] = np.nan
                years_data["consumption residential"] = np.nan
                years_data["consumption non-residential"] = np.nan
                
            ## add calculated stuff
            years_data['line loss'] = 1.0 - years_data['consumption']/\
                                                years_data['net generation']

            years_data['efficiency'] = years_data['generation diesel'] / \
                                                        years_data['fuel used']
            #  zeros
            years_data['kwh_purchased'] = 0
            
            
            data_by_year.append(years_data)
            
        ### clean up
        columns = ["year","generation","consumption","fuel used",
            "efficiency","line loss","net generation","consumption residential",
            "consumption non-residential","kwh_purchased",
            "generation diesel","generation hydro",
            "generation natural gas","generation wind","generation solar",
            "generation biomass", "residential rate", 'diesel price']
        processed_data = DataFrame(data_by_year)[columns]
        
        return processed_data
        
    def helper_eia_generation_sales_only(self, eia_sales, **kwargs):
        """process EIA data into a dataframe with yearly data for:
        "generation", "consumption", "fuel used", "efficiency", "line loss",
        "net generation", "consumption residential",
        "consumption non-residential", "kwh_purchased", "residential_rate",
        "diesel_price", "generation diesel", "generation hydro",
        "generation natural gas", "generation wind", "generation solar",
        "generation biomass". if only eia sales data is available
        
        Parameters
        ----------
        eia_sales: DataFrame
            data as loaded from the eia sales data file
            
        Returns 
        -------
        DataFrame
            yearly electic data for EIA
        """
        sales = eia_sales
        
        data_by_year = []
        for year in sales.index:
            
            years_data = sales.sum(level=0).ix[year]
            years_data['year'] = year
            
            years_data["residential rate"] = np.nan
            years_data["diesel price"] = np.nan
            
            ## setup generation from diesel, hydro, etc
            years_data['generation diesel'] = np.nan
            years_data['generation hydro'] = np.nan
            years_data['generation solar'] = np.nan
            years_data['generation wind'] = np.nan
            years_data['generation natural gas'] = np.nan
            years_data['generation biomass'] = np.nan
            years_data['fuel used'] = np.nan
           
            
            ## set net_generation and (gross_)generation
            years_data['net generation'] = np.nan
                
            years_data['generation'] = np.nan
                
            self.diagnostics.add_note(
                "Community Generation(EIA)",
                "No generation data")
        
            years_data["consumption"] = \
                sales.ix[year]["Total Megawatthours"] * 1000.0
            years_data["consumption residential"] = \
                sales.ix[year]["Residential Megawatthours"] * 1000.0
            years_data["consumption non-residential"] = \
                years_data["consumption"] - \
                years_data["consumption residential"]
            
                
            ## add calculated stuff
            years_data['line loss'] = np.nan
            years_data['efficiency'] = np.nan 
            years_data['kwh_purchased'] = np.nan
            
            
            data_by_year.append(years_data)
            
        ### clean up
        columns = ["year","generation","consumption","fuel used",
            "efficiency","line loss","net generation","consumption residential",
            "consumption non-residential","kwh_purchased",
            "generation diesel","generation hydro",
            "generation natural gas","generation wind","generation solar",
            "generation biomass", "residential rate", 'diesel price']
        processed_data = DataFrame(data_by_year)[columns]
        
        return processed_data
        
    def helper_yearly_electric_data (self, **kwargs):
        """Create yearly electric data from available PCE or EIA data. will 
        create empty structure if no data found
        
        Parameters
        ----------
        pce_data: DataFrame
            data as loaded from the PCE data file
        eia_generation: DataFrame
            data as loaded from the eia generation data file
        eia_sales: DataFrame
            data as loaded from the eia sales data file
            
        Returns
        -------
        data: DataFrame
            Yearly Electric Data for:
            "generation","consumption","fuel used",
            "efficiency","line loss","net generation",
            "consumption residential",
            "consumption non-residential","kwh_purchased","residential_rate",
            "diesel_price","generation diesel","generation hydro",
            "generation natural gas","generation wind","generation solar",
            "generation biomass"
        """
        #~ print kwargs.keys()
        if 'pce_data' in kwargs:
            data = self.helper_pce_generation(kwargs['pce_data'])
        elif 'eia_generation' in kwargs and 'eia_sales' in kwargs:
            data = self.helper_eia_generation (
                kwargs['eia_generation'], 
                kwargs['eia_sales'] )
        elif 'eia_sales' in kwargs:
            data = self.helper_eia_generation_sales_only ( kwargs['eia_sales'] )
        else:
            data = DataFrame(columns=
                ["year","generation","consumption","fuel used",
                "efficiency","line loss","net generation",
                "consumption residential",
                "consumption non-residential","kwh purchased","residential rate",
                "diesel_price","generation diesel","generation hydro",
                "generation natural gas","generation wind","generation solar",
                "generation biomass", "diesel price"]
            )
            #~ raise PreprocessorError, "No generation data avaialbe"
        return data
        
    def process_generation (self, **kwargs):
        """Preprocess generation data
        
        Returns
        -------
        data: Dict
            data for linelosses, diesel generation efficiency, and utility data
        """
        
        data = self.helper_yearly_electric_data(**kwargs)
        
        data = {
            "community":{
                "line losses": self.helper_line_losses(data),
                "diesel generation efficiency":
                     self.helper_diesel_efficiency(data),
                "utility info": self.helper_generation(data),
            }
        
        }
        return data
        
    def helper_line_losses (self, electric_data, **kwargs):
        """caclulates the average line loss percent from last N years
        
        Parameters
        ----------
        electic_data: DataFrame
            yearly electric data
        max_line_loss: int 
            maximum limit on the line losses
        default_line_loss: int 
            default line losses when a nan is caclulated
        years_to_average: int 
            years of data to use in average (N)
            
        Returns 
        -------
        float
            Average line loss percentage
        """
        #~ default_line_losses: default max is 40
        max_line_losses = \
            kwargs['max_line_loss'] if 'max_line_loss' in kwargs else 40
        default_line_losses = \
            kwargs['default_line_loss'] if 'default_line_loss' in kwargs else 10
        ## last n years of measured data to average for value to use 
        ## the -1 is to allow index of last n vals
        years = -1 * \
            (kwargs['years_to_average'] if 'years_to_average' in kwargs else 3)
            
        self.diagnostics.add_note('Community: line losses',
            'Line losses are being calculated as average of last ' + \
            str(-1*years) + ' of measured data'
        )
 
        ## get mean of last 3 years and convert to a percent from decimal

        line_losses = electric_data['line loss'].iloc[years:].mean() * 100
        
        if np.isnan(line_losses) or line_losses < 0:
            line_losses = default_line_losses
            self.diagnostics.add_note('Community: line losses',
                'Caclulated line losses were invalid (less than 0,' + \
                ' or not a number). Setting to default (' + \
                str(default_line_losses) + '%)'
            )
            
        if line_losses > max_line_losses:
            line_losses = max_line_losses
            self.diagnostics.add_note('Community: line losses',
                'Caclulated line losses were greter than the maximum allowed. '
                'Setting to maximum (' + \
                str(max_line_losses) + '%)'
            )
        return round(line_losses,2)
        
        ## should these be processed here or in the CD module
        
        
        
    def helper_diesel_efficiency (self, electric_data, **kwargs):
        """caclulates the average diesel (kWh/gal) from last N years
        
        Parameters
        ----------
        electic_data: DataFrame
            yearly electric data
        default_diesel_efficieny: int 
            default line losses when a nan is caclulated
        years_to_average: int 
            years of data to use in average (N)
            
        Returns 
        -------
        float
            Average diesel efficiency
        """
        default_efficiency = kwargs['default_diesel_efficieny']\
            if 'default_diesel_efficieny' in kwargs else 12
        ## last n years of measured data to average for value to use 
        ## the -1 is to allow index of last n vals
        years = -1 * \
            (kwargs['years_to_average'] if 'years_to_average' in kwargs else 3)
            
        self.diagnostics.add_note('Community: diesel generation efficiency',
            'iesel generation efficiency is being calculated as average of ' +\
            'last ' + str(-1*years) + ' of measured data'
        )
        
        efficiency = electric_data['efficiency'].iloc[years:].mean()
        
        if np.isnan(efficiency) or efficiency <= 0:
            efficiency = default_efficiency
            self.diagnostics.add_note('Community: diesel generation efficiency',
                'Caclulated diesel generation efficiency was invalid ' + \
                '(less than or equall to 0,' + \
                ' or not a number). Setting to default (' + \
                str(default_efficiency) + ')'
            )
            
        return efficiency
        
        
    def helper_generation (self, electric_data, **kwargs):
        """creates utility info dataFrame
        
        Parameters
        ----------
        electic_data: DataFrame
            yearly electric data

            
        Returns 
        -------
        DataFrame
            the utility info
        """
        ## todo combine generation and generation numbers in the other places 
        generation = electric_data.set_index('year')[[
            'consumption',
            'consumption residential',
            'consumption non-residential',
            'net generation',
            'generation diesel',
            'generation hydro',
            'generation natural gas',
            'generation wind',
            'generation solar',
            'generation biomass',
            'line loss',
            'efficiency',
            'residential rate',
            'diesel price',
        ]]
        generation.index = generation.index.astype(int)
        generation = generation.sort_index()
        return generation.round(3)
        
        
    def load_heating_degree_days (self, **kwargs):
        """Load heating degree day data for a community
        
        returns 
        -------
        float
            heating degree days
        """
        datafile = os.path.join(self.data_dir, "heating_degree_days.csv")
        data = read_csv(datafile, index_col=0, comment = "#", header=0)
        
        ## community
        if self.community in data.index:
            ids = self.community
        ## community alais ,note: check if community is a child
        elif str(self.aliases[0]) in data.index:
            child_or_parent = 0
            if self.intertie_status == 'child':
                child_or_parent = 1
            ids = self.aliases[child_or_parent]
        ## parent is alaways index 0 if it gets this far
        elif str(self.communities[0]) in data.index:
            ids = self.communities[0]
            self.diagnostics.add_note('Community: heating degree days',
                'Using parents heating degree days'
            )
        ## parent alais is alaways index 0 if it gets this far   
        elif str(self.aliases[0]) in data.index:
            ids = self.aliases[0]
            self.diagnostics.add_note('Community: heating degree days',
                'Using parents heating degree days'
            )
        else:
            raise PreprocessorError, 'No Heating Degree data found'

        return data.ix[ids]['HDD in ARIS equations']
        
    def load_heating_fuel_premium (self, **kwargs):
        """load heating fuel premium
        
        Returns
        -------
        float
            the addition cost for heating fuel on top of the diesel price 
        for the region community is in.
        """
        datafile = os.path.join(self.data_dir,"heating_fuel_premium.csv")
        data = read_csv(datafile, index_col=0, comment='#')
        
        ids = self.regions[0].replace(' Region','') 
        if self.intertie_status == 'child':
            ids = self.regions[1].replace(' Region','') 
        
        premium = float(data.ix[ids])
        if premium < 0:
            self.diagnostics.add_note('Heating Fuel Premium',
                ('Value was less than 0. Premium must be greater'
                ' than or equal to 0, seting to 0')
            )
            premium = 0 
        return premium 
        
    def load_election_divisions (self, **kwargs):
        """load the data for a communities election districts
        
        Returns
        -------
        senate: list
            list of state senate districs 
        house: list
            list of state house districs 
        """
        datafile = os.path.join(self.data_dir,'election-divisions.csv')
        data = read_csv(datafile, index_col=0, comment='#')
        data.index = [i.replace(' (part)','') for i in data.index]
        
        ## make it a list index to make all acesses return same format
        senate = data.ix[[self.community]]['Senate'].values.tolist()
        house = data.ix[[self.community]]['House District'].values.tolist()
        return senate, house
        
    def load_goals (self, **kwargs):
        """load the goals
        
        Returns
        -------
        community: list
            list of community goals
        house: list
            list of state regional goals
        """
        datafile = os.path.join(self.data_dir,'goals_community.csv')
        data = read_csv(datafile, index_col=0, comment='#')
        #~ data.index = [i.replace(' (part)','') for i in data.index]
        idx = 1 if self.intertie_status == 'child' else 0  
        ids = [self.community, self.aliases[idx]]
        ids = [ i for i in ids if i != '' ]
        
        community = data.ix[ids][data.ix[ids].isnull().all(1) == False]
        community = community.T
        community = community[community.columns[0]]
        community = community[~community.isnull()]
        region = community['Region']

        community = [g.decode('unicode_escape').encode('ascii','ignore') \
            for g in community.values[1:]]
        datafile = os.path.join(self.data_dir,'goals_regional.csv')
        data = read_csv(datafile, index_col=0, comment='#')
        regional = data.ix[region]
        regional = regional[~regional.isnull()]
        regional = [g.decode('unicode_escape').encode('ascii','ignore') \
            for g in regional.values[1:]]
    
        return community, regional
    
    def load_road_system_status (self, **kwargs):
        """load boolead for if community has acces to road system 
        or marine highway
        
        Returns
        -------
        status: bool
        """
        datafile = os.path.join(self.data_dir,"road_system.csv")
        data = read_csv(datafile ,comment = '#',index_col = 0)
        
        idx = 1 if self.intertie_status == 'child' else 0  
        ids = [self.community, self.aliases[idx]]
        ids = [ i for i in ids if type(i) is str ]
                            
        data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
        status = data['On Road/SE'].values[0]
        status = True if status.lower() == 'yes' else False
        
        return status

    
    def load_diesel_powerhouse_data (self, **kwargs):
        """Load diesel power house data
        
        Returns 
        -------
        DataFrame
        """
        datafile = os.path.join(self.data_dir, "diesel_powerhouse_data.csv")
        data = read_csv(datafile, comment = '#', index_col = 0)
        
        idx = 1 if self.intertie_status == 'child' else 0  
        ids = [self.community, self.aliases[idx]]
        ids = [ i for i in ids if type(i) is str ]
        
        data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
        if data.size == 0:
            data.ix[self.community] = 'N/a'
        
        return data
        
    def process_diesel_powerhouse_data (self, **kwargs):
        """preprocess diesel power house data
        
        Returns
        -------
        Dict:
            community section with heat recovery operational and 
        switchgear suatable for renewables data
        """
        data = self.load_diesel_powerhouse_data()
        
        hr_operational = data['Waste Heat Recovery Opperational'].values[0]
        hr_operational = True if hr_operational.lower() == 'yes' else False
        switchgear_status = data['Switchgear Suitable'].values[0]
        switchgear_status = True if  switchgear_status.lower() == 'yes' \
            else False
        
        total = data['Total Number of generators'].values[0]
            
        total_capacity = data['Total Capacity (in kW)'].values[0]
        try:
            float(total_capacity)
        except:
            total_capacity = np.nan 
            
        largest = data['Largest generator (in kW)'].values[0]
        size = data['Sizing'].values[0]
            
        return {
            'community': {
                'heat recovery operational': hr_operational,
                'switchgear suatable for renewables': switchgear_status,
                'total capacity': total_capacity,
                'number diesel generators': total,
                'largest generator': largest,
                'diesel generator sizing': size,
            }
        }
        
    def load_fuel_prices (self, **kwargs):
        """load all fuel prices for community
        
        Returns
        -------
        price_cord: float
            price of cordwood ($/cord)
        price_pellet: float 
            price of pellets ($/ton)
        prices_diesel: DataFrame
            prics of diesel per year ($/gal)/year
        price_propane: float
            price of propane per gallon ($/gal)
        """
        datafile_biomass = os.path.join(self.data_dir, "biomass_prices.csv")
        datafile_diesel = os.path.join(self.data_dir, "diesel_fuel_prices.csv")
        datafile_propane = os.path.join(self.data_dir,
            "propane_price_estimates.csv")
        
        idx = 1 if self.intertie_status == 'child' else 0  
        ids = [self.community, self.aliases[idx]]
        ids = [ i for i in ids if type(i) is str ]
        
        data = read_csv(datafile_biomass, comment = '#', index_col = 0)
       
        try:
            set_as_0 = False
            price_cord = float(data.ix[ids]\
                [data.ix[ids].isnull().all(1) == False]['Biomass ($/Cord)'])
            if np.isnan(price_cord):
                set_as_0 = True
        except TypeError:
            set_as_0 = True
        if set_as_0:
            self.diagnostics.add_note("Community: Pellet Cordwood", 
                "Could not find price. seting as $0")
            price_cord = 0
        
        try:
            set_as_0 = False
            price_pellet = float(data.ix[ids]\
                [data.ix[ids].isnull().all(1) == False]['Pellets ($/ton)'])
            if np.isnan(price_pellet):
                set_as_0 = True
        except TypeError:
            set_as_0 = True
            
        if set_as_0:
            self.diagnostics.add_note("Community: Pellet Price", 
                "Could not find price. seting as $0")
            price_pellet = 0
        
        data = read_csv(datafile_diesel, comment = '#', index_col = 0)
        data.index = [c.split('-')[0] for c in data.index]
        prices_diesel = data.ix[ids][data.ix[ids].isnull().all(1) == False].T
        if prices_diesel.empty:
            if self.intertie_status == 'child':
                prices_diesel = data.ix[[self.communities[0]]].T
                self.diagnostics.add_note('prices',
                    'using parents diesel prices')
                ## dumb Nondalton, Ilimiana fix
                if 'Nondalton' in self.communities:
                    prices_diesel = data.ix[['Iliamna']].T
            else:
                communities = os.path.join(self.data_dir, "community_list.csv")
                index = read_csv(communities, index_col=2, comment="#")
                index = index.ix[self.regions[0]]['Community'].values
                prices_diesel = DataFrame(data.ix[index].mean().T, 
                    columns =['Regional Average'])
                
                self.diagnostics.add_note('Community: Diesel Prices', 
                        'Not found. Using regional average')
                #~ raise PreprocessorError, "could not find diesel prices"
        prices_diesel.index.name = 'year'
        prices_diesel.columns.name = None
        
        
        
        data = read_csv(datafile_propane, comment = '#', index_col = 0)
        
        try:
            set_as_0 = False
            price_propane = float(data.ix[ids]\
                [data.ix[ids].isnull().all(1) == False]['Propane ($/gallon)'])
            if np.isnan(price_propane):
                set_as_0 = True
        except TypeError:
            set_as_0 = True
            
        if set_as_0:
            self.diagnostics.add_note("Community: Propane Price", 
                "Could not find price. seting as $0")
            price_propane = 0
        
        
        return price_cord, price_pellet, prices_diesel, price_propane
        
    def load_measured_heating_fuel_prices (self, **kwargs):
        """Load the known heating fuel prices
        
        Returns
        -------
        DataFrame
            measured fuel price data
        """
        datafile = os.path.join(self.data_dir, "fuel-price-survey-data.csv")
        fuel_prices = read_csv(datafile, index_col = 1)
        
        ids = self.GNIS_ids
        if not self.process_intertie:
            if self.intertie_status == 'child':
                ids = [ids[1]]
            else:
                ids = [ids[0]]
        
        ids = ids[0]
        #~ print ids
        current_year = self.data['community']['current year']
        fuel_prices = fuel_prices[fuel_prices['year'] < current_year]
        #~ data = [] 
        try:
            data = fuel_prices.ix[ids].groupby('year').mean()[[
                'no_1_fuel_oil_price','no_2_fuel_oil_price']].mean(1)

            data = DataFrame(data)
            data.columns = ['average price']
        except (KeyError, ValueError):
            data = DataFrame(columns = ['average price'])
            data.index.name = 'year'
        
        return {'community': {'heating fuel prices': data}}
        

    def helper_fuel_prices (self, ** kwargs):
        """process fuel prices in to dictionay section
        
        Returns
        -------
        Dict
            community section with keys 'diesel prices', 'propane price'
        'cordwood price', 'pellet price', 'natural gas price'
        """
        price_cord, price_pellet, prices_diesel, price_propane = \
            self.load_fuel_prices()
        
        ## todo add statment to fix for nuqisu.. and Barrow
        price_ng = 0
        
        return {
            'community': {
                'diesel prices': prices_diesel, 
                'propane price': price_propane,
                'cordwood price': price_cord,
                'pellet price': price_pellet, 
                'natural gas price': price_ng,
            } 
        }
        
    def process_prices (self, **kwargs):
        """process electic and heating fuel prices
        
        returns 
        dict:
            data for prices
        """
        
        electric_prices = self.helper_electric_prices(**kwargs)
        fuel_prices = self.helper_fuel_prices()
        electric_non_fuel_prices = None
        
        
        data = merge_configs(electric_prices, fuel_prices)
        data['community']['electric non-fuel prices'] = electric_non_fuel_prices
        return data
        
    def load_renewable_capacities (self, **kwargs):
        """load renewable energy capacities
        
        Returns
        -------
        DataFrame
        """
        
        datafile = os.path.join(self.data_dir, 
            'renewable_generation_capacities.csv')

        data = read_csv(datafile, comment = '#', index_col = 0)[
            ['Resource Type','Resource Sub-Type',
            'Capacity (kW)','Average Expected Annual Generation (kWh)']
        ]
        data.index = [i.replace('_',' ') for i in data.index]
        ids = self.communities + self.aliases
        #~ print ids
        if not self.process_intertie:
            ## parent community or only community 
            if self.intertie_status in ['parent', 'not in intertie']:
                ids = [self.communities[0], self.aliases[0]]
            else:
                ## name and ailias of first child (community of interest)
                ids = [self.communities[1], self.aliases[1]]
        ## cleanup ids
        ids = [i for i in ids if i != ""]
        data = data.ix[ids]

        data = data.groupby(['Resource Type']).sum()

        return data
        
    def process_renewable_capacities (self, **kwargs):
        """Process reneable capacities
        
        Returns 
        -------
        Dict
        """
        ## in kW
        hydro_capacity = 0
        wind_capacity = 0
        solar_capacity = 0
        
        ## in  kWh
        hydro_generation = 0
        wind_generation = 0
        solar_generation = 0 
        
        try:
            data = self.load_renewable_capacities()
            ## hydro 
            try:
                hydro_capacity = data.ix['Hydro']['Capacity (kW)']
                hydro_generation = \
                    data.ix['Hydro']['Average Expected Annual Generation (kWh)']
            except KeyError:
                self.diagnostics.add_note('Community: Renewable Capacities',
                    'No hydro data found. Values have been set to 0')
            ## solar 
            try:
                solar_capacity = data.ix['Solar']['Capacity (kW)']
                solar_generation = \
                    data.ix['Solar']['Average Expected Annual Generation (kWh)']
            except KeyError:
                self.diagnostics.add_note('Community: Renewable Capacities',
                    'No solar data found. Values have been set to 0')
            
            ## wind
            try:
                wind_capacity = data.ix['Wind']['Capacity (kW)']
                wind_generation = \
                    data.ix['Wind']['Average Expected Annual Generation (kWh)']
            except KeyError:
                self.diagnostics.add_note('Community: Renewable Capacities',
                    'No wind data found. Values have been set to 0')
            
            
        except KeyError:
            self.diagnostics.add_note('Community: Renewable Capacities',
                'No data found. Values have been set to 0')
                
        return {
            'community' : {
                'hydro generation limit': hydro_generation,
                'solar generation limit': solar_generation,
                'wind generation limit': wind_generation,
                'hydro capacity': hydro_capacity,
                'solar capacity': solar_capacity,
                'wind capacity': wind_capacity,
            
            }
        }
    
    def load_construction_multiplier (self, **kwargs):
        """Load construction multipliers
        
        Retruns 
        -------
        float
            regional multiplier for community
        """
        datafile = os.path.join(self.data_dir, "regional_multipliers.yaml")
        with open(datafile) as fd:
            data = yaml.load(fd)
        
        r = self.regions[0]
        if r == 'Kodiak Region':
            r = 'Kodiak'
        
        return data[r]
        
        
        
        
