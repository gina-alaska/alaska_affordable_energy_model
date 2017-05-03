"""
preprocessor
------------

process data into a format for the model to use
"""
from pandas import DataFrame,read_csv, concat
import shutil
import os.path
from diagnostics import diagnostics
import numpy as np
#~ from forecast import growth
from datetime import datetime

from importlib import import_module

from aaem.components import comp_lib
import aaem.yaml_dataframe as yd

GENERATION_AVG = .03



from config_IO import merge_configs


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
    def __init__ (self, community, data, diag = None, process_intertie = False):
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
            diag = diagnostics()
        self.diagnostics = diag
        self.data_dir = os.path.join(os.path.abspath(data),"")


        self.intertie_status = self.detrmine_intertie_status(community)
        
        if process_intertie == True and self.intertie_status != 'parent':
            raise StandardError, "Cannot Preprocess as interite not a parent"
            
        self.process_intertie = process_intertie
        
        if self.intertie_status == "not in intertie":
            self.intertie = [community]
        else:
            self.intertie = self.get_all_intertie_communties(
                os.path.join(self.data_dir,"current_interties.csv"),
                community
            )

        ## all communities on the interties to make loading more standard
        self.communities, self.regions ,self.GNIS_ids, self.FIPS_ids, \
            self.aliases = \
            self.load_ids(
                os.path.join(self.data_dir, "community_list.csv"),
                self.intertie
            )
        self.data = {}
        
    def run (self, **kwargs):
        """ Function doc """
        self.data = merge_configs(self.data, self.create_community_section())
        self.data = merge_configs(self.data, self.create_forecast_section())
        
    def load_ids (self, datafile, communities):
        """get a communities id information
        """
        data = read_csv(datafile, comment = '#')
        ids = data[data.isin(self.intertie).any(axis=1)]
        if len(ids) != len(communities):
            print len(ids)
            raise StandardError, "Could not find community ID info"
        ids = ids.set_index('Community').ix[self.intertie]
        return list(ids.index), \
            list(ids['Energy Region'].values), \
            list(ids['GNIS'].values), \
            list(ids['FIPS'].values), \
            list(ids['Alias'].values) 
            
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
            other_communites = data.ix[community]['Other Community on Intertie']
            if plant.lower()  == 'yes' and other_communites != "''":
                status = "parent"
            else: 
                # if 'Plant Intertied' not yes or no communites listed
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
        
        ## TODO modify all code format to support the new tags and the 
        ## reworked intertie format
        if self.intertie_status != "not in intertie":
            intertie = self.communities 
        else:
            intertie = "not in intertie"
        data = {
            'community': {
                'name': self.community,
                'alternate name': self.aliases[0],
                'region': self.regions[0],
                'GNIS ID': self.GNIS_ids[0],
                'FIPS ID': self.FIPS_ids[0],
                'intertie': intertie
            },
        }
        return data
        
        
    def create_forecast_section (self, **kwargs):
        """create forecast section
        
        Returns
        -------
        dict: 
            the forecast section of a confinguration object 
        """
        population = self.load_population(**kwargs)
        data = {
            'forecast': {
                'population':population
            }
        }
        
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
        
        # TODO check intertie needs normal Population?
        #~ if not self.process_intertie:
            #~ ids = [ids[0]]
        ids = [ids[0]]
       
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
        return pops
        
    def load_pce (self, **kwargs):
        """load PCE data
        
        Returns
        -------
        pce_data: DataFrame
            the PCE Data for the community (or intertie if 
            process_intertie is True)
        """
        
        ### TODO fix weird cases
        # "Klukwan": [["Klukwan","Chilkat Valley"]]
            
        ###
        datafile = os.path.join(self.data_dir, 
            "power-cost-equalization-pce-data.csv")
        data = read_csv(datafile, index_col=1, comment = "#")
        ## clean up index
        data.index = [i.split(',')[0] for i in data.index]
        
        ## get ids
        ids = self.communities + self.aliases
        if not self.process_intertie:
            ids = [self.communities[0], self.aliases[0]]
        ## cleanup ids
        ids = [i for i in ids if type(i) is str]
        
        ## Klukwan fix - see not at top of function
        if 'Klukwan' in ids:
            ids += ["Chilkat Valley"]    
        
        ## get data
        data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
        return data
        
    def process_electric_prices_pce (self, pce_data):
        """process the PCE electric prices
        
        Parameters
        ----------
        pce_data: DataFrame
            the pce data to process prices for
            
        Returns
        -------
        dict
            configuration values in community section with keys
            residential non-PCE electric price and electric non-fuel price
        
        
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
        
        ## get last year with full data
        last_year = data["year"].max()
        while len(data[data["year"] == last_year])%12 != 0:
            last_year -= 1
        
        ## get last years electric fuel cost
        cols = [
            "residential_kwh_sold", "commercial_kwh_sold", 
            "community_kwh_sold", "government_kwh_sold", "unbilled_kwh"
        ]
        elec_fuel_cost = (
            data[data["year"] == last_year]['fuel_cost']/\
            data[data["year"] == last_year][cols].sum(axis = 1)
        ).mean()
        
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
            
        ## TODO change these name in other code
        return {
            'community': {
                'residential non-PCE electric price' :  res_nonPCE_price, # was res non-PCE elec cost 
                'electric non-fuel price': elec_nonFuel_cost, # was elec non-fuel cost
            }
        }
    
    
    def load_purchased_power_lib (self, **kwargs):
        """load pruchaced power lib for pce data
        
        Returns
        -------
        dict:
            dictionary of utilities and the type of generation they supply
        """
        ## get ids
        ids = self.communities + self.aliases
        if not self.process_intertie:
            ids = [self.communities[0], self.aliases[0]]
        
        ## TODO: weird
        if 'Klukwan' in ids:
            ids += ["Chilkat Valley"]
            
        ## setup data
        datafile = os.path.join(self.data_dir, "purchased_power_lib.csv")
        data = read_csv(datafile, index_col=0, comment = '#')
        data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
        data= data.set_index('purchased_from')
        
        ### create purchased power lib
        lib = {}
        for utility in set(data.index):
            source = data.ix[utility]['Energy Source']
            if not type(source) is str:
                if 1 != len(set(data.ix[utility]['Energy Source'].values)):
                    raise StandardError, \
                        "More Than One Energy Source in Purcased power lib"
                source = data.ix[utility]['Energy Source'].values[0]
            
            lib[utility] = source
            
        return lib
    
    def process_generation_pce (self, pce_data):
        data = pce_data[[
            "year","diesel_kwh_generated", "powerhouse_consumption_kwh",
            "hydro_kwh_generated", "other_1_kwh_generated", "other_1_kwh_type",
            "other_2_kwh_generated", "other_2_kwh_type", 'purchased_from',
            'kwh_purchased', "fuel_used_gal", "residential_kwh_sold",
            "commercial_kwh_sold", "community_kwh_sold", "government_kwh_sold",
            "unbilled_kwh", "residential_rate", "fuel_price"]]
            
        
        
        
        
