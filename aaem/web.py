from jinja2 import Environment, PackageLoader
import aaem.driver as driver
from pandas import concat, DataFrame, read_csv
import os
import shutil

from importlib import import_module
from aaem.components import comp_lib, comp_order
from aaem.constants import hours_per_year
from aaem import __file__, __version__
from datetime import datetime

import numpy as np
import yaml

#WHAT TO DO IF ALL PLOT DATA IS NANS?
#~ import aaem
class WebSummary(object):
    """ Class doc """
    
    def __init__ (self, model_root, directory, tag = ''):
        """ Class initialiser """
        self.max_year = 2040
        self.model_root = model_root
        model = driver.Driver(self.model_root)
        self.results = model.load_results(tag)
        #~ print self.results
        
        
       
        self.version = __version__
        with open(os.path.join(self.model_root,'input_files',
                    '__metadata','input_files_metadata.yaml'), 'r') as md:
            self.data_version = yaml.load(md)['data version']
        self.metadata = {"date": datetime.strftime(datetime.now(),'%Y-%m-%d'),
                         "version": self.version, 
                         "data_version": self.data_version}
        
        self.directory = directory
        try:
            os.makedirs(self.directory)
        except OSError as e:
            #~ print e
            pass
        #~ print "fine"
        self.env = Environment(loader=PackageLoader('aaem','templates/'))

    def get_viable_components (self, com, cutoff = 1):
        """ Function doc """
        l = []
        for comp in self.results[com]:
            try:
                if self.results[com][comp].get_BC_ratio() == 'N/A':
                    continue
                if self.results[com][comp].get_BC_ratio() >= cutoff:
                    l.append(comp)
            except AttributeError as e:
                #~ print e
                pass
        
        return l
        
    def generate_web_summaries (self, com):
        """
        """
        os.makedirs(os.path.join(self.directory, com, 'csv'))
        self.finances_demo_summary(com)
        self.consumption_summary(com)
        self.generation_summary(com)
        self.projects_summary(com)
        #~ self.get_web_summary(comp_lib['Biomass for Heat (Cordwood)'])(self, com)
        #~ return 
        components = set(comp_order)
        
        it = self.results[com]['community data'].intertie
        if not it is None:
            if it == 'parent':
                components = set(["Wind Power", 'Solar Power',  'Hydropower',
                              'Transmission and Interties','Diesel Efficiency'])
            else:
                components = set(comp_order) - set(["Wind Power", 'Solar Power',  'Hydropower',
                              'Transmission and Interties','Diesel Efficiency'])
        
        
        re_dirs = set(comp_order) - components
        
        for comp in components:
            #~ print comp
            try:
                self.get_web_summary(comp_lib[comp])(self, com)
            except (AttributeError, RuntimeError) as e:
                #~ print comp, e
                template = self.env.get_template('no_results.html')
                #~ if comp in ['Solar Power','Wind Power','Heat Recovery'] :
                pth = os.path.join(self.directory, com, comp.replace(' ','_').replace('(','').replace(')','').lower() +'.html')

                with open(pth, 'w') as html:
                    reason = self.results[com][comp].reason
                    if reason.lower() == 'ok':
                        reason = "The component has a bad motivater"
                    html.write(template.render( 
                                    type = comp, 
                                    com = com ,
                                    reason = reason,
                                    sections = self.get_summary_pages(),
                                    communities = self.get_all_coms(),
                                    metadata = self.metadata,))
                                    
            template = self.env.get_template('no_results.html')
            for comp in re_dirs:
                
                pth = os.path.join(self.directory, com, comp.replace(' ','_').replace('(','').replace(')','').lower() +'.html')

                with open(pth, 'w') as html:
                    reason = "REDIRECT " + "parent" if it == "child" else "child"
                    
                    html.write(template.render( 
                                    type = comp, 
                                    com = com ,
                                    reason = reason,
                                    sections = self.get_summary_pages(),
                                    communities = self.get_all_coms(),
                                    metadata = self.metadata,))

    def copy_etc (self):
        
        pth = os.path.dirname(__file__)
        shutil.copytree(os.path.join(pth,'templates','css'),os.path.join(self.directory,'css'))
        shutil.copytree(os.path.join(pth,'templates','js'),os.path.join(self.directory,'js'))
        shutil.copytree(os.path.join(pth,'templates','fonts'),os.path.join(self.directory,'fonts'))
        shutil.copy(os.path.join(pth,'templates','summary.css'),self.directory)
        
        
        
    def get_web_summary(self, component):
        """
        """
        try:
            return self.imported_summaries[component].generate_web_summary
        except AttributeError as e:
            #~ print e
            self.imported_summaries = {}
        except KeyError as e:
            #~ print e
            pass
            
        self.imported_summaries[component] = \
                    import_module("aaem.components." + component).outputs
        return self.imported_summaries[component].generate_web_summary
    

    def get_all_coms (self):
        """ Function doc """
        return sorted([k for k in self.results.keys() if k.find('+') == -1])
    
    def get_summary_pages (self):
        return [{'name':'Summary', 'pages':['Financial and Demographic',
                                            'Consumption',
                                            'Generation',
                                            'Potential Projects']}, 
                {'name':'Efficiency Projects', 'pages':["Residential Energy Efficiency",
                                                        "Non-residential Energy Efficiency",
                                                        "Water and Wastewater Efficiency"]
                },
                {'name':'Electricity Projects', 'pages':["Wind Power",
                                                         'Solar Power',
                                                          'Hydropower',
                                                         'Transmission and Interties',
                                                         'Diesel Efficiency']
                },
                {'name':'Heating Projects', 'pages':['Biomass for Heat (Cordwood)',
                                                     'Biomass for Heat (Pellet)',
                                                      'Residential ASHP',
                                                      'Non-Residential ASHP',
                                                      'Heat Recovery']
                }
               ]

    def generate_all (self):
        """ Function doc """
        keys = sorted([k for k in self.results.keys() if k.find('+') == -1])
        self.copy_etc()
        try:
            from multiprocessing import Process, Lock,active_children, cpu_count
            lock = Lock()
    
            for com in keys:#["Stebbins","Adak","Brevig_Mission"]:
                while len(active_children()) >= cpu_count():
                    continue
                lock.acquire()
                print com, "started"
                lock.release()
                Process(target=self.generate_com_mc, args=(com, lock)).start()
                
            while len(active_children()) > 0:
                continue
        except ImportError:
            for com in keys:#["Stebbins","Adak","Brevig_Mission"]:
                start = datetime.now()
                self.generate_web_summaries(com)
                print com, datetime.now() - start
    
    def generate_com_mc (self, com):
        """ Function doc """
        start = datetime.now()
        self.generate_web_summaries(com)
        l.acquire()
        print com, datetime.now() - start
        l.release()
    
                                        
    def finances_demo_summary (self, com):
        """ Function doc """
        template = self.env.get_template('demo.html')
        res = self.results[com]
        population = res['community data'].get_item('forecast','population')
        p1 = population
        p1['year'] = p1.index
        population_table = self.make_plot_table(p1[['year','population']] , community = com, fname = com+"_population.csv")
        #~ print com
        
        charts = [
        {'name':'population', 'data': str(population_table).replace('nan','null'), 
         'title': 'Population Forecast',
         'type': "'people'",
         'plot': True,},
            ]
        
        elec_price = res['community data'].get_item('community','electric non-fuel prices')
        if not type(elec_price) is str:
            elec_price ['year'] = elec_price.index
            ep_table = self.make_plot_table(elec_price[['year','price']], names = ['year', 'electricity price ($/kWh)'], sigfig = 2)
            charts.append({'name':'e_price', 'data': str(ep_table).replace('nan','null'), 
                        'title':'Electricity Price ($/kWh)',
                        'type': "'currency'",
                        'plot': True,})
        else:
            charts.append({'name':'e_price', 'data': "No electricity price for community.", 
                        'title':'Electricity Price ($/kWh)',
                        'type': "'currency'",})

        diesel = res['community data'].get_item('community','diesel prices')
        diesel = DataFrame(diesel.projected_prices, columns = ['Diesel Price ($/gal)'],index=range(diesel.start_year,diesel.start_year+len(diesel.projected_prices)))
        diesel['year'] = diesel.index
        #~ print diesel
        diesel['Heating Fuel ($/gal)'] = diesel['Diesel Price ($/gal)'] + res['community data'].get_item('community','heating fuel premium')
        d_table = self.make_plot_table(diesel[['year','Diesel Price ($/gal)','Heating Fuel ($/gal)']], sigfig = 2)
        charts.append({'name':'d_price', 'data': str(d_table).replace('nan','null'), 
                        'title':'Fuel Price',
                        'type': "'currency'",
                        'plot': True,})  
                        
        
        costs = DataFrame(index=range(res['Residential Energy Efficiency'].start_year,
                                    res['forecast'].end_year))
                            
        costs['year']=costs.index
        #~ costs_data = False
        if hasattr(res['Residential Energy Efficiency'], 'baseline_kWh_cost'):
            costs['Residential Electricity'] = res['Residential Energy Efficiency'].baseline_kWh_cost
        else:
            costs['Residential Electricity'] = np.nan
                              
        if hasattr(res['Non-residential Energy Efficiency'], 'baseline_kWh_cost'):
            costs['Non-residential Electricity'] = res['Non-residential Energy Efficiency'].baseline_kWh_cost
        else:
            costs['Non-residential Electricity'] = np.nan
        
        if hasattr(res['Water and Wastewater Efficiency'], 'baseline_kWh_cost'):
            costs['Water/Wastewater Electricity'] = res['Water and Wastewater Efficiency'].baseline_kWh_cost
        else: 
            costs['Water/Wastewater Electricity'] =  np.nan
            
        if hasattr(res['Residential Energy Efficiency'], 'baseline_HF_cost'):
            costs['Residential Heating Fuel'] = res['Residential Energy Efficiency'].baseline_HF_cost
        else:
            costs['Residential Heating Fuel'] = np.nan
            
        if hasattr(res['Non-residential Energy Efficiency'], 'baseline_HF_cost'):
            costs['Non-residential Heating Fuel'] = res['Non-residential Energy Efficiency'].baseline_HF_cost
        else:
            costs['Non-residential Heating Fuel'] = np.nan
            
        if hasattr(res['Water and Wastewater Efficiency'], 'baseline_HF_cost'):
            costs['Water/Wastewater Heating Fuel'] = res['Water and Wastewater Efficiency'].baseline_HF_cost
        else:
            costs['Water/Wastewater Heating Fuel'] = np.nan
            

        costs = costs[['year'] + list(costs.columns)[1:][::-1]]
        #~ print costs
        costs_table = self.make_plot_table(costs, sigfig = 2)
        
        #~ if costs_data:
        charts.append({'name':'costs', 'data': str(costs_table).replace('nan','null'), 
                            'title':'Costs by Sector',
                            'type': "'percent'",
                            'stacked': True,
                            'plot': True,})  
        #~ else:
            #~ charts.append({'name':'e_price', 'data': str(e), 
                        #~ 'title':'Electricity Price ($/kWh)',
                        #~ 'type': "'currency'",})

        
            
        
        pth = os.path.join(self.directory, com,
                    'Financial and Demographic'.replace(' ','_').replace('(','').replace(')','').lower() + '.html')
        with open(pth, 'w') as html:
            html.write(template.render( type = 'Financial and Demographic', 
                                com = com ,
                                charts = charts,
                                summary_pages = ['Summary'] + comp_order ,
                                sections = self.get_summary_pages(),
                                communities = self.get_all_coms(),
                                metadata = self.metadata,
                                ))
                                
    def consumption_summary (self, com):
        """ Function doc """
        template = self.env.get_template('demo.html')
        res = self.results[com]
        charts = []
        
        
        if hasattr(res['forecast'], 'consumption_to_save') or \
           hasattr(res['forecast'], 'consumption'):
            if hasattr(res['forecast'], 'consumption_to_save'):
                consumption = res['forecast'].consumption_to_save
                cols = ['year', "consumption kWh", 'residential kWh', 'non-residential kWh']
                names = ['Year', 'Total', 'Residential' , 'Non-Residential']
            else:   
                consumption = res['forecast'].consumption
                cols = ['year', "consumption kWh"]
                names = ['Year', 'Total']
            
            consumption['year'] = consumption.index
            c_map = res['forecast'].c_map
            annotation = c_map[c_map['consumption_qualifier']\
                                                    == 'M'].index.max() + 1
            consumption['annotation'] = np.nan 
            consumption['annotation'][annotation] = 'start of forecast'
            
            names.insert(1,'annotation')
            cols.insert(1,'annotation')
        
            consumption_table = self.make_plot_table(consumption[cols] ,
                                                                names = names)
            #~ print consumption_table
            charts.append({'name':'consumption', 
                    'data': str(consumption_table).replace('nan','null'), 
                    'title':'Electricity Consumed',
                    'type': "'kWh'",
                        'plot': True,})
        else: 
            charts.append({'name':'consumption', 
                    'data': "No consumption data avaialble.", 
                    'title':'Electricity Consumed',
                    'type': "'kWh'"})
            
        
        diesel_consumption = DataFrame(index=range(res['Residential Energy Efficiency'].start_year,
                                    res['forecast'].end_year))
        diesel_consumption['year']=diesel_consumption.index
        if hasattr(res['Residential Energy Efficiency'],
                    'baseline_fuel_Hoil_consumption'):
            diesel_consumption['Residential Heating Oil(gallons)'] = \
                                        res['Residential Energy Efficiency'].\
                                        baseline_fuel_Hoil_consumption
        else:
            diesel_consumption['Residential Heating Oil(gallons)'] = np.nan
        
        
        if hasattr(res['Non-residential Energy Efficiency'], 
                    'baseline_fuel_Hoil_consumption'):
            diesel_consumption['Non-residential Heating Oil(gallons)'] = \
                                    res['Non-residential Energy Efficiency'].\
                                    baseline_fuel_Hoil_consumption
        else:
            diesel_consumption['Non-residential Heating Oil(gallons)'] = np.nan
        
        if hasattr(res['Water and Wastewater Efficiency'], 
                    'baseline_fuel_Hoil_consumption'):
            diesel_consumption['Water/Wastewater Heating Oil(gallons)'] = \
                                        res['Water and Wastewater Efficiency'].\
                                        baseline_fuel_Hoil_consumption
        else:
            diesel_consumption['Water/Wastewater Heating Oil(gallons)'] = np.nan
            
        if hasattr(res['forecast'], 'generation_by_type'):
            eff = res['community data'].get_item("community",
                                            "diesel generation efficiency")
            if eff == 0:
                eff = np.nan
                
            #~ print res['forecast'].generation_by_type["generation diesel"]
            diesel_consumption['Utility Diesel(gallons)'] = \
                res['forecast'].generation_by_type["generation diesel"] / eff
            #~ diesel_consumption['Utility Diesel(gallons)']
        else:
            diesel_consumption['Utility Diesel(gallons)'] = np.nan
            
            
        diesel_consumption = diesel_consumption[['year'] + list(diesel_consumption.columns)[1:][::-1]]
            

        diesel_consumption_table = self.make_plot_table(diesel_consumption, sigfig = 2)
        charts.append({'name':'diesel_consumption', 'data': str(diesel_consumption_table).replace('nan','null'), 
                        'title':'Energy Consumption',
                        'type': "'percent'",
                        'stacked': True,'plot': True,})  
        #~ except AttributeError:
            #~ pass

            
        pth = os.path.join(self.directory, com,
                    'Consumption'.replace(' ','_').replace('(','').replace(')','').lower() + '.html')
        with open(pth, 'w') as html:
            html.write(template.render( type = 'Consumption', 
                                    com = com ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = self.get_summary_pages(),
                                    communities = self.get_all_coms(),
                                    metadata = self.metadata,
                                    ))
        
    def generation_summary (self, com):
        """ Function doc """
        template = self.env.get_template('demo.html')
        res = self.results[com]
        charts = []
        #~ try:
        if hasattr(res['forecast'], 'generation_by_type'):
            if not hasattr(res['forecast'], 'generation_forecast_dataframe'):
                res['forecast'].generate_generation_forecast_dataframe()
            
            generation = res['forecast'].generation_forecast_dataframe[['generation_diesel [kWh/year]',
                                                                        'generation_hydro [kWh/year]',
                                                                        'generation_natural_gas [kWh/year]',
                                                                        'generation_wind [kWh/year]',
                                                                        'generation_solar [kWh/year]',
                                                                        'generation_biomass [kWh/year]']]
            
                                                                        
              
                                                                    
            generation['year']=generation.index
            generation = generation[['year'] + list(generation.columns)[:-1][::-1]]
            
            c_map = res['forecast'].c_map
            annotation = c_map[c_map['consumption_qualifier']\
                                                    == 'M'].index.max() + 1
            generation['annotation'] = np.nan 
            generation['annotation'][annotation] = 'start of forecast'
        
            generation = generation[['year','annotation'] + list(generation.columns[1:-1])]
            
            generation_table = self.make_plot_table(generation, sigfig = 2, community = com, fname = com+"_generation.csv")
            charts.append({'name':'generation', 'data': 
                           str(generation_table).replace('nan','null'), 
                                'title':'generation',
                                'type': "'gallons'",'plot': True,})  
        else:
            charts.append({'name':'generation',
                            'data': "No generation data available",
                                'title':'generation',
                                'type': "'gallons'",})
        
        #~ hh = DataFrame(costs['year'])
        #~ hh['households']=res['Residential Energy Efficiency'].households
        #~ print hh
        #~ hh_table = self.make_plot_table(hh)
        #~ charts.append({'name':'hh', 'data': str(hh_table).replace('nan','null'), 
                            #~ 'title':'housholds',
                            #~ 'type': "'households'"}) 
            
            
        if hasattr(res['forecast'], 'consumption_to_save') or \
           hasattr(res['forecast'], 'consumption'):
            if hasattr(res['forecast'], 'consumption_to_save'):
                avg_load = res['forecast'].consumption_to_save
            else:    
                avg_load = res['forecast'].consumption
            
            names = ['Year', 'annotation', 'Average Load']
            avg_load = avg_load
            avg_load['year'] = avg_load.index
            
            c_map = res['forecast'].c_map
            annotation = c_map[c_map['consumption_qualifier']\
                                                    == 'M'].index.max() + 1
            avg_load['annotation'] = np.nan 
            avg_load['annotation'][annotation] = 'start of forecast'
            
            
            avg_load['Average Load'] = avg_load["consumption kWh"]/hours_per_year
        
            avg_load_table = self.make_plot_table(avg_load[['year', 'annotation', 'Average Load']], names = names, community = com, fname = com+"_avg_load.csv")
        
            charts.append({'name':'avg_load', 'data': str(avg_load_table).replace('nan','null'), 
                    'title':'Averag Load',
                    'type': "'kW'",'plot': True,})
        else:
            charts.append({'name':'avg_load', 
                    'data': "No Conumption available to calculate average load", 
                    'title':'Averag Load',
                    'type': "'kW'",})
        
        #~ print os.path.join(self.model_root,'input_files', com, 'yearly_electricity_summary.csv')
        
        try:
            yes = read_csv(os.path.join(self.model_root,'input_files', com, 'yearly_electricity_summary.csv'),comment='#')
            #~ print yes.columns
        except IOError: 
            yes = None
            
        if not yes is None:
            yes_years = yes[yes.columns[0]].values
        
        if not yes is None:
            start = min(yes_years)
        else:
            start = res['community data'].get_item('community','current year')
        
        end = res['community data'].get_item('forecast','end year')
        years = range(int(start),int(end))
        
        line_loss = DataFrame(years, columns = ['year'], index = years)
        line_loss['line losses'] = res['community data'].get_item('community','line losses')
        line_loss['diesel generation efficiency'] = res['community data'].get_item('community','diesel generation efficiency')
         
        if not yes is None:
            line_loss['line losses'].ix[ range(int(min(yes_years)),int(max(yes_years)))] = np.nan
            line_loss['line losses'].ix[ yes_years ] = yes['line loss'].values
            line_loss['diesel generation efficiency'].ix[ range(int(min(yes_years)),int(max(yes_years))) ] = np.nan
            line_loss['diesel generation efficiency'].ix[ yes_years ] = yes['efficiency'].values
        #~ print line_losxs

        
        try:
            line_loss['annotation'] = np.nan 
            line_loss['annotation'][int(max(yes_years)) + 1] = 'start of forecast'
        except:
            line_loss['annotation'] = np.nan 
            line_loss['annotation'][start] = 'start of forecast'

        line_loss = line_loss.replace([np.inf, -np.inf], np.nan)
        line_loss_table = self.make_plot_table(line_loss[['year', 'annotation', "line losses"]],sigfig = 2)
        charts.append({'name':'line_loss', 'data': str(line_loss_table).replace('nan','null').replace('None','null'), 
                'title':'line losses',
                'type': "'percent'",'plot': True,})

        gen_eff_table = self.make_plot_table(line_loss[['year', 'annotation', 'diesel generation efficiency']],sigfig = 2, community = com, fname = com+"_generation_efficiency.csv")
        charts.append({'name':'generation_efficiency', 'data': str(gen_eff_table).replace('nan','null'), 
                'title':'Diesel Genneration Efficiency',
                'type': "'gal/kWh'",'plot': True,})
            

        pth = os.path.join(self.directory, com,
                    'Generation'.replace(' ','_').replace('(','').replace(')','').lower() + '.html')
        with open(pth, 'w') as html:
            html.write(template.render( type = 'Generation', 
                                    com = com ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = self.get_summary_pages(),
                                    communities = self.get_all_coms(),
                                    metadata = self.metadata,
                                    ))
        
        
    def projects_summary (self, com):
        """ Function doc """
        template = self.env.get_template('potential_projects.html')
        res = self.results[com]

        
       
        cats = {}
        
        for i in [i for i in sorted(self.results.keys()) if i.find(com) != -1 ]:
            comps = self.results[i]
            if i.find('hydro') != -1:
                comps = ['Hydropower']
            elif i.find('wind') != -1:
                comps = ['Wind Power']
            elif i.find('heat_recovery') != -1:
                comps =['Heat Recovery']
            
            it = self.results[com]['community data'].intertie    
            
            for comp in comps:  
                if comp in ['forecast', 'community data']:
                    continue
                  
                it = self.results[com]['community data'].intertie
                if not it is None:
                    if it == 'parent' and not comp in ["Wind Power",
                                                         'Solar Power',
                                                          'Hydropower',
                                                         'Transmission and Interties',
                                                         'Diesel Efficiency']:
                        continue
                    if it == 'child' and comp in ["Wind Power",
                                                         'Solar Power',
                                                          'Hydropower',
                                                         'Transmission and Interties',
                                                         'Diesel Efficiency']:
                        continue
                        
                                                             
                    
                c = self.results[i][comp]
                ratio = c.get_BC_ratio()
                if 'N/A' == ratio:
                    ratio = 0
  
                
                try:
                    name = c.comp_specs['project details']['name']
                except (KeyError,TypeError):
                    name = comp
                    
                #~ print name
                if name == 'None':
                    
                    name = comp
                
                if not comp in cats.keys():
                    cats[comp] = []
                    
                lcoe_e = 0
                lcoe_hf = 0
                try:
                    try:
                        lcoe_e = c.levelized_cost_of_energy['kWh']
                        lcoe_hf = c.levelized_cost_of_energy['MMBtu']
                    except:
                        if comp in ["Wind Power",'Solar Power','Hydropower',
                                    'Transmission and Interties','Diesel Efficiency']:
                            lcoe_e = c.levelized_cost_of_energy
                        else:
                            lcoe_hf = c.levelized_cost_of_energy
                except AttributeError:
                    pass
                    
                fs = 0
                try:
                    fs = c.get_fuel_total_saved()[0]
                except:
                    pass
                cats[comp].append({'name':name.decode('unicode_escape').encode('ascii','ignore'),
                              'sucess': True if ratio > 1.0 else False,
                              'comp':comp,
                              'benefits': '${:,.0f}'.format(0 if c.get_NPV_benefits() == 'N/A' else c.get_NPV_benefits()),
                              'costs': '${:,.0f}'.format(0 if c.get_NPV_costs() == 'N/A' else c.get_NPV_costs()),
                              'net': '${:,.0f}'.format(0 if c.get_NPV_net_benefit() == 'N/A' else c.get_NPV_net_benefit()),
                              'ratio': '{:,.2f}'.format(ratio),
                              'lcoe_e':lcoe_e,
                              'lcoe_hf':lcoe_hf,
                              'fuel_saved':fs})
         
        projs =[]
        for comp in ["Residential Energy Efficiency", "Non-residential Energy Efficiency",
                     "Water and Wastewater Efficiency", "Wind Power", 'Solar Power',
                    'Hydropower','Transmission and Interties','Diesel Efficiency',
                    'Biomass for Heat (Cordwood)', 'Biomass for Heat (Pellet)',
                    'Residential ASHP', 'Non-Residential ASHP', 'Heat Recovery']:
            try:
                projs += cats[comp]
            except KeyError:
                pass
        
        
        pth = os.path.join(self.directory, com,
                    'Potential Projects'.replace(' ','_').replace('(','').replace(')','').lower() + '.html')
        with open(pth, 'w') as html:
            html.write(template.render( type = 'Potential Projects', 
                                    com = com ,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = self.get_summary_pages(),
                                    communities = self.get_all_coms(),
                                    potential_projects = projs,
                                    metadata = self.metadata,
                                    ))
                                        

        
        
        
    def make_plot_table (self, xs, ys = None, names = None, sigfig=0,
                         community = None, fname = None):
        """
        make a table
        
        inputs:
        outputs:    
            returns plotting_table, a table that can be used to make a google chart
        """
        if type(xs) == DataFrame and len(xs.columns) > 1:
            x_name = xs.columns[0]
            y_name = list(xs.columns[1:])
        else:
            # todo:fix order
            x_name = xs.keys()[0]
            y_name = ys.keys()
            xs.update(ys)
            xs = DataFrame(xs)[[x_name] + y_name]
            
        if names is None:
            names = [x_name] + y_name
        
        header = []
        years = None
        anno = None
        for name in names:
            if name == 'annotation':
                header.append("{type: 'string', role: 'annotation'}")
                anno = name
            else:
                header.append("{label: '"+name+"', type: 'number'}")
        
        if not anno is None:
            xs[anno+'_text'] = xs[anno] 
            header.append("{type: 'string', role: 'annotationText'}")    
        
        for name in xs.columns:
            if name.lower() == 'year':
                years = name
                xs[name] = xs[name].astype(int)
            
        if not years is None:
            xs = xs[xs[years] <= self.max_year]
            
        plotting_table = xs.round(sigfig).values.tolist()
        
        
        if not community is None and not fname is None:
            cols = [c for c in \
                    xs.columns if c.lower().find('annotation_text') == -1]
            xs[cols].round(sigfig).to_csv(os.path.join(self.directory,
                                             community,'csv', fname),
                                index=False)
        plotting_table.insert(0,header)
        #~ print plotting_table
        return plotting_table 
        
    def make_table (self, xs, ys = None, names = None, sigfig=0,
                    community = None, fname = None):
        """
        make a table
        
        inputs:
        outputs:    
            returns plotting_table, a table that can be used to make a google chart
        """
        if type(xs) == DataFrame and len(xs.columns) > 1:
            x_name = xs.columns[0]
            y_name = list(xs.columns[1:])
        else:
            # todo:fix order
            x_name = xs.keys()[0]
            y_name = ys.keys()
            xs.update(ys)
            xs = DataFrame(xs)[[x_name] + y_name]
            
        if names is None:
            names = [x_name] + y_name
        
        header = []
        years = None
        for name in names:
            header.append(name)
            
        for name in xs.columns:
            if name.lower() == 'year':
                years = name
                xs[name] = xs[name].astype(int)
            
        if not years is None:
            xs = xs[xs[years] <= self.max_year]
            
        plotting_table = xs.round(sigfig).values.tolist()
       
        if not community is None and not fname is None:
            cols = [c for c in \
                    xs.columns if c.lower().find('annotation_text') == -1]
            xs[cols].round(sigfig).to_csv(os.path.join(self.directory,
                                             community,'csv', fname),
                                index=False)
        
        plotting_table.insert(0,header)
        return plotting_table 
    
                                        


