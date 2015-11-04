"""
forecast.py
Ross Spicer
created: 2015/09/18

    forecast
"""
import numpy as np
from community_data import CommunityData


from scipy.optimize import curve_fit
from pandas import DataFrame, read_csv, concat
import os.path

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
        self.fc_specs = self.cd.get_section('forecast')
        self.start_year = self.fc_specs["start year"]
        self.end_year = self.fc_specs["end year"]
        self.electricty_actuals =\
                        read_csv(os.path.abspath(self.fc_specs["input"]),
                        index_col = 0)
        self.base_pop = self.electricty_actuals['population']\
                        [self.fc_specs["base year"]]
    
    def get_trend (self, key):
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
            y = self.electricty_actuals[key]
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
        kWh = self.fc_specs["electricity"]
        years = kWh.T.keys().values
        totals = np.nansum([kWh['residential'].values,
                                            kWh['community'].values,
                                            kWh['commercial'].values,
                                            kWh['government'].values,
                                            kWh['unbilled'].values,
                                            kWh['industrial'].values
                                            ],0)
        self.yearly_kWh_totals = DataFrame({"year":years,
                                        "total":totals}).set_index("year")

    def forecast_population (self):
        """
        pre:
            tbd.
        post:
            self.population is a array of estimated populations for each 
        year between start and end
        """
        if len(self.fc_specs["population"]) < 10:
            print "warning: forecast: "\
                  "the data range is < 10 for input population "\
                  "check population.csv in the models data directory"
        
        population = self.fc_specs["population"].T.values.astype(float)
        years = self.fc_specs["population"].T.keys().values.astype(int)
        new_years = np.array(range(years[-1]+1,self.end_year+1))
        self.population = DataFrame({"year":new_years, 
             "population":growth(years,population,new_years)}).set_index("year")
        #~ trend = self.get_trend('population')
        #~ self.population = []
        #~ idx = -1
        #~ while np.isnan(self.electricty_actuals['population'].values[idx]):
            #~ idx -= 1
        #~ pop_pre = self.electricty_actuals['population'].values[idx]
        #~ for year in range(self.start_year,self.end_year+1):
            #~ pop = trend*pop_pre
            #~ pop_pre = pop
            #~ self.population.append(pop)
        #~ self.population = np.array(self.population)
        
    def forecast_consumption (self):
        """
        pre:
            tbd.
        post:
            self.consumption is a array of estimated kWh consumption for each 
        year between start and end
        """
        self.calc_electricity_totals()
        
        if len(self.yearly_kWh_totals) < 10:
            print "warning: forecast: "\
                  "the data range is < 10 for input consumption "\
                  "check electricity.csv in the models data directory"
        ### for fit version
        #~ start = self.fc_specs["population"].T.keys().values[0] \
                #~ if self.fc_specs["population"].T.keys().values[0] > \
                #~ self.yearly_kWh_totals.T.keys().values[0] \
                #~ else self.yearly_kWh_totals.T.keys().values[0]
        
        #~ end = self.fc_specs["population"].T.keys().values[-1] \
                #~ if self.fc_specs["population"].T.keys().values[-1] < \
                #~ self.yearly_kWh_totals.T.keys().values[-1] \
                #~ else self.yearly_kWh_totals.T.keys().values[-1]
        
        #~ population = self.fc_specs["population"].ix[start:end].T.values[0]
        #~ consumption = self.yearly_kWh_totals[start:end].T.values[0]
        #~ if len(population) < 10:
            #~ print "warning: forecast: "\
                  #~ "the data range is < 10 matching years for "\
                  #~ "population and consumption "\
                  #~ "check population.csv and electricity.csv "\
                  #~ "in the models data directory"
        
        last_year = int(self.yearly_kWh_totals.T.keys()[-1])
        
        ### for last year version
        last_consumption = self.yearly_kWh_totals.ix[last_year].values[0]
        last_population = self.fc_specs["population"].ix[last_year].values[0]
        
        
        year = last_year + 1 
        fc_con_known_pop = []
        while year <= self.end_year:
            try: 
                pop = self.fc_specs["population"].ix[year].values[0]
            except KeyError:
                break
            fc_con_known_pop.append(last_consumption * pop / last_population)
            year +=1 
            
        fc_con_fc_pop = last_consumption * \
                    self.population.T.values[0] / last_population
        consumption = fc_con_known_pop + fc_con_fc_pop.tolist()
        
        self.consumption = DataFrame({'year':range(last_year+1,self.end_year+1),
                            'consumption kWh':consumption}).set_index('year')
        
        
        #~ trend = self.get_trend('total')
        #~ self.consumption = np.zeros(len(self.population))
        #~ self.calc_electricity_totals()
        #~ idx = -1
        #~ while np.isnan(self.electricity_totals[idx]):
            #~ idx -= 1

        #~ last_con = self.electricity_totals[idx] 
        #~ idx = -1
        #~ while np.isnan(self.electricty_actuals['population'].values[idx]):
            #~ idx -= 1
        #~ last_pop = self.electricty_actuals['population'].values[idx]
        #~ self.consumption = last_con * self.population/ last_pop
      
    def forecast_generation (self):
        """
        pre:
            tbd.
            self.consumption should be a float array of kWh/yr values
        post:
            self.generation is a array of estimated kWh generation for each 
        year between start and end
        """
        generation = self.consumption/\
                    (1.0-self.cd.get_item('community','line losses'))
        self.generation = generation.apply(np.round, args=(-3,))
        
        self.generation["kWh generation"] = self.generation["consumption kWh"]
        del(self.generation["consumption kWh"])
        
    def forecast_average_kW (self):
        """
        ???
        """
        self.average_kW = (self.consumption/ 8760.0)\
                                /(1-self.cd.get_item('community','line losses'))
        
        self.average_kW["avg. kW"] = self.average_kW["consumption kWh"]
        del(self.average_kW["consumption kWh"])
        
    def forecast_households (self):
        """
        forcast # of houselholds
        """
        peps_per_house = float(self.base_pop) / \
    self.cd.get_item('residential buildings','res model data')['total_occupied']
        self.households = np.round(self.population / peps_per_house, 0)
        
        self.households["HH"] = self.households["population"]
        del(self.households["population"])
        
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
    
    def get_consumption (self, start, end = None):
        """
        get consumption values from the consumption forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        get_pop = self.get_con_range
        if end is None:
            get_pop = self.get_con_val
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

    def get_generation (self, start, end = None):
        """
        get population values from the population forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        get_gen = self.get_gen_range
        if end is None:
            get_gen = self.get_gen_val
        try:
            return get_gen(start,end)
        except AttributeError:
            self.forecast_population()
            self.forecast_consumption()
            self.forecast_generation()
        return get_gen(start,end)
    
    def get_gen_range (self, start, end):
        """
        get generation list from the generation forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end is a year where start <= end < self.end_year
        post:
            returns a list of floats
        """
        return self.generation[start-self.start_year:end-self.start_year]
    
    def get_gen_val (self, start, end):
        """
        get generation values from the generation forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end is not used, but is here for consistency with get_pop_range
        post:
            returns a float 
        """
        return self.generation[start-self.start_year]

    def get_households (self, start, end = None):
        """
        get households values from the households forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        get_pop = self.get_hh_range
        if end is None:
            get_pop = self.get_hh_val
        try:
            return get_pop(start,end)
        except AttributeError:
            self.forecast_population()
            self.forecast_households()
            
        return get_pop(start,end)
    
    def get_hh_range (self, start, end):
        """
        get households list from the households forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end is a year where start <= end < self.end_year
        post:
            returns a list of floats
        """
        return self.households[start-self.start_year:end-self.start_year]
    
    def get_hh_val (self, start, end):
        """
        get households values from the households forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end is not used, but is here for consistency with get_pop_range
        post:
            returns a float 
        """
        return self.households[start-self.start_year]

    def set_res_HF_fuel_forecast (self, fc, start_year):
        """
        set the residential HF consumption forecast
        
        pre: 
        """
        start_pad = np.zeros(start_year - self.start_year)
        end_pad = np.zeros(self.end_year - (start_year + len(fc))+1) + fc[-1]
        self.res_HF = np.append(np.append(start_pad, fc), end_pad)
    
    def set_com_HF_fuel_forecast (self, fc, start_year):
        """
        set the residential HF consumption forecast
        
        pre: 
        """
        start_pad = np.zeros(start_year - self.start_year)
        end_pad = np.zeros(self.end_year - (start_year + len(fc))+1) + fc[-1]
        self.com_HF = np.append(np.append(start_pad, fc), end_pad)
        
    def set_www_HF_fuel_forecast (self, fc, start_year):
        """
        set the residential HF consumption forecast
        
        pre: 
        """
        start_pad = np.zeros(start_year - self.start_year)
        end_pad = np.zeros(self.end_year - (start_year + len(fc) )+1) + fc[-1]
        self.www_HF = np.append(np.append(start_pad, fc), end_pad)
        
    def calc_total_HF_forecast(self):
        try:
            r = self.res_HF
        except AttributeError:
            r = np.array([])
            years = (self.end_year - np.arange(len(r)))[::-1]
            self.res_HF = DataFrame({'year': years,
                                   'consumption': r}).set_index('year')
        try:
            c = self.com_HF 
        except AttributeError:
            c = np.array([])
            years = (self.end_year - np.arange(len(c)))[::-1]
            self.com_HF = DataFrame({'year': years,
                                   'consumption': c}).set_index('year')
        try:
            w = self.www_HF
        except AttributeError:
            w = np.array([])
            years = (self.end_year - np.arange(len(w)))[::-1]
            self.www_HF = DataFrame({'year': years,
                                   'consumption': w}).set_index('year')
        
        
        self.total_HF = self.res_HF + self.com_HF + self.www_HF
        
        self.res_HF["res HF"] = self.res_HF["consumption"]
        del(self.res_HF["consumption"])
        self.com_HF["com HF"] = self.com_HF["consumption"]
        del(self.com_HF["consumption"])
        self.www_HF["ww HF"] = self.www_HF["consumption"]
        del(self.www_HF["consumption"])
        self.total_HF["total HF"] = self.total_HF["consumption"]
        del(self.total_HF["consumption"])
        
    def save_forecast (self, path):
        """
        save the forecast to a csv
        pre:
            everything needs to be foretasted
        post:
            saves a file
        """
        df = concat([self.population.T, self.households.T, self.consumption.T,
                     self.generation.T, self.average_kW.T, self.res_HF.T,
                     self.com_HF.T, self.www_HF.T, self.total_HF.T]).T
        
        #~ return df
        #~ df = DataFrame( {"pop": self.population,
                     #~ "HH" : self.households,
                     #~ "kWh consumed" : self.consumption,
                     #~ "kWh generation": self.generation,
                     #~ "avg. kW": self.average_kW,
                     #~ "res HF": self.res_HF,
                     #~ "com HF": self.com_HF,
                     #~ "ww HF": self.www_HF,
                     #~ "total HF": self.total_HF,}, 
              #~ np.array(range(len(self.population))) + self.start_year)
        df.to_csv(path, index_label="year")
        
        

def test ():
    """ Function doc """
    manley_data = CommunityData("../data/", "../test_case/manley_data.yaml")
    
                            
    fc = Forecast(manley_data)
    fc.calc_electricity_totals()
    fc.forecast_population()
    fc.forecast_consumption()
    fc.forecast_generation()
    fc.forecast_average_kW()
    fc.forecast_households()
    return fc
