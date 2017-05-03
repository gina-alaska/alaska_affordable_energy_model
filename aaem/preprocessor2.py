"""
preprocessor.py
ross spicer

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


        self.intertie_status = self.detrmine_intertie_status( 
            os.path.join(self.data_dir,"current_interties.csv"),
            community
        )
        
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
        print communities
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
            
    def detrmine_intertie_status (self, datafile, community):
        """ detrmine if commiunity is parent, child, or not in intertie
        """
        data = read_csv(datafile, index_col=0, comment = "#").fillna("''")
        
        ### TODO: figure this out
        if community in ['Klukwan']:
            return "not in intertie"
        
        if community in data.index: 
            plant = data.ix[community]['Plant Intertied']
            other_communites = data.ix[community]['Other Community on Intertie']
            if plant.lower()  == 'yes' and other_communites != "''":
                status = "parent"
            else:
                status = "not in intertie"
        elif (data == community).any().any():
            status = 'child'
        else:
            status = "not in intertie"
        return status
    
    def get_all_intertie_communties (self, datafile, community):
        """
        will return list as 
            parent(community_of_interest), child, child,  or
            parent, child(community_of_interest), other child, other child
        depending on weatehr the community of interest is has an
        intertie status of paret or child
        """
        data = read_csv(datafile, index_col=0, comment = "#").fillna("''")
        if community in data.index: 
            intertie = [community] +\
                list(data.ix[community].drop('Plant Intertied'))
            intertie = [c for c in intertie  if c != "''"]
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
        """
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
        """ Function doc """
        
        population = self.load_population(
            os.path.join(self.data_dir, "population_projections.csv")
        )
        data = {
            'forecast': {
                'population':population
            }
        }
        
        return data
        
        
    def load_population (self, datafile, **kwargs):
        """
        """
        in_file = datafile

        ids = self.GNIS_ids
        
        # intertie needs normal Population?
        #~ if not self.process_intertie:
            #~ ids = [ids[0]]
        ids = [ids[0]]
        
        threshold = kwargs['threshold'] if 'threshold' in kwargs else 20
        end_year = kwargs['end_year'] if 'end_year' in kwargs else 2050
        current_year = \
            kwargs['current_year'] if 'current_year' in kwargs else 2015
        start_year = kwargs['start_year'] if 'start_year' in kwargs else 2003
        
        #change to support 1 as one percent as opposed to .01
        percent = kwargs['percent'] if 'percent' in kwargs else .02
        
        # load data & remove name of town
        pops = read_csv(in_file, index_col = 1)
        pops = pops.ix[ids].drop('place_name', axis = 1).sum()
    
        # set index to integers
        pops.index = pops.index.astype(int)

        ## interpolate missing values
        if pops[ pops.isnull()].size != 0:
            self.diagnostics.add_warning("Forecast: Population",
                "Missing values were found, interpolation may occur")
        
            pops = pops.interpolate()
        
        pops = DataFrame(pops.ix[2003:])
        pops.columns  = ["population"]
        ## check threshold
        if (pops.values < threshold).any():
            self.diagnostics.add_warning("Forecast: Population",
                "less than threshold (" + str(threshold) + ")")
        
        ## check change
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
        
    def load_pce (self):
        """ Function doc """
        
        ### TODO fix weird cases
        # "Klukwan": [["Klukwan","Chilkat Valley"]]
            
        ###
        in_file = os.path.join(self.data_dir,
                        "power-cost-equalization-pce-data.csv")
        data = read_csv(in_file, index_col=1, comment = "#")
        # clean up index
        data.index = [i.split(',')[0] for i in data.index]
        
        ids = self.communities + self.aliases
        if not self.process_intertie:
            ids = [self.communities[0], self.aliases[0]]
        
        if 'Klukwan' in ids:
            ids += ["Chilkat Valley"]    
        
        ids = [i for i in ids if type(i) is str]
        #~ print ids
        data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
        return data
        
    def process_electric_prices_pce (self, pce_data):
        """
        """
        ## todo add some intertie stuff?
        data = pce_data[[
            "year","month","residential_rate",
            "pce_rate","effective_rate","residential_kwh_sold",
            "commercial_kwh_sold",
            "community_kwh_sold",
            "government_kwh_sold",
            "unbilled_kwh", "fuel_cost"
        ]]
        
        # get last year with full data
        last_year = data["year"].max()
        while len(data[data["year"] == last_year])%12 != 0:
            last_year -= 1
        print last_year
        
        
        ## get last years electric fuel cost
        cols = [
            "residential_kwh_sold", "commercial_kwh_sold", 
            "community_kwh_sold", "government_kwh_sold", "unbilled_kwh"
        ]
        elec_fuel_cost = (
            data[data["year"] == last_year]['fuel_cost']/\
            data[data["year"] == last_year][cols].sum(axis = 1)
        ).mean()
        print elec_fuel_cost 
        
        if np.isnan(elec_fuel_cost):
            elec_fuel_cost = 0.0
            self.diagnostics.add_note("Community: Electric Prices(PCE)",
                "electric fuel price not available, seting to 0")
                
        res_nonPCE_price = data[data["year"] == \
                                last_year]["residential_rate"].mean()
        elec_nonFuel_cost = res_nonPCE_price - elec_fuel_cost
        
        #~ self.diagnostics.add_note("Community: Generation(PCE)",
                                #~ "calculated res non-PCE elec cost: " + \
                                 #~ str(res_nonPCE_price))
        #~ self.diagnostics.add_note("Electricity Prices PCE",
                                    #~ "calculated elec non-fuel cost: " + \
                                    #~ str(elec_nonFuel_cost))
        return {
            'community': {
                'residential non-PCE electric price' :  res_nonPCE_price, # was res non-PCE elec cost 
                'electric non-fuel price': elec_nonFuel_cost, # was elec non-fuel cost
            }
        }
    
    
    def load_purchased_power_lib (self):
        lib_file = os.path.join(self.data_dir, "purchased_power_lib.csv")
        
        #~ try:
        
        
        ids = self.communities + self.aliases
        if not self.process_intertie:
            ids = [self.communities[0], self.aliases[0]]
        
        
        ## TODO: weird
        if 'Klukwan' in ids:
            ids += ["Chilkat Valley"]
            
        data = read_csv(lib_file, index_col=0, comment = '#')
        data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
        
        data= data.set_index('purchased_from')
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
            
        
        
        
        
