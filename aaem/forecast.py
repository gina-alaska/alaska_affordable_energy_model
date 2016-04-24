"""
forecast.py
Ross Spicer
created: 2015/09/18

    forecast
"""
from community_data import CommunityData
from diagnostics import diagnostics
import constants
import plot
import colors

import numpy as np
from pandas import DataFrame, read_csv, concat
import os.path
import copy

from datetime import datetime


class Forecast (object):
    """ Class doc """
    
    def __init__ (self, community_data, diag = None):
        """
        pre:
            self.cd is a community_data instance. 
        post:
            self.start_year < self.end_year are years(ints) 
            self.cd is a community_data instance. 
        """
        self.diagnostics = diag
        if self.diagnostics == None:
            self.diagnostics = diagnostics()
        self.cd = community_data
        self.fc_specs = self.cd.get_section('forecast')
        self.start_year = self.fc_specs["end year"]
        self.end_year = self.fc_specs["end year"]
        
        yr = self.cd.get_item('residential buildings', 'data').ix['year']
        self.base_pop = self.fc_specs['population'].ix[yr].values[0][0]
        
        self.forecast_population()
        
        
        if self.cd.get_item("community","model electricity") is False:
            self.base_res_consumption = None
            self.base_non_res_consumption = None
            self.base_total_consumption = None
        else:
            kWh = self.fc_specs["electricity"]
            self.base_res_consumption = \
                float(kWh['consumption residential'].ix[yr])
            self.base_non_res_consumption = \
                float(kWh['consumption non-residential'].ix[yr])
            self.base_total_consumption = float(kWh['consumption'].ix[yr])
            self.forecast_consumption()
            self.forecast_generation()
            try:
                self.forecast_generation_by_type()
            except IndexError:
                pass
            self.forecast_average_kW()
        
        self.cpi = self.cd.load_pp_csv("cpi.csv")
        self.forecast_households()
        self.heat_demand_cols = []
        self.heating_fuel_cols = [] 
        self.electric_columns = []
        

    def calc_electricity_values (self):
        """ 
        pre:
            'fc_electricity_used' should contain the kWh used for each key type
        post:
            self.electricty_totals is a array of yearly values of total kWh used
        """
        kWh = self.fc_specs["electricity"]
        #~ print kWh
        years = kWh.T.keys().values
        self.yearly_res_kWh = DataFrame({"year":years,
                          "total":kWh['consumption residential'].values}).set_index("year")
        self.yearly_total_kWh = DataFrame({"year":years,
                          "total":kWh['consumption'].values}).set_index("year")
        self.average_nr_kWh = kWh['consumption non-residential'].values[-3:].mean()
        self.yearly_nr_kWh = DataFrame({"year":years,
                          "total":kWh['consumption non-residential'].values}).set_index("year")
        #~ print self.average_nr_kWh


    def forecast_population (self):
        """
        pre:
            tbd.
        post:
            self.population is a array of estimated populations for each 
        year between start and end
        """
        # pop forecast is preprocessed now
        self.p_map = DataFrame(self.fc_specs["population"]\
                                            ["population_qualifier"])
        self.population = DataFrame(self.fc_specs["population"]["population"])
        if len(self.p_map[self.p_map == "M"] ) < 10:
            msg = "the data range is < 10 for input population "\
                  "check population.csv in the models data directory"
            self.diagnostics.add_warning("forecast", msg)
        
        
    def forecast_consumption (self):
        """
        pre:
            tbd.
        post:
            self.consumption is a array of estimated kWh consumption for each 
        year between start and end
        """
        self.calc_electricity_values()
        idx =  self.yearly_res_kWh.index.values.astype(int).tolist()

        if len(self.yearly_res_kWh) < 10:
            msg = "the data range is < 10 for input consumption "\
                  "check electricity.csv in the models data directory"
            self.diagnostics.add_warning("forecast", msg)
        population = self.population.ix[idx]
        if any(population.isnull()):
            v= population.isnull().values.T.tolist()[0]
            for year in population[v].index.values.tolist():
                idx.remove(year)
        
        if any(self.yearly_res_kWh.isnull()):
            v = self.yearly_res_kWh.isnull().values.T.tolist()[0]
            for year in self.yearly_res_kWh[v].index.values.tolist():
                idx.remove(year)
        
        self.diagnostics.add_note("forecast", 
           "years with measured consumption and population " + str(idx) +\
        ". List used to generate fit function")
        population = self.population.ix[idx]
        population = self.population.ix[idx].T.values[0]
        self.measured_consumption = self.yearly_total_kWh.ix[idx] 
        consumption = self.yearly_res_kWh.ix[idx].T.values[0]
        if len(population) < 10:
            self.diagnostics.add_warning("forecast", 
                  "the data range is < 10 matching years for "\
                  "population and consumption "\
                  "check population.csv and electricity.csv "\
                  "in the models data directory")
        # get slope(m),intercept(b)
        #~ print population
        #~ print consumption
        try:
            m, b = np.polyfit(population,consumption,1) 
        except TypeError:
            raise RuntimeError, "Known population & consumption do not overlap"
        
        fc_consumption = (m * self.population + b) + self.average_nr_kWh

        start = int(self.measured_consumption.index[-1] + 1)
        years= idx +self.population.ix[start:].index.values.astype(int).tolist()
        cons = (consumption-consumption).tolist() + \
                                  fc_consumption.ix[start:].T.values[0].tolist()
                                  
        self.c_map = DataFrame({'year':years, 'consumption': cons}).\
                                                        set_index('year').\
                                                        astype(bool).\
                                                        astype(str).\
                                                        replace("True", "P").\
                                                        replace("False", "M")   
        self.c_map.columns  = [self.c_map.columns[0] + "_qualifier"]
        
        cons = self.measured_consumption.T.values.tolist()[0] +\
                                fc_consumption.ix[start:].values.T.tolist()[0]
        
        nr = np.zeros(len(fc_consumption.ix[start:])-1) + self.average_nr_kWh
        r = (m * self.population + b).ix[start:]
        
        r =  self.yearly_res_kWh.ix[idx].T.values.tolist()[0] + \
             r.values.T.tolist()[0]
        
        nr = self.yearly_nr_kWh.ix[idx].T.values.tolist()[0] + nr.tolist() 
        
        if len(nr) < len(r):
            nr.append(self.average_nr_kWh)
        if len(nr) > len(r):
            nr = nr[:-1]
        consumption = DataFrame({'year':years, 
                                 'consumption': cons, 
                                 'res': r,
                                 'non res' : nr}).set_index('year')
        consumption = consumption[["consumption", 'res', 'non res']]
        consumption.columns = ["consumption kWh", 
                               'residential kWh',
                               'non-residential kWh']
        self.consumption_to_save = consumption
        
        self.consumption = DataFrame({'year':years, 
                                 'consumption': cons, }).set_index('year')
        self.consumption.columns = ["consumption kWh"]
        self.consumption.index = self.consumption.index.values.astype(int)
        self.start_year = int(self.yearly_res_kWh.T.keys()[-1])
        
    def forecast_generation (self):
        """
        forecast generation
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
        
        
        try:
            real = self.cd.get_item('community',"generation").ix[2003:]
            idx = real.index.values.tolist()
            df = DataFrame(real.ix[idx])
            df.columns = ['consumption kWh']
            
            nas = [] 
            for i in idx:
                if np.isnan(float(df.ix[i])):
                    nas.append(i)
            idx = set(idx).difference(nas)
            
            self.generation.ix[idx] = df.ix[idx]
        except:
            pass
    
        self.generation.columns = ["kWh generation"]
            
    def forecast_generation_by_type (self):
        """
        forecasts the generation by each fuel type
        
        pre:
            self.generation is calculated
        post:
            self.generation_by_type is created and filled 
        """
        gen_types = self.cd.get_item('community','generation numbers')

        self.generation_by_type = copy.deepcopy(self.generation)
        self.generation_by_type.columns = ["generation total"]
        if (gen_types[['generation natural gas']].fillna(0) != 0).any().bool():
            msg = "natural gas is fuel used to make up difference" 
            self.diagnostics.add_note('forecast', msg) 
            current_type = 'generation natural gas'
            self.forecast_fuels(current_type)   
                
        else: 
            msg = "diesel is fuel used to make up difference" 
            self.diagnostics.add_note('forecast', msg) 
            current_type = 'generation diesel'
            self.forecast_fuels(current_type)  
        self.correct_generation()
    
    def correct_generation (self):
        """
            checks generation of RE fuels, and ensures they remain between the 
        total generation and the 0
        
        pre:
            self.generation_by_type should be populated with generation 
        values for each fuel type
        post:
            RE fuel types are 0 < fuel genneration < total generation, and
        sum(generation[each fuel]) == generation total
        """
        fuel_types = ['generation natural gas', 'generation diesel',
                  'generation hydro','generation wind','generation biomass']
        
        total = self.generation_by_type['generation total'].ix[self.start_year:] 
        
        
        for fuel in ['generation wind','generation hydro','generation biomass']:
            #~ if any(self.generation_by_type[fuel].ix[self.start_year:] <= 0):
                #~ continue
            fuel_sums = \
                self.generation_by_type[fuel_types].ix[self.start_year:].sum(1) 
            if any(total.ix[self.start_year:] < fuel_sums.ix[self.start_year:]):
                if any(total.ix[self.start_year:] < \
                        self.generation_by_type[fuel].ix[self.start_year:]):
                    msg = "scaling generation(" + fuel + ") where geneation(" + \
                            fuel + ") > total generation"
                    self.diagnostics.add_note('forecast', msg)   
                            
                    self.generation_by_type[fuel].ix[self.start_year:] = \
                            self.generation_by_type[fuel].ix[self.start_year:] -\
                            (fuel_sums - total.ix[self.start_year:])
                
                
        
            else:
                continue
            if any(self.generation_by_type[fuel].ix[self.start_year:] < 0):
                msg = "zeroing generation(" + fuel + ") where geneation < 0"
                self.diagnostics.add_note('forecast', msg)
            
            self.generation_by_type[fuel].ix[self.start_year:]\
            [self.generation_by_type[fuel].ix[self.start_year:] < 0 ] = 0

        
        
    def forecast_fuels (self, current_type):
        """
        forecast the consumption for each fuel
        
        pre:
            self.generation_by_type should be created but not yet populated
            current_type is "generation diesel" or "generation natural gas"
        post:
            self.generation_by_type will be populated
        """
        gen_types = self.cd.get_item('community','generation numbers')
        self.generation_by_type[current_type] = gen_types[current_type]
        
        fuel_types = gen_types.keys().values
        fuel_types = list(set(fuel_types).difference([current_type]))
        
        for fuel in fuel_types:
            rolling = False
            self.generation_by_type[fuel] = gen_types[fuel]
            try:
                # get the last 3 years of generation  and average them
                if fuel == 'generation hydro':
                    generation = self.cd.get_item('community',
                                                  'hydro generation limit')
                    if generation == 0:
                        temp = gen_types[gen_types[fuel].notnull()]\
                                                    [fuel].values[-3:]
                        temp = np.mean(temp)
                        if np.isnan(temp):
                            generation = 0
                        else:
                            msg = "generation(hydro) using rolling average"
                            self.diagnostics.add_note('forecast', msg)
                            rolling = True
                elif fuel == 'generation wind':
                    generation = self.cd.get_item('community',
                                                  'wind generation limit')
                    if generation == 0:
                        temp = gen_types[gen_types[fuel].notnull()]\
                                                    [fuel].values[-3:]
                        temp = np.mean(temp)
                        if np.isnan(temp):
                            generation = 0
                        else:
                            msg = "generation(wind) using rolling average"
                            self.diagnostics.add_note('forecast', msg)
                            rolling = True
                            
                else:
                    if current_type == "generation natural gas" and \
                            fuel == "generation diesel" \
                        or current_type == "generation diesel" and \
                            fuel == "generation natural gas":
                        continue
                    else:
                        generation = gen_types[gen_types[fuel].notnull()]\
                                                    [fuel].values[-3:]
                        generation = np.mean(generation)
                    msg = "generation("+ fuel +") is " + str(generation)
                    self.diagnostics.add_note('forecast', msg)
                    
                last_year = self.start_year
                foreward_years = np.logical_and(\
                            self.generation_by_type[fuel].isnull(), 
                            self.generation_by_type[fuel].index > last_year)
                if not rolling:
                    self.generation_by_type[fuel][foreward_years] = generation
                else:
                    for year in self.generation_by_type.ix[foreward_years].index:
                        data = self.generation_by_type[fuel].ix[year-3:year-1]
                        self.generation_by_type[fuel][year] = np.mean(data) 
            except IndexError as e:
                #~ print 'INDEXERROR',fuel, e
                # fuel not found
                pass
        
        last_year = self.start_year
        foreward_years = self.generation_by_type.index>last_year
        
        other_type_values = \
                self.generation_by_type[foreward_years ][fuel_types]
        other_type_values = other_type_values.fillna(0).sum(1)
        
        foreward_values = \
                self.generation_by_type[foreward_years ]['generation total']\
                - other_type_values
        
        if any(foreward_values < 0):
            msg = "zeroing generation("+ current_type +") where generation < 0"
            self.diagnostics.add_note('forecast', msg)
        foreward_values[foreward_values < 0] = 0
        
        self.generation_by_type.loc[foreward_years,current_type]=foreward_values
        
    def forecast_average_kW (self):
        """
        forecast the average kW used per community per year
        pre:
        post:
        """
        self.average_kW = (self.consumption/ 8760.0)\
                                /(1-self.cd.get_item('community','line losses'))
        
        self.average_kW.columns = ["avg. kW"]
        
    def forecast_households (self):
        """
        forcast # of houselholds
        pre:
        post:
        """
        peps_per_house = float(self.base_pop) / \
            self.cd.get_item('residential buildings','data').ix['total_occupied']
        self.households = np.round(self.population / np.float64(peps_per_house))
        self.households.columns = ["HH"] 
        
    def get_population (self, start, end = None):
        """
        get population values from the population forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        if end is None:
            return self.population.ix[start].T.values[0]
        return self.population.ix[start:end-1].T.values[0]
    
    def get_consumption (self, start, end = None):
        """
        get consumption values from the consumption forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        if end is None:
            return self.consumption.ix[start].T.values[0]
        return self.consumption.ix[start:end-1].T.values[0]

    def get_generation (self, start, end = None):
        """
        get population values from the population forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        if end is None:
            return self.generation.ix[start].T.values[0]
        return self.generation.ix[start:end-1].T.values[0]

    def get_households (self, start, end = None):
        """
        get households values from the households forecast. 
        
        pre:
            start is a year where start >= self.start_year
            end(if provided) is a year where start <= end < self.end_year
        post:
            returns a float or list of floats
        """
        if end is None:
            return self.households.ix[start].T.values[0]
        return self.households.ix[start:end-1].T.values[0]
        
    def save_forecast (self, path, png_path = None):
        """
        save the forecast to a csv
        pre:
            everything needs to be foretasted
            path: path to each communities output dir
            png_path: altenat location for pngs
        post:
            saves 3 files
        """
        tag = self.cd.get_item("community", "name").replace(" ", "_") + "_"
        pathrt = os.path.join(path, tag)
        if png_path is None:
            os.makedirs(os.path.join(path,"images"))
            png_path = os.path.join(path, 'images',tag)
            epng_path = png_path
            hdpng_path = png_path
            hfpng_path = png_path;
            gpng_path = png_path
        else:
            epng_path = os.path.join(png_path,'electric_forecast',tag)
            try:
                os.makedirs(os.path.join(png_path,'electric_forecast'))
            except OSError:
                pass
            gpng_path = os.path.join(png_path,'generation_forecast',tag)
            try:
                os.makedirs(os.path.join(png_path,'generation_forecast'))
            except OSError:
                pass
            hdpng_path = os.path.join(png_path,'heat_demand_forecast',tag)
            try:
                os.makedirs(os.path.join(png_path,'heat_demand_forecast'))
            except OSError:
                pass
            hfpng_path = os.path.join(png_path,'heating_fuel_forecast',tag)
            try:
                os.makedirs(os.path.join(png_path,'heating_fuel_forecast'))
            except OSError:
                pass
        if self.cd.intertie != 'child' and \
            self.cd.get_item("community","model electricity"):

            #~ start = datetime.now() 
            self.save_electric(pathrt, epng_path)
            self.save_generation_forecast(pathrt, gpng_path)
            #~ print "saving electric:" + str(datetime.now() - start)
        if self.cd.intertie != 'parent' and \
            self.cd.get_item("community","model heating fuel"):
     
            #~ start = datetime.now() 
            self.save_heat_demand(pathrt, hdpng_path)
            #~ print "saving heat demand:" + str(datetime.now() - start)
            
            #~ start = datetime.now() 
            self.save_heating_fuel(pathrt, hfpng_path)
            #~ print "saving heating fuel:" + str( datetime.now() - start)
    
    def add_heat_demand_column (self, key, year_col, data_col):
        """ 
        add a column to be saved with the heat demand forecast 
        pre:
            Key is a string. year_col is a numpy array of values, date_col
        is a corresponding array of years
        post:
            a dataframe is added to self.heat_demand_cols
        """
        self.heat_demand_cols.append(DataFrame({"year":year_col, 
                                           key:data_col}).set_index("year"))
                                           
    def add_heating_fuel_column (self, key, year_col, data_col):
        """
        add a column to be saved with the heating fuel forecast 
        pre:
            Key is a string. year_col is a numpy array of values, date_col
        is a corresponding array of years
        post:
            a dataframe is added to self.heating_fuel_cols
        """
        self.heating_fuel_cols.append(DataFrame({"year":year_col, 
                                           key:data_col}).set_index("year"))
    
    
    def generate_electric_output_dataframe (self):
        """
        """
        kWh_con = self.consumption_to_save
        kWh_con.columns = ["total_electricity_consumed [kWh/year]",
                           'residential_electricity_consumed [kWh/year]',
                           'non-residential_electricity_consumed [kWh/year]']
        c_map = copy.deepcopy(self.c_map)
        c_map.columns = ["total_electricity_consumed_qualifier"]
        
        kWh_gen = self.generation
        kWh_gen.columns = ["total_electricity_generation [kWh/year]"]
        g_map = copy.deepcopy(c_map)
        g_map.columns = ["total_electricity_generation_qualifier"]
    
        #~ community = copy.deepcopy(self.c_map)
        community = copy.deepcopy(self.c_map)
        community.columns = ["community"]
        community.ix[:] = self.cd.get_item("community","name")
        try:
            self.electric_dataframe = \
                    concat([community,self.population.round().astype(int), 
                           self.p_map, kWh_con.round().astype(int), c_map, 
                           kWh_gen.round().astype(int), g_map] ,axis=1)
        except ValueError:
            self.electric_dataframe = None
            
    
    
    def save_electric (self, csv_path, png_path):
        """ 
        save the electric forecast
        
        pre:
            self.population, consumption, and generation. should be dataframes 
        as calculated in this class. path should be the path to the output 
        directory.
        post:
            a file, electricity_forecast.csv, is save in the output directory.
        """
        self.generate_electric_output_dataframe()
        self.save_electric_csv(csv_path)
        self.save_electric_png(png_path)
        


    def save_electric_csv (self, path):
        """ 
        save the electric forecast
        
        pre:
            self.population, consumption, and generation. should be dataframes 
        as calculated in this class. path should be the path to the output 
        directory.
        post:
            a file, electricity_forecast.csv, is save in the output directory.
        """

        if self.electric_dataframe is None:
            self.diagnostics.add_warning("Forecast", 
                                ("when saving null values were found in "
                                 "generation/consumption data. Electricity "
                                 "forecast is suspect not saving summary(csv)"))
            return
        data = self.electric_dataframe
        #not joining path adding file name
        f_name = path + "electricity_forecast.csv" 
        
        fd = open(f_name ,"w")
        fd.write("# Electricity Forecast for " + \
                                    self.cd.get_item("community","name") + "\n")
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        
        fd.close()
            
        data.index = data.index.values.astype(int)
        data.to_csv(f_name, index_label="year", mode = 'a')
    
    def save_electric_png (self, path):
        """ Function doc """
        if self.electric_dataframe is None:
            self.diagnostics.add_warning("Forecast", 
                                ("when saving null values were found in "
                                 "generation/consumption data. Electricity "
                                 "forecast is suspect not saving summary(png)"))
            return
            
        path = path+ "electricity_forecast.png"
        start = self.p_map[self.p_map['population_qualifier'] == 'P'].index[0]
        df2 = self.electric_dataframe[['population',
                            'total_electricity_consumed [kWh/year]',
                            'total_electricity_generation [kWh/year]',
                            'residential_electricity_consumed [kWh/year]',
                            'non-residential_electricity_consumed [kWh/year]']]
        name = self.cd.get_item("community","name") + ' Electricity Forecast'
        
        fig, ax = plot.setup_fig(name ,'years','population')
        ax1 = plot.add_yaxis(fig,'kWh')
        
        c_dict = {'population': [min(1,r*4) for r in colors.red],
                   'total_electricity_consumed [kWh/year]':colors.orange,
                    'total_electricity_generation [kWh/year]':colors.green,
                     'residential_electricity_consumed [kWh/year]':colors.yellow,
                    'non-residential_electricity_consumed [kWh/year]':colors.violet
        }
        
        plot.plot_dataframe(ax1,df2,ax,['population'],
                    {'population':'population',
                    'total_electricity_consumed [kWh/year]':'consumption',
                    'total_electricity_generation [kWh/year]':'generation',
                    'residential_electricity_consumed [kWh/year]':'residential consumption',
                    'non-residential_electricity_consumed [kWh/year]':'non residential consumption'},
                    c_dict)
        fig.subplots_adjust(right=.85)
        fig.subplots_adjust(left=.12)
        plot.add_vertical_line(ax,start, 'forecasting starts' )
        plot.add_horizontal_line(ax1,0)
    
    
        plot.create_legend(fig)
        plot.save(fig,path)
        plot.clear(fig)
        
    def generate_generation_forecast_dataframe(self):
        """
        """
        data = self.generation_by_type
        g_map = copy.deepcopy(self.c_map)
        g_map.columns = ["generation_qualifier"]
        
        
        order = []
        try:
            for col in ['generation total', 'generation diesel', 
                        'generation hydro', 
                        'generation natural gas', 'generation wind', 
                        'generation solar', 'generation biomass']:
                kWh = col.replace(" ", "_") + " [kWh/year]"
                mmbtu = col.replace(" ", "_") + " [mmbtu/year]"
                data[kWh] = data[col].round().astype(int)
                data[mmbtu] = (data[col] / constants.mmbtu_to_kWh)\
                                                .fillna(0).round().astype(int)
                del data[col]
                order += [kWh, mmbtu]
            data = concat([self.population.round().astype(int),
                           self.p_map,g_map,data],axis=1) 
            data["community"] = self.cd.get_item("community","name")
                    
            self.generation_forecast_dataframe = \
                            data[[data.columns[-1]] + data.columns[:-1].tolist()]
            del data
        except ValueError:
            self.generation_forecast_dataframe = None
        
    def save_generation_forecast (self, csv_path, png_path):
        
        self.generate_generation_forecast_dataframe()
        
        if self.generation_forecast_dataframe is None:
            self.diagnostics.add_warning("Forecast", 
                        ("when saving null values were found in "
                         "generation data. generation generation "
                         "forecast is suspect not saving summary(csv and png)"))
        else:
            self.save_generation_forecast_csv(csv_path)
            self.save_generation_forecast_png(png_path)
        
    def save_generation_forecast_csv (self, path):
        """
        """
        out_file = path + "generation_forecast.csv"
        fd = open(out_file, 'w')
        fd.write("# Generation forecast\n")
        fd.write(("# The column 'generation_qualifier' applies to all "
                                "of the following generation columns"))
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        fd.close()
        self.generation_forecast_dataframe.to_csv(out_file, 
                                        index_label="year", mode = 'a')  
                                        
    def save_generation_forecast_png (self, path):
        """ Function doc """
            
        path = path + "generation_forecast.png"
        
        png_list = ['population',
        'generation_total [kWh/year]',
        'generation_diesel [kWh/year]',
        'generation_hydro [kWh/year]',
        'generation_natural_gas [kWh/year]',
        'generation_wind [kWh/year]',
        'generation_solar [kWh/year]',
        'generation_biomass [kWh/year]']
        
        
        
        png_dict = {'population':'population',
        'generation_total [kWh/year]':'total',
        'generation_diesel [kWh/year]':'diesel',
        'generation_hydro [kWh/year]':'hydro',
        'generation_natural_gas [kWh/year]':'natural gas',
        'generation_wind [kWh/year]':'wind',
        'generation_solar [kWh/year]':'solar',
        'generation_biomass [kWh/year]':'biomass'}
        
    
        c_dict = {'population': [min(1,r*4) for r in colors.red],
        'generation_total [kWh/year]':colors.jet,
        'generation_diesel [kWh/year]':colors.red,
        'generation_hydro [kWh/year]':colors.blue,
        'generation_natural_gas [kWh/year]':colors.violet,
        'generation_wind [kWh/year]':[ min(1,r*2) for r in colors.blue],
        'generation_solar [kWh/year]':colors.orange,
        'generation_biomass [kWh/year]':colors.avacado}
        
        temp = []
        for i in png_list:
            if  all(self.generation_forecast_dataframe[i].fillna(0) == 0):
                continue
            temp.append(i)
        png_list = temp
        if len(png_list) == 3:
            png_list = list(set(png_list).\
                    difference(['generation_total [kWh/year]']))
        
        df2 = self.generation_forecast_dataframe[png_list]
        plot_name = self.cd.get_item("community","name") +' Generation Forecast'
        
        fig, ax = plot.setup_fig(plot_name ,'years','population')
        ax1 = plot.add_yaxis(fig,'Generation kWh')
        
        plot.plot_dataframe(ax1,df2,ax,['population'],png_dict,c_dict)
        fig.subplots_adjust(right=.85)
        fig.subplots_adjust(left=.12)
        start = self.p_map[self.p_map['population_qualifier'] == 'P'].index[0]
        plot.add_vertical_line(ax,start, 'forecasting starts' )
        plot.add_horizontal_line(ax1,0)
        plot.create_legend(fig,.20)

        plot.save(fig,path)
        plot.clear(fig)
        
    
    def generate_heat_demand_dataframe (self):
        """
        """
        data = concat([self.population.round().astype(int), self.p_map] + \
                                                self.heat_demand_cols,axis=1) 
    
        for key in data.keys():
            try:
                col = data[key]
                idx = np.logical_not(col.apply(np.isnan))
                lv = col[idx].tail(1).values[0]
                yr = col[idx].tail(1).index[0]
                col[col.index > yr] = lv
                data[key] = col.round()
            except (TypeError, IndexError, AttributeError):
                pass
            
        idx = data.keys()[['mmbtu' in s for s in data.keys()]]
    
        data["heat_energy_demand_total [mmbtu/year]"] = data[idx].sum(1).round()
        data["community"] = self.cd.get_item("community","name")
                
        self.heat_demand_dataframe = data[[data.columns[-1]] + data.columns[:-1].tolist()]
        del data
        
    def save_heat_demand (self,csv_path, png_path):
        """ Function doc """
        self.generate_heat_demand_dataframe()
        self.save_heat_demand_csv(csv_path)
        self.save_heat_demand_png(png_path)
    
    def save_heat_demand_csv (self, path):
        """
        save the heat demand forecast
        
        pre:
            self.population should be a dataframe. self.heat_demad_cols should 
        be populated using add_heat_demad_column. path should be the path to the
        output directory.
        post:
            a file, heat_demand_forecast.csv, is save in the output directory.
        """
        f_name = path + "heat_demand_forecast.csv"
        data =  self.heat_demand_dataframe      
        fd = open(f_name ,"w")
        fd.write("# Heat Demand Forecast for " + \
                                    self.cd.get_item("community","name") + "\n")
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        fd.close()
        
        data.index = data.index.values.astype(int)
        data.to_csv(f_name, index_label="year", mode = 'a')
        
    def save_heat_demand_png(self,path):
        """
        """
        path = path+ "heat_demand_forecast.png"
        start = self.p_map[self.p_map['population_qualifier'] == 'P'].index[0]
        
        cols = ['population']
        for col in self.heat_demand_dataframe.columns:
            if "[mmbtu/year]" in col:
                cols += [col]
                
        df2 = self.heat_demand_dataframe[cols]
        name = self.cd.get_item("community","name") + ' Heat Demand Forecast'
        
        fig, ax = plot.setup_fig(name ,'years','population')
        ax1 = plot.add_yaxis(fig,'Heat Demand MMBtu')
        
        c_dict = {'population': [min(1,r*4) for r in colors.red],
        'heat_energy_demand_residential [mmbtu/year]':colors.yellow,
        'heat_energy_demand_water-wastewater [mmbtu/year]':colors.cobalt,
        'heat_energy_demand_non-residential [mmbtu/year]':colors.green,
                        'heat_energy_demand_total [mmbtu/year]':colors.jet}
        
        plot.plot_dataframe(ax1,df2,ax,['population'],
            {'population':'population',
        'heat_energy_demand_residential [mmbtu/year]':'residential',
        'heat_energy_demand_water-wastewater [mmbtu/year]':'water & wastewater',
        'heat_energy_demand_non-residential [mmbtu/year]':'non-residential',
                        'heat_energy_demand_total [mmbtu/year]':'total'},
                        c_dict)
        fig.subplots_adjust(right=.85)
        fig.subplots_adjust(left=.12)
        plot.add_vertical_line(ax,start, 'forecasting starts' )
        plot.add_horizontal_line(ax1,0)
    
        plot.create_legend(fig,.2)
        plot.save(fig,path)
        plot.clear(fig)
    
    def generate_heating_fuel_dataframe(self):
        """ """
        data = concat([self.population.round().astype(int), self.p_map] + \
                                                self.heating_fuel_cols, axis=1)

        for key in data.keys():
            try:
                col = data[key]
                idx = np.logical_not(col.apply(np.isnan))
                lv = col[idx].tail(1).values[0]
                yr = col[idx].tail(1).index[0]
                col[col.index > yr] = lv
                data[key] = col.round()
            except (TypeError,IndexError, AttributeError):
                pass

        hf_gal_idx = data.keys()[['gallons' in s for s in data.keys()]]
        hf_gal_idx =  hf_gal_idx[['heating_fuel' in s for s in hf_gal_idx]]
        
        hf_btu_idx = data.keys()[['mmbtu' in s for s in data.keys()]]
        hf_btu_idx =  hf_btu_idx[['heating_fuel' in s for s in hf_btu_idx]]
        
        
        data["heating_fuel_total_consumed [gallons/year]"] = \
                                        data[hf_gal_idx].sum(1).round()
        data["heating_fuel_total_consumed [mmbtu/year]"]= \
                                        data[hf_btu_idx].sum(1).round()
        data["community"] = self.cd.get_item("community","name")


        self.heating_fuel_dataframe = \
                        data[[data.columns[-1]] + data.columns[:-1].tolist()]
        del data
    
    def save_heating_fuel(self, csv_path, png_path):
        """ """
        #~ start = datetime.now() 
        self.generate_heating_fuel_dataframe()
        #~ print "saving heating fuel *1:" + str( datetime.now() - start)
        #~ start = datetime.now() 
        self.save_heating_fuel_csv(csv_path)
        #~ print "saving heating fuel *2:" + str( datetime.now() - start)
        #~ start = datetime.now() 
        self.save_heating_fuel_png(png_path)
        #~ print "saving heating fuel *3:" + str( datetime.now() - start)
    
    def save_heating_fuel_csv (self, path):
        """
        save the heating fuel 
        
        pre:
            self.population should be a dataframe. self.heat_demad_cols should 
        be populated using add_heating_fuel_column. path should be the path to 
        the output directory. 
        post:
            a file, heating_fuel_forecast.csv, is save in the output directory.
        """
        f_name = path + "heating_fuel_forecast.csv"
        data = self.heating_fuel_dataframe
        
        fd = open(f_name ,"w")
        fd.write("# Heating Fuel Forecast for " + \
                                    self.cd.get_item("community","name") + "\n")
        fd.write("# Qualifier info: \n")
        fd.write("#   M indicates a measured value \n")
        fd.write("#   P indicates a projected value \n")
        fd.close()

        data.index = data.index.values.astype(int)
        data.to_csv(f_name, index_label="year", mode = 'a')
        
    def save_heating_fuel_png (self, path):
        """"""
        path = path+ "heating_fuel_forecast.png"
        start = self.p_map[self.p_map['population_qualifier'] == 'P'].index[0]
        
        cols = ['population']
        for col in self.heating_fuel_dataframe.columns:
            if "[mmbtu/year]" in col:
                cols += [col]
        
        df2 = self.heating_fuel_dataframe[cols]

        name = self.cd.get_item("community","name") + ' Heating fuel Forecast'
        
        fig, ax = plot.setup_fig(name ,'years','population')
        ax1 = plot.add_yaxis(fig,'Heating fuel MMBtu')
        
        c_dict = {'population': [min(1,r*4) for r in colors.red],
            "heating_fuel_residential_consumed [mmbtu/year]":
                    colors.red,
            "cords_wood_residential_consumed [mmbtu/year]":
                    colors.avacado,
            "gas_residential_consumed [mmbtu/year]":
                    colors.violet,
            "electric_residential_consumed [mmbtu/year]":
                    colors.goldenrod,
            "propane_residential_consumed [mmbtu/year]":
                    colors.orange,
            "heating_fuel_water-wastewater_consumed [mmbtu/year]":
                    colors.cobalt,
            "heating_fuel_non-residential_consumed [mmbtu/year]":
                    colors.green,
            "heating_fuel_total_consumed [mmbtu/year]":colors.jet,}
        
        plot.plot_dataframe(ax1,df2,ax,['population'],
            {"population":'population',
            "heating_fuel_residential_consumed [mmbtu/year]":
                    'heating oil - residential',
            "cords_wood_residential_consumed [mmbtu/year]":
                    'wood - residential',
            "gas_residential_consumed [mmbtu/year]":
                    'natural gas - residential',
            "electric_residential_consumed [mmbtu/year]":
                    'electric - residential',
            "propane_residential_consumed [mmbtu/year]":
                    'propane - residential',
            "heating_fuel_water-wastewater_consumed [mmbtu/year]":
                    'heating oil - water wastewater',
            "heating_fuel_non-residential_consumed [mmbtu/year]":
                    'heating oil - non - residential',
            "heating_fuel_total_consumed [mmbtu/year]":'total'},
            c_dict)
        fig.subplots_adjust(right=.85)
        fig.subplots_adjust(left=.12)
        plot.add_vertical_line(ax,start, 'forecasting starts' )
        plot.add_horizontal_line(ax1,0)
    
        plot.create_legend(fig,.30)
        plot.save(fig,path)
        plot.clear(fig)

def test ():
    """ 
    test the forecast
    """
    manley_data = CommunityData("../test_case/input_data/", 
                            "../test_case/baseline_results/config_used.yaml")
    
                            
    fc = Forecast(manley_data)

    return fc
