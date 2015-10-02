"""
forecast.py
Ross Spicer
created: 2015/09/18

    mock up of for cast tab
"""
import numpy as np
#~ from community_data import manley_data
import community_data
reload(community_data)
manley_data = community_data.manley_data

from scipy.optimize import curve_fit

class Forecast (object):
    """ Class doc """
    
    def __init__ (self, community_data):
        """
        pre:
            self.cd is a community_data instance. 
        post:
            self.start_year < self.end_year are years(ints) 
            self.cd is a community_data instance. 
        """
        self.cd = community_data
        self.start_year = self.cd["fc_start_year"]
        self.end_year = self.cd["fc_end_year"]
        #~ self.ff_gen_displaced = fossil_fuel_gen_displaced
        
    def get_fossil_fuel_generation_displaced (self, start, end):
        """
        TODO: this function will probably go away
        """
        self.forecast_population()
        self.forecast_consumption()
        #~ print len(np.array(self.consumption))
        return np.array(self.consumption)
    
    def get_trend (self, key ):
        """
        pre:
            key should be a string{'years'|'population'|'community'|
                                   'residential','gov',commercial'|
                                   'unbilled'|'total'}
            'fc_electricity_used' should contain the kWh used for each key type
            except 'total'
        post:
            a trend rate is returned 
        """
        try:
            e = self.trends[key]
            return e
        except AttributeError:
            self.trends = {} 
        except KeyError:
            pass
        
        try:
            y = self.cd['fc_electricity_used'][key]
        except KeyError as e:
            if key != "total":
                raise
            self.calc_electricity_totals()
            y = self.electricity_totals #kWh
        y = y[:-2] # TODO: Replace when model is updated
        x = range(len(y))
        
        def f (x,m,b):
            """ this is the functin for curve fit"""
            return b*(m**x)
        self.trends[key] = curve_fit(f,np.array(x)*1.101,y)[0][0]
        return self.trends[key]

    def calc_electricity_totals (self):
        """ 
        pre:
            'fc_electricity_used' should contain the kWh used for each key type
        post:
            self.electricty_totals is a array of yearly values of total kWh used
        """
        kWh = self.cd['fc_electricity_used']
        self.electricity_totals = np.nansum([kWh['residential'],
                                            kWh['community'],
                                            kWh['commercial'],
                                            kWh['gov'],
                                            kWh['unbilled']
                                            ],0)
    
    def get_population (self, start, end = None):
        """
        get population values from the population forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        get_pop = self.get_pop_range
        if end is None:
            get_pop = self.get_pop_val
        try:
            return get_pop(start,end)
        except AttributeError:
            self.forecast_population()
        return get_pop(start,end)
    
    def get_pop_range (self, start, end):
        """
        get population list from the population forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end is a year where start <= end < self.end_year
        post:
            returns a list of floats
        """
        return self.population[start-self.start_year:end-self.start_year]
    
    def get_pop_val (self, start, end):
        """
        get population values from the population forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end is not used, but is here for consistency with get_pop_range
        post:
            returns a float 
        """
        return self.population[start-self.start_year]
    
    def forecast_population (self):
        """
        pre:
            tbd.
        post:
            self.population is a array of estimated populations for each 
        year between start and end
        """
        trend = self.get_trend('population')
        self.population = []
        pop_pre = self.cd['fc_electricity_used']['population'][-3] # TD: update
        for year in range(self.start_year,self.end_year+1):
            pop = trend*pop_pre
            pop_pre = pop
            self.population.append(pop)
        self.population = np.array(self.population)
        
        
    def forecast_consumption (self):
        """
        pre:
            tbd.
        post:
            self.consumption is a array of estimated kWh consumption for each 
        year between start and end
        """
        #~ trend = self.get_trend('total')
        #~ self.consumption = np.zeros(len(self.population))
        self.calc_electricity_totals()
        base_con = self.electricity_totals[-2]*2 # TD: update
        base_pop = self.cd['fc_electricity_used']['population'][-3]
        self.consumption = base_con * self.population/ base_pop
        
    def get_consumption (self, start, end = None):
        """
        get consumption values from the consumption forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        get_pop = self.get_pop_range
        if end is None:
            get_pop = self.get_pop_val
        try:
            return get_pop(start,end)
        except AttributeError:
            self.forecast_population()
            self.forecast_consumption()
            
        return get_pop(start,end)
    
    def get_con_range (self, start, end):
        """
        get consumption list from the consumption forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end is a year where start <= end < self.end_year
        post:
            returns a list of floats
        """
        return self.consumption[start-self.start_year:end-self.start_year]
    
    def get_con_val (self, start, end):
        """
        get consumption values from the consumption forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end is not used, but is here for consistency with get_pop_range
        post:
            returns a float 
        """
        return self.consumption[start-self.start_year]
            
    def forecast_generation (self):
        """
        pre:
            tbd.
            self.consumption should be a float array of kWh/yr values
        post:
            self.generation is a array of estimated kWh generation for each 
        year between start and end
        """
        self.generation = np.array(self.consumption)/\
                                (1.0-self.cd['line_losses'])
        self.generation = np.round(self.generation,-3) # round to nears thousand
        
    def forecast_average_kW (self):
        """
        ???
        """
        self.average_kW = (np.array(self.consumption)/ 8760.0)\
                                         /(1-self.cd['line_losses']) 
        #~ self.average_kW = np.round(self.generation,-3) # round to nears thousand
        
    def forecast_households (self):
        """
        forcast # of houselholds
        """
        peps_per_house = float(self.cd["population"]) / self.cd["households"]
        #~ print peps_per_house
        self.households = np.round(self.population / peps_per_house, 0)
        
        

def test ():
    """ Function doc """
    fc = Forecast(manley_data)
    fc.calc_electricity_totals()
    fc.forecast_population()
    fc.forecast_consumption()
    fc.forecast_generation()
    fc.forecast_average_kW()
    fc.forecast_households()
    return fc
