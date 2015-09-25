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

# TODO: this is for manley, but I'm not sure where it comes from
fossil_fuel_gen_displaced = [395674.849879193,418138.515848389,441877.512531502,
                             466964.244336258,493475.226289067,521491.317407356,
                             551097.967321171,582385.476896231,615449.273653346,
                             650390.202824239,687314.83493149,726335.790830729,
                             767572.085206463,811149.489569216,857200.915861106,
                             905866.821839895,957295.639477916,1011644.22768251,
                             1069078.3507188,1129773.18379393,1193913.84734495,
                             0.0,0.0,0.0] # extra zeros 
fossil_fuel_gen_displaced = np.array(fossil_fuel_gen_displaced)


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
        self.forecast_consumption()
        print len(np.array(self.consumption))
        return np.array(self.consumption)
        #~ return self.ff_gen_displaced[start-self.start_year:end-self.start_year]
    
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
            #~ return self.trends[key]
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
            y = self.electricty_totals #kWh
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
        self.electricty_totals = np.nansum([kWh['residential'],
                                            kWh['community'],
                                            kWh['commercial'],
                                            kWh['gov'],
                                            kWh['unbilled']
                                            ],0)
    
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
            
    def forecast_consumption (self):
        """
        pre:
            tbd.
        post:
            self.consumption is a array of estimated kWh consumption for each 
        year between start and end
        """
        trend = self.get_trend('total')
        self.consumption = []
        pre = self.electricty_totals[-2]*2 # TD: update
        for year in range(self.start_year,self.end_year+1):
            cur = trend*pre
            pre = cur
            self.consumption.append(cur)
            
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

def test ():
    """ Function doc """
    fc = Forecast(manley_data)
    return fc
