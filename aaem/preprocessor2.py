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
from collections import Counter
from importlib import import_module


from aaem.components import comp_lib
import aaem.yaml_dataframe as yd
import aaem.constants as constants
from aaem.config_IO import save_config

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
    def __init__ (self, community, data_dir, diag = None, process_intertie = False):
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
            self.aliases = \
            self.load_ids(
                os.path.join(self.data_dir, "community_list.csv"),
                self.intertie
            )
        self.data = {}
        
    def run (self, **kwargs):
        """ Function doc """
        print self.community, 'Intertie' if self.process_intertie else ''
        
        data = self.load_pce()
        if len(data) == 0:
            data = self.load_eia()
            if len(data[0]) == 0 or len(data[1]) == 0:
                source = None
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
        
        ## try paret if source is none and a child
        if source is None:
            # TODO, do i use parent or all interttie ?
            ids_to_use = [self.communities[0],self.aliases[0]]
            data = self.load_pce(ids_to_use=ids_to_use) 
            if len(data) == 0:
                data = self.load_eia(ids_to_use=ids_to_use)
                if len(data[0]) == 0 or len(data[1]) == 0:
                    print "No generation data found"
                    return
                    #~ raise PreprocessorError, "No generation data found"
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
            print "ids used", ids_to_use
        
        print source
        if source == 'pce':
            generation_data = self.process_generation(pce_data = data) 
            sales_data = self.process_prices(pce_data = data) 
        else: # 'eia'
            generation_data = self.process_generation(
                eia_generation = data[0],
                eia_sales = data[1],
            ) 
            sales_data = self.process_prices(
                eia_sales = data[1],
            ) 
        
        #~ print len(generation_data)
        #~ print sales_data
        self.data = merge_configs(self.data, self.create_community_section())
        #~ self.data = merge_configs(self.data, self.create_forecast_section())
        self.data = merge_configs(self.data, generation_data)
        self.data = merge_configs(self.data, sales_data)
        self.data = merge_configs(self.data, 
            self.process_diesel_powerhouse_data() )
            
        ## caclulate 'electric non-fuel prices'
        efficiency = self.data['community']['diesel generation efficiency']
        percent_diesel = \
            self.data['community']['utility info']['generation diesel'].fillna(0)\
            /self.data['community']['utility info']['net generation']
        percent_diesel = float(percent_diesel.iloc[-1])
        
        adder = percent_diesel * \
            self.data['community']['diesel prices'] / efficiency
        adder = adder.fillna(0)
        
        
        self.data['community']['electric non-fuel prices'] = \
            self.data['community']['electric non-fuel price'] + adder
            
        self.data = merge_configs(self.data,
            {'community': {'precent diesel generation': percent_diesel}})
            
            
        import aaem.components.non_residential.preprocessing as test
        reload(test)
        
        self.data = merge_configs(self.data, 
            self.preprocess_component(test, population=100)
        )
        #~ print self.data
        return self.data
            
            
    def save_config (self, out_dir):
        """ Function doc """
        
        community = self.community.replace(' ', '_').replace("'", '')
        if self.process_intertie == True:
            community += '_intertie'
        
        out_path = os.path.join(out_dir, community+'.yaml')
        save_config(out_path,
            self.data,
            comments = {},
            s_order = ['community', 'Non-residential Energy Efficiency'],
            i_orders = {
                'community': [
                    'name',
                    'alternate name',
                    'region',
                    'GNIS ID',
                    'FIPS ID',
                    'senate district',
                    'house district',
                    
                    'population',
                    'intertie',
                    'heating degree days',
                    'heating fuel premium',
                    'on road system',
                    
                    'diesel prices',
                    'electric non-fuel prices',
                    
                    'residential non-PCE electric price',
                    'electric non-fuel price',
                    'propane price',
                    'cordwood price',
                    'pellet price',
                    'natural gas price',
                    
                    'hydro generation limit',
                    'solar generation limit',
                    'wind generation limit',
                    'hydro capacity',
                    'solar capacity',
                    'wind capacity',
                    
                    "utility info",
                    "precent diesel generation",
                    "line losses",
                    "diesel generation efficiency",
                    
                    'heat recovery operational',
                    'switchgear suatable for renewables',
                
                ],

                'Non-residential Energy Efficiency': [
                    'enabled',
                    'start year',
                    'lifetime',
                    'average refit cost',
                    'cohort savings multiplier',
                    'heating cost percent',
                    'waste oil cost percent',
                    
                    'number buildings',
                    'consumption estimates',
                    'building inventory'
                ]
            }
        )
        
        
        
        
        
        
        

        
    def preprocess_component ( self, component, **kwargs):
        """
        """
        data = component.preprocess(self.community, self.data_dir, self.diagnostics, **kwargs)
        return data
        
        
    def load_ids (self, datafile, communities):
        """get a communities id information
        """
        data = read_csv(datafile, comment = '#')
        id_cols = [c for c in data.columns if c != 'Energy Region']
        ids = data[data[id_cols].isin(self.intertie).any(axis=1)]
        if len(ids) != len(communities):
            print ids, communities
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
        
        senate, house = self.load_election_divisions()
        
        if self.intertie_status != "not in intertie":
            intertie = self.communities 
        else:
            intertie = "not in intertie"
            
        population = self.load_population(**kwargs)
        data = {
            'community': {
                'model electricity': True,
                'file id': self.community,
                
            
                'name': self.community,
                'alternate name': self.aliases[0],
                'region': self.regions[0],
                'GNIS ID': self.GNIS_ids[0],
                'FIPS ID': self.FIPS_ids[0],
                'senate district': senate,
                'house district': house,
                'intertie': intertie,
                
                'population':population,
                
                'heating degree days': self.load_heating_degree_days(),
                'heating fuel premium': self.load_heating_fuel_premium(),
                'on road system': self.load_road_system_status(),
                
                'max wind generation precent': 20,
                
            },
        }
        
        data = merge_configs(data, self.process_renewable_capacities())
        return data
        
        
    #~ def create_forecast_section (self, **kwargs):
        #~ """create forecast section
        
        #~ Returns
        #~ -------
        #~ dict: 
            #~ the forecast section of a confinguration object 
        #~ """
        #~ population = self.load_population(**kwargs)
        #~ data = {
            #~ 'forecast': {
                #~ 'population':population
            #~ }
        #~ }
        
        #~ return data
        
        
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
        
        if not self.process_intertie:
            ids = [ids[0]]
        #~ ids = [ids[0]]
       
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
        
        
        
        ### TODO fix weird cases
        # "Klukwan": [["Klukwan","Chilkat Valley"]]
            
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
                if self.intertie_status in ['parent', 'not in intertie']:
                    ids = [self.communities[0], self.aliases[0]]
                else:
                    ## name and ailias of first child (community of interest)
                    ids = [self.communities[1], self.aliases[1]]
        ## cleanup ids
        ids = [i for i in ids if i != ""]
        
        ## Klukwan fix - see not at top of function
        if 'Klukwan' in ids:
            ids += ["Chilkat Valley"]    
        
        ## get data
        data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
        
        # filter out 'Purchased Power' from child communities as they
        # buy it from the parent so its counted there
        if self.process_intertie:
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
        if not self.process_intertie:
            ids = [self.communities[0], self.aliases[0]]
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
        """
        """
        ### read kwargs
        phc_percent = kwargs['power_house_consumption_percet'] if \
            'power_house_consumption_percet' in kwargs else .03
        
        data = pce_data[[
            "year","month","diesel_kwh_generated", "powerhouse_consumption_kwh",
            "hydro_kwh_generated", "other_1_kwh_generated", "other_1_kwh_type",
            "other_2_kwh_generated", "other_2_kwh_type", 'purchased_from',
            'kwh_purchased', "fuel_used_gal", "residential_kwh_sold",
            "commercial_kwh_sold", "community_kwh_sold", "government_kwh_sold",
            "unbilled_kwh", "residential_rate", "fuel_price"
        ]]
        
        ### NOTE: folowing code block (commented) is not nessary at this time
        ### but would become required if more that one type of 
        ### pruchaded power is provided to a comunity / intertie
        #~ purchase_sources = sorted(set(
            #~ data[data['purchased_from'].notnull()]["purchased_from"].values
        #~ ))
        #~ ### DO we need this note
        #~ self.diagnostics.add_note("Community: generation(PCE)",
                #~ "Utility list for purchased power " + str(sources)
        #~ )
        ### -- End
        
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
            msg = ("At this point it is assumed that all power is purchased "
                "from one source type. This may not be the case in the future " 
                "and code for handleing it should be written"
            )
            raise PreprocessorError, msg
        
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
            other_type_2 = other_type_2.lower()
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
            
            
            
            ## add generation from purchases
            if not purchase_type is None:
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
            "consumption non-residential","kwh_purchased","residential_rate",
            "diesel_price","generation diesel","generation hydro",
            "generation natural gas","generation wind","generation solar",
            "generation biomass"]
        processed_data = DataFrame(data_by_year)[columns]
        
        return processed_data
        
    def load_eia (self, **kwargs):
        """"""
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
        print ids
        
        
        generation = read_csv(datafile_generation, comment = '#', index_col=3)
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
        """
        """
        if 'pce_data' in kwargs:
            process_function = self.helper_pce_prices
            data = kwargs['pce_data']
        elif 'eia_sales' in kwargs:
            process_function = self.helper_eia_prices
            data = kwargs['eia_sales']
        else:
            raise PreprocessorError, "No electric price data avaialbe"
            
        res_nonPCE_price, elec_nonFuel_cost = process_function(data)
        
        ## TODO change these name in other code
        return {
            'community': {
                'residential non-PCE electric price' :  res_nonPCE_price, # was res non-PCE elec cost 
                'electric non-fuel price': elec_nonFuel_cost, # was elec non-fuel cost
            }
        }
        
    def helper_eia_generation(self, eia_generation, eia_sales, **kwargs):
        """
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
            "generation biomass"]
        processed_data = DataFrame(data_by_year)[columns]
        
        return processed_data
        
    def helper_yearly_electric_data (self, **kwargs):
        """ Function doc """
        #~ print kwargs.keys()
        if 'pce_data' in kwargs:
            data = self.helper_pce_generation(kwargs['pce_data'])
        elif 'eia_generation' in kwargs and 'eia_sales' in kwargs:
            data = self.helper_eia_generation (
                kwargs['eia_generation'], 
                kwargs['eia_sales'] )
        else:
            raise PreprocessorError, "No generation data avaialbe"
        return data
        
    def process_generation (self, **kwargs):
        """
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
        """
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
        
        default_efficiency = kwargs['default_diesl_efficieny']\
            if 'default_diesl_efficieny' in kwargs else 12
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
            'efficiency'
        ]]
        generation.index = generation.index.astype(int)
        return generation.round(3)
        
        
    def load_heating_degree_days (self, **kwargs):
        """ Function doc """
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
        """
        """
        datafile = os.path.join(self.data_dir,"heating_fuel_premium.csv")
        data = read_csv(datafile, index_col=0, comment='#')
        
        ids = self.regions[0].replace(' Region','') 
        if self.intertie_status == 'child':
            ids = self.regions[1].replace(' Region','') 
        
        premium = float(data.ix[ids])
        
        return premium 
        
    def load_election_divisions (self, **kwargs):
        """
        """
        datafile = os.path.join(self.data_dir,'election-divisions.csv')
        data = read_csv(datafile, index_col=0, comment='#')
        data.index = [i.replace(' (part)','') for i in data.index]
        
        ## make it a list index to make all acesses return same format
        senate = data.ix[[self.community]]['Senate'].values.tolist()
        house = data.ix[[self.community]]['House District'].values.tolist()
        return senate, house
    
    def load_road_system_status (self, **kwargs):
        """
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
        """
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
        data = self.load_diesel_powerhouse_data()
        
        hr_operational = data['Waste Heat Recovery Opperational'].values[0]
        hr_operational = True if hr_operational.lower() == 'yes' else False
        switchgear_status = data['Switchgear Suitable'].values[0]
        switchgear_status = True if  switchgear_status.lower() == 'yes' \
            else False
            
        return {
            'community': {
                'heat recovery operational': hr_operational,
                'switchgear suatable for renewables': switchgear_status,
            }
        }
        
    def load_fuel_prices (self, **kwargs):
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
        prices_diesel = data.ix[ids][data.ix[ids].isnull().all(1) == False].T
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
        
    
    def helper_fuel_prices (self, ** kwargs):
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
        
        
        electric_prices = self.helper_electric_prices(**kwargs)
        fuel_prices = self.helper_fuel_prices()
        electric_non_fuel_prices = None
        
        
        data = merge_configs(electric_prices, fuel_prices)
        data['community']['electric non-fuel prices'] = electric_non_fuel_prices
        return data
        
        
        
        
    def load_renewable_capacities (self, **kwargs):
        
        datafile = os.path.join(self.data_dir, 
            'renewable_generation_capacities.csv')

        data = read_csv(datafile, comment = '#', index_col = 0)[
            ['Resource Type','Resource Sub-Type',
            'Capacity (kW)','Average Expected Annual Generation (kWh)']
        ]

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
        """
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
                hydro_capacity = data.ix['Solar']['Capacity (kW)']
                hydro_generation = \
                    data.ix['Solar']['Average Expected Annual Generation (kWh)']
            except KeyError:
                self.diagnostics.add_note('Community: Renewable Capacities',
                    'No solar data found. Values have been set to 0')
            
            ## wind
            try:
                hydro_capacity = data.ix['wind']['Capacity (kW)']
                hydro_generation = \
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
        
        
        
    
        
        
        
        
        
