from jinja2 import Environment, PackageLoader
import aaem.driver as driver
from pandas import concat, DataFrame, read_csv
import os
import shutil

from importlib import import_module
from aaem.components import comp_lib, comp_order
from aaem.constants import *
from aaem import __file__, __version__
from datetime import datetime

import numpy as np
import yaml
from pickle import PicklingError

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
        self.bad_data_msg = \
            "This community is known to have missing/incomplete data."
        self.bad_data_coms = []
        try:
            inputs = os.path.join(self.model_root, 'input_files')
            for d in os.listdir(inputs):
            
                if os.path.isdir(os.path.join(inputs,d)) and d.find('__') == -1:
                    
                    if len(os.listdir(os.path.join(inputs,d))) < 29:
                        self.bad_data_coms.append(d)       
        except:
            print "Could not analyze bad commuities"
            pass
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
        
        self.component_html = self.env.get_template('component.html')
        self.general_summaries_html = self.env.get_template('demo.html')
        self.potential_projects_html = \
                        self.env.get_template('potential_projects.html')
        self.no_results_html = self.env.get_template('no_results.html')
        self.index_html = self.env.get_template('index.html')
        self.comp_redir_html = self.env.get_template('intertie_redir.html')
        

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
        os.makedirs(os.path.join(self.directory, com.replace("'",""), 'csv'))
        self.overview(com)
        self.finances_demo_summary(com)
        self.consumption_summary(com)
        self.generation_summary(com)
        self.projects_summary(com)
        components = set(comp_order)
        
        it = self.results[com]['community data'].intertie
        if not it is None:
            if it == 'parent':
                components = set(["Wind Power", 'Solar Power',  'Hydropower',
                              'Transmission and Interties','Diesel Efficiency'])
            else:
                components = set(comp_order) - set(["Wind Power", 'Solar Power', 
                                                    'Hydropower',
                                                'Transmission and Interties',
                                                    'Diesel Efficiency'])
        
        
        re_dirs = set(comp_order) - components
        
        ## generate the component pages
        for comp in components:
            c_clean = comp.replace(' ','_').\
                           replace('(','').replace(')','').lower()
            #~ print comp
            try:
                ## try to run the components generate web summary function
                self.get_web_summary(comp_lib[comp])(self, com)
            except (AttributeError, RuntimeError) as e:
                ## if it cant be run 
                #~ print comp, e
                template = self.no_results_html
                #~ if comp in ['Solar Power','Wind Power','Heat Recovery'] :
                pth = os.path.join(self.directory, com.replace("'",""), c_clean +'.html')


                msg = None
                if com in self.bad_data_coms:
                    msg = self.bad_data_msg
                with open(pth, 'w') as html:
                    reason = self.results[com][comp].reason
                    if reason.lower() == 'ok':
                        reason = "The component has a bad motivator"
                    html.write(template.render( 
                                    type = comp, 
                                    com = com.replace("'",'') ,
                                    reason = reason,
                                    sections = self.get_summary_pages(),
                                    communities = self.get_cleanded_coms(),
                                    metadata = self.metadata,
                                    message = msg))
                                   
        ## geneate redirect pages for intertie related pages
        template = self.comp_redir_html
        for comp in re_dirs:
            c_clean = comp.replace(' ','_').\
                           replace('(','').replace(')','').lower()
            pth = os.path.join(self.directory, com.replace("'",""), c_clean +'.html')

            with open(pth, 'w') as html:
                
                parent = True
                intertie =  [i for i in self.results[com]['community data'].intertie_list if i != "''"]
                if it == "child":
                    parent = False
                    intertie = [ self.results[com]['community data'].parent +"_intertie"]
                    
                
                msg = None
                if com in self.bad_data_coms:
                    msg = self.bad_data_msg
    
                
                html.write(template.render( 
                                type = comp, 
                                com = com.replace("'",'') ,
                                sections = self.get_summary_pages(),
                                communities = self.get_cleanded_coms(),
                                metadata = self.metadata,
                                message = msg,
                                parent = parent,
                                intertie = intertie
                                ))



    def copy_etc (self):
        """
        copy all of the css stuff
        """
        pth = os.path.dirname(__file__)
        shutil.copytree(os.path.join(pth,'templates','css'),
                                        os.path.join(self.directory,'css'))
        shutil.copytree(os.path.join(pth,'templates','js'),
                                        os.path.join(self.directory,'js'))
        shutil.copytree(os.path.join(pth,'templates','fonts'),
                                        os.path.join(self.directory,'fonts'))
        shutil.copy(os.path.join(pth,'templates','summary.css'),self.directory)
        shutil.copy(os.path.join(pth,'templates','footer.css'),self.directory)
        shutil.copy(os.path.join(pth,'templates','dropdown.css'),self.directory)
        shutil.copy(os.path.join(pth,'templates','map.js'),self.directory)
        
        template = self.env.get_template('navbar.js')
        with open(os.path.join(self.directory,'navbar.js'), 'w') as html:
            html.write(template.render(communities = self.get_cleanded_coms(), regions=self.get_regions()))
        
        
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
    
    
    def get_cleanded_coms (self):
        """ Function doc """
        return sorted([k.replace("'",'') for k in self.get_coms()])
        
    def get_coms (self):
        return sorted([k for k in self.results.keys() if k.find('+') == -1])
    
    def get_regions (self):
        try:
            return self.regions 
        except AttributeError:
            pass
            
        
        temp = {}
        for com in self.get_coms():
            reg = self.results[com]['community data']\
                                            .get_item('community', 'region')
            try:
                temp[reg].append(com.replace("'",''))
            except:
                temp[reg] = [com.replace("'",'')]
                
        
        regions = []
        for k in sorted(temp.keys()):
            regions.append({"region":k, "communities":temp[k], 
                            "clean": k.replace(' ','_').replace('(','').\
                                replace(')','').replace('/','_').lower()})
        
        
        self.regions = regions
        #~ print self.regions
        return self.regions 
    
    
    def get_summary_pages (self):
        """
        get the summary pages for the secondary nav for the community summaries
        """
        return [{'name':'Summary', 'pages':['Overview',
                                            'Financial and Demographic',
                                            'Consumption',
                                            'Generation',
                                            'Potential Projects']}, 
                {'name':'Efficiency Projects',
                 'pages':["Residential Energy Efficiency",
                          "Non-residential Energy Efficiency",
                          "Water and Wastewater Efficiency"]
                },
                {'name':'Electricity Projects', 
                 'pages':["Wind Power",
                         'Solar Power',
                          'Hydropower',
                         'Transmission and Interties',
                         'Diesel Efficiency']
                },
                {'name':'Heating Projects', 
                 'pages':['Biomass for Heat (Cordwood)',
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
        self.generate_index()
        self.generate_regional_summaries()

        try:
            os.fork
            from multiprocessing import Process, Lock,active_children, cpu_count
            
            lock = Lock()
    
            for com in keys: #["Stebbins","Adak","Brevig_Mission"]:
                while len(active_children()) >= cpu_count():
                    continue
                lock.acquire()
                print com, "started"
                lock.release()
                Process(target=self.generate_com_mc, args=(com, lock)).start()
                
            while len(active_children()) > 0:
                continue
        except (ImportError, NotImplementedError, PicklingError, AttributeError):
            for com in keys: #["Stebbins","Adak","Brevig_Mission"]:
                start = datetime.now()
                self.generate_web_summaries(com)
                print com, datetime.now() - start
    
    
    def generate_com_mc (self, com, lock):
        """ Function doc """
        start = datetime.now()
        self.generate_web_summaries(com)
        lock.acquire()
        print com, datetime.now() - start
        lock.release()
    

    def generate_index (self):
        """ 
        generate index page
        """
        pth = os.path.join(self.directory, 'index.html')
        regions = []
        with open(pth, 'w') as html:
            html.write(self.index_html.render( type = 'index', 
                       #~ summary_pages = ['Summary'] + comp_order ,
                       #~ com = 'index',
                       sections = self.get_summary_pages(),
                       communities = self.get_cleanded_coms(),
                       regions = regions,
                       metadata = self.metadata,
                       in_root = True,
                                ))
                                     
                                        
    def finances_demo_summary (self, com):
        """ Function doc """
        template = self.general_summaries_html
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
            ep_table = self.make_plot_table(elec_price[['year','price']], names = ['year', 'electricity price ($/kWh)'], sigfig = 2,  community = com, fname = com+"_e_price.csv")
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
        d_table = self.make_plot_table(diesel[['year','Diesel Price ($/gal)','Heating Fuel ($/gal)']], sigfig = 2,  community = com, fname = com+"_d_price.csv")
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
        costs_table = self.make_plot_table(costs, sigfig = 2,  community = com, fname = com+"_costs.csv")
        
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

        msg = None
        if com in self.bad_data_coms:
            msg = self.bad_data_msg
            
        
        pth = os.path.join(self.directory, com.replace("'",""),
                    'Financial and Demographic'.replace(' ','_').replace('(','').replace(')','').lower() + '.html')
        with open(pth, 'w') as html:
            html.write(template.render( type = 'Financial and Demographic', 
                                com = com.replace("'",'') ,
                                charts = charts,
                                summary_pages = ['Summary'] + comp_order ,
                                sections = self.get_summary_pages(),
                                communities = self.get_cleanded_coms(),
                                metadata = self.metadata,
                                message = msg
                                ))
                                
                                
    def consumption_summary (self, com):
        """ Function doc """
        template = self.general_summaries_html
        res = self.results[com]
        charts = []
        
        
        HDD = res['community data'].get_item('community','HDD')
        charts.append({'name':'hdd', 
                'data': [[False, 'Heating Degree Days per year', 
                                                '{:,.0f}'.format(HDD)]],
                'title':'Heating Degree Days',
                'table': True,})
        
        
        r = res['Residential Energy Efficiency'] # res. eff. component
        rd = r.comp_specs['data'].T # res. data
        
        table = [[ True, "", "Number Houses","Avg. Sqft.", "Avg. EUI" ],
                 [ False, "BEES", 
                            '{:,.0f}'.format(float(rd["BEES Number"])),
                            '{:,.0f}'.format(float(rd['BEES Avg Area (SF)'])),
                            '{:,.4f}'.format(\
                                float(rd['BEES Avg EUI (MMBtu/sf)']))],
                 [ False, "Post-Retrofit", 
                            '{:,.0f}'.format(float(rd["Post-Retrofit Number"])),
                            '{:,.0f}'.format(\
                                float(rd['Post-Retrofit Avg Area (SF)'])),
                            '{:,.4f}'.format(\
                                float(rd['Post-Retrofit Avg EUI (MMBtu/sf)']))],
                 [ False, "Pre-Retrofit", 
                            '{:,.0f}'.format(r.opportunity_HH),  
                            '{:,.0f}'.format(float(\
                                        rd['Pre-Retrofit Avg Area (SF)'])), 
                            '{:,.4f}'.format(\
                                float(rd['Pre-Retrofit Avg EUI (MMBtu/sf)']))],
                ]
        
        charts.append({'name':'residential_buildings', 
                'data': table,
                'title':'Residential Buildings',
                'table': True,})
        
        
        
        
        
        nr = res['Non-residential Energy Efficiency']
        measurments = nr.buildings_df
        estimates = nr.comp_specs["com building data"].fillna(0)
        num = 0
        
        try:
            try:
                if 'Average' in set(estimates.ix['Average'].index):
                    num = len(estimates.ix['Average'])
                else:
                    num = 1
            except KeyError:
                pass
            
            
            total_sf = measurments['Square Feet'].sum()
            count = measurments['count'].sum()
            percent_sf =  total_sf/estimates['Square Feet'].sum()
            percent_id = float(count)/\
                          (count+num)
                     
            total = 0
            building_types={}
            for t in set(estimates.index):
                #~ k = t
                #~ if k == 'Average':
                    #~ k = 'Unknown'
                hf_used = (estimates['Fuel Oil'][t]/mmbtu_to_gal_HF + \
                        estimates['Natural Gas'][t]/mmbtu_to_Mcf + \
                        estimates['Propane'][t]/mmbtu_to_gal_LP + \
                        estimates['HW District'][t]/mmbtu_to_gal_HF +\
                        estimates['Biomass'][t]/mmbtu_to_cords).sum()
                total += hf_used
                building_types[t] = hf_used
            #~ print building_types
            
                
            
            
            table = [['name','value']]#[[False,'# Buildings',count+num],
             #~ [False,'Square feet', '{:,.0f}'.format(estimates['Square Feet'].sum())],
             #~ [False,'% Buildings identified', '{:,.2f}%'.format(percent_id*100)],
             #~ [False,'% Square feet measured','{:,.2f}%'.format(percent_sf*100)]]
            description = "There is a estimated total of " + \
                    '{:,.0f}'.format(estimates['Square Feet'].sum()) + \
                    " square feet for the " + str(int(count+num)) + \
                    " non-residential buildings in this community. " +\
                    '{:,.2f}%'.format(percent_id*100) + " of the buildings " +\
                    "have been identified. The others are assumed to exist. " +\
                    '{:,.2f}%'.format(percent_sf*100) + " of the assumed" +\
                    " square footage is from measured sources." +\
                    " The break down of heating fuel consumption by building" +\
                    " type is pesented in the pie chart"
             
            for t in building_types:
                n = t
                if n == 'Average':
                    n = 'Unknown'
                n = 'Consumption by ' + n 
                v = (building_types[t]/total)*100
                table.append([n,v])
                             
                          
            
            charts.append({'name':'non_residential_buildings', 
                'data': str(table),
                'title':'Non-residential Buildings',
                'pie': True,
                'plot':True,
                'type': "'pie'",
                'description': description})
        except (ZeroDivisionError):
            charts.append({'name':'non_residential_buildings', 
                'data': "No Building data avaialble." ,
                'title':'Non-residential Buildings'})
        
        
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
                                                                names = names, community = com, fname = com+"_consumption.csv" )
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
            

        diesel_consumption_table = self.make_plot_table(diesel_consumption, sigfig = 2,  community = com, fname = com+"_diesel_consumption.csv")
        charts.append({'name':'diesel_consumption', 'data': str(diesel_consumption_table).replace('nan','null'), 
                        'title':'Energy Consumption',
                        'type': "'percent'",
                        'stacked': True,'plot': True,})  
        #~ except AttributeError:
            #~ pass

        msg = None
        if com in self.bad_data_coms:
            msg = self.bad_data_msg
            
        pth = os.path.join(self.directory, com.replace("'",""),
                    'Consumption'.replace(' ','_').replace('(','').replace(')','').lower() + '.html')
        with open(pth, 'w') as html:
            html.write(template.render( type = 'Consumption', 
                                    com = com.replace("'",'') ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = self.get_summary_pages(),
                                    communities = self.get_cleanded_coms(),
                                    metadata = self.metadata,
                                    message = msg
                                    ))
        
        
    def generation_summary (self, com):
        """ Function doc """
        template = self.general_summaries_html
        res = self.results[com]
        charts = []
        
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
                                'type': "'kWh'",'plot': True,})  
        else:
            charts.append({'name':'generation',
                            'data': "No generation data available.",
                                'title':'generation',
                                'type': "'kWh'",})
        
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
                    'title':'Average Load',
                    'type': "'kW'",'plot': True,})
        else:
            charts.append({'name':'avg_load', 
                    'data': "No Consumption available to calculate average load", 
                    'title':'Average Load',
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
        line_loss_table = self.make_plot_table(line_loss[['year', 'annotation', "line losses"]],sigfig = 2,  community = com, fname = com+"_line_loss.csv")
        charts.append({'name':'line_loss', 'data': str(line_loss_table).replace('nan','null').replace('None','null'), 
                'title':'line losses',
                'type': "'percent'",'plot': True,})

        gen_eff_table = self.make_plot_table(line_loss[['year', 'annotation', 'diesel generation efficiency']],sigfig = 2, community = com, fname = com+"_generation_efficiency.csv")
        charts.append({'name':'generation_efficiency', 'data': str(gen_eff_table).replace('nan','null'), 
                'title':'Diesel Generation Efficiency',
                'type': "'gal/kWh'",'plot': True,})
                
                
        eff = res['community data'].get_item('community',
                                            'diesel generation efficiency')
        ph_data = res['community data'].get_item('Diesel Efficiency', 'data')
        try:
            num_gens = int(float(ph_data['Total Number of generators']))
        except ValueError:
            num_gens = ph_data['Total Number of generators']
        
        try:
            cap = '{:,.0f} kW'.format(float(ph_data['Total Capacity (in kW)']))
            c2 = float(ph_data['Total Capacity (in kW)'])
        except ValueError:
            c2 = 0
            cap = ph_data['Total Capacity (in kW)']
        try:
            largest = '{:,.0f} kW'.format(\
                                    float(ph_data['Largest generator (in kW)']))
        except ValueError:
            largest = ph_data['Largest generator (in kW)']
        
        size = ph_data['Sizing']
        
        try:
            ratio = float(c2)/ \
                        float(avg_load['Average Load']\
                        [avg_load['annotation'] == 'start of forecast']) 
        except (ValueError, UnboundLocalError):
            ratio = 0
                         
        hr_data = res['community data'].get_item('Heat Recovery', 
                                                  'estimate data')
        hr_opp = hr_data['Waste Heat Recovery Opperational']
        hr_ava = hr_data['Est. current annual heating fuel gallons displaced']
        if type(hr_ava) is str or np.isnan(hr_ava):
            hr_ava = 0
            
        wind = res['community data'].get_item('Wind Power', 
                                                  'resource data')
                                                  
        w_cap = float(wind['existing wind'])
        
        w_fac = float(wind['assumed capacity factor'])
        
        
            
        solar = res['community data'].get_item('Solar Power', 
                                                  'data')
                                                  
        s_cap = float(solar['Installed Capacity'])
        s_pv = solar['Output per 10kW Solar PV']
        
        
        h_cap = float(res['community data'].get_item('community',
                                                'hydro generation capacity'))
                                        
        
        
        try:
            w_gen = float(res['community data'].get_item('community',
                'generation numbers')['generation wind'].iloc[-1:])
            s_gen = float(res['community data'].get_item('community',
                'generation numbers')['generation solar'].iloc[-1:])
                
            h_gen = float(res['community data'].get_item('community',
                'generation numbers')['generation hydro'].iloc[-1:])
            
            if  np.isnan(w_gen):
                w_gen = 0
                
            if  np.isnan(s_gen):
                s_gen = 0
                
            if  np.isnan(h_gen):
                h_gen = 0
                
            w_gen = '{:,.0f} kWh'.format(w_gen)
            h_gen = '{:,.0f} kWh'.format(h_gen)
            s_gen = '{:,.0f} kWh'.format(s_gen)
        except TypeError:
            w_gen = "unknown"
            s_gen = "unknown"
            h_gen = "unknown"
            
            
        
                                            
        table = [
            [True, "Power House", ""],
            [False, "Efficiency", '{:,.2f} kWh/gallon'.format(eff)],
            [False, "Total number of generators", num_gens],
            [False, "Total capacity (in kW)", cap], 
            [False, "Largest generator (in kW)", largest],
            [False, "Sizing", size],
            [False, "Ratio of total capacity to average load", 
                                                    '{:,.2f}'.format(ratio)],
            [True, "Heat Recovery", ""],
            [False, "Operational",  hr_opp],
            [False, 
                "Estimated number of gallons of heating oil displaced", 
                                            '{:,.0f} gallons'.format(hr_ava)],
            [True, "Wind Power", ""],
            [False, "Current wind capacity (kW)",  '{:,.0f} kW'.format(w_cap)],
            [False, "Current wind generation (kWh/year)", w_gen],
            [False, "Current wind capacity factor",  '{:,.2f}'.format(w_fac)],
            [True, "Solar Power", ""],
            [False, "Current solar capacity (kW)",  '{:,.0f} kW'.format(s_cap)],
            [False, "Current solar generation (kWh/year)",  s_gen],
            [False, "Current output per 10kW Solar PV", '{:,.0f}'.format(s_pv)],
            [True, "Hydropower", ""],
            [False, "Current hydro capacity (kW)",  '{:,.0f} kW'.format(h_cap)],
            [False, "Current hydro generation (kWh/year)",  h_gen],
            
            ]

            
        charts.insert(0,{'name':'gen_summary', 'data':table, 
                'title':'Generation Overview',
                'table': True,})
                
        try:
            if res['community data'].intertie_list[0] != "''":
                table = [
                    [True, "Community", "Parent/Child"],
                    [False, res['community data'].parent, 'Parent']
                    ]
                
                
                for c in res['community data'].intertie_list:
                    if c == "''":
                        break
                    table.append([False,c,'Child'])
            
                charts.insert(0,{'name':'it_l', 'data':table, 
                    'title':'Intertied Communities',
                    'table': True,})
        except AttributeError:
            pass
        #~ else:
            #~ charts.insert(0,{'name':'it_l', 'data':"Community not on intertie",
                #~ 'title':'Intertied Communities'})
        
        msg = None
        if com in self.bad_data_coms:
            msg = self.bad_data_msg

        pth = os.path.join(self.directory, com.replace("'",""),
                    'Generation'.replace(' ','_').replace('(','').replace(')','').lower() + '.html')
        with open(pth, 'w') as html:
            html.write(template.render( type = 'Generation', 
                                    com = com.replace("'",'') ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = self.get_summary_pages(),
                                    communities = self.get_cleanded_coms(),
                                    metadata = self.metadata,
                                    message = msg
                                    ))
        
        
    def projects_summary (self, com):
        """ Function doc """
        template = self.potential_projects_html
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
                        
                if not comp in cats.keys():
                    cats[comp] = []
                    
                c = self.results[i][comp]
                ratio = c.get_BC_ratio()
                
                fs = 0
                lcoe_e = 0
                lcoe_hf = 0
                if (not type(ratio) is str):
                    fs = c.get_fuel_total_saved() 
                    if type(fs) in [list, np.array, np.ndarray]:
                        fs = fs[0]
                        
                    if type(c.levelized_cost_of_energy) is dict:
                        lcoe_e = c.levelized_cost_of_energy['kWh'] #* mmbtu_to_kWh
                        lcoe_hf = c.levelized_cost_of_energy['MMBtu'] * mmbtu_to_gal_HF
                    
                    elif comp in ["Wind Power",'Solar Power','Hydropower',
                                  'Transmission and Interties',
                                  'Diesel Efficiency']:
                        lcoe_e = c.levelized_cost_of_energy
                    else:
                        lcoe_hf = c.levelized_cost_of_energy
                
                
                
                net = c.get_NPV_net_benefit()
                if net == 'N/A': 
                    net = 0
                
                benefit = c.get_NPV_benefits()
                if benefit == 'N/A': 
                    benefit = 0
                    
                costs = c.get_NPV_costs()
                if costs == 'N/A': 
                    costs = 0
                
                if 'N/A' == ratio:
                    ratio = 0
  
                
                try:
                    name = c.comp_specs['project details']['name']
                except (KeyError, TypeError):
                    name = comp
                if name == 'None':
                    name = comp
                
                name = name.decode('unicode_escape').encode('ascii','ignore')
            
            

                cats[comp].append({'name': name,
                              'sucess': True if ratio > 1.0 else False,
                              'comp':comp,
                              'benefits': '${:,.0f}'.format(benefit),
                              'costs': '${:,.0f}'.format(costs),
                              'net': '${:,.0f}'.format(net),
                              'ratio': '{:,.2f}'.format(ratio),
                              'lcoe_e':'${:,.2f}'.format(lcoe_e),
                        'lcoe_hf':'${:,.2f}'.format(lcoe_hf/mmbtu_to_gal_HF),
                              'fuel_saved': '{:,.0f}'.format(fs)})
         
        projs =[]
        for comp in ["Residential Energy Efficiency", # start eff
                     "Non-residential Energy Efficiency",
                     "Water and Wastewater Efficiency", 
                        "Wind Power", 'Solar Power', # start elec
                     'Hydropower','Transmission and Interties',
                     'Diesel Efficiency',
                        'Biomass for Heat (Cordwood)',  # start heat
                    'Biomass for Heat (Pellet)',
                    'Residential ASHP', 'Non-Residential ASHP', 
                    'Heat Recovery']:
            try:
                projs += cats[comp]
            except KeyError:
                pass
        
        
        msg = None
        if com in self.bad_data_coms:
            msg = self.bad_data_msg
        
        pth = os.path.join(self.directory, com.replace("'",""),
                    'Potential Projects'.replace(' ','_').replace('(','').
                                            replace(')','').lower() + '.html')
        with open(pth, 'w') as html:
            html.write(template.render( type = 'Potential Projects', 
                                    com = com.replace("'",'') ,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = self.get_summary_pages(),
                                    communities = self.get_cleanded_coms(),
                                    potential_projects = projs,
                                    metadata = self.metadata,
                                    message = msg
                                    ))
                                    
    def overview (self, com):
        """ Function doc """
        template = self.general_summaries_html
        res = self.results[com]
        charts = []
        
        pop = res['community data'].get_item('forecast','population')\
                                    .ix[2010]['population']
        hh = res['Residential Energy Efficiency']\
                            .comp_specs['data'].ix['Total Occupied']
                            
        try:
            c_map = res['forecast'].c_map
            year = c_map[c_map['consumption_qualifier'] == 'M'].index.max()
        
            gen = '{:,.0f}'.format(res['forecast'].\
                                        generation.ix[year].values[0])
            gen_year = year
       
            con = '{:,.0f} kWh'.format(res['forecast'].\
                                        consumption.ix[year].values[0])
            con_year = year 
        except AttributeError:
            gen_year = ''
            con_year = ''
            gen = "unknown"
            con = gen
            
        diesel = res['community data'].get_item('community','diesel prices')
        fuel_year = diesel.start_year
        diesel_c = diesel.projected_prices[0]
        HF_c = diesel_c + res['community data'].get_item('community',
                                                        'heating fuel premium')
        
        diesel_c = '${:,.2f}/gallon'.format(diesel_c)
        HF_c = '${:,.2f}/gallon'.format(HF_c)
        
        elec_price = res['community data'].get_item('community',
                                                'electric non-fuel prices')
        if type( elec_price ) is str:
            elec_c = "unknown"
        else:
            elec_c = '${:,.2f}/kWh'.format(float(elec_price.iloc[0]))
           
           
        oil_year = res['Residential Energy Efficiency'].start_year
        if hasattr(res['Residential Energy Efficiency'],
                    'baseline_fuel_Hoil_consumption'):
            res_gal = res['Residential Energy Efficiency'].\
                                        baseline_fuel_Hoil_consumption[0]
            res_gal = '{:,.0f} gallons'.format(res_gal)
        else:
            res_gal = "unknown"
        
        
        if hasattr(res['Non-residential Energy Efficiency'], 
                    'baseline_fuel_Hoil_consumption'):
            nr_gal = res['Non-residential Energy Efficiency'].\
                                    baseline_fuel_Hoil_consumption
            
        else:
            nr_gal = 0
        
        if hasattr(res['Water and Wastewater Efficiency'], 
                    'baseline_fuel_Hoil_consumption'):
            nr_gal +=  res['Water and Wastewater Efficiency'].\
                                        baseline_fuel_Hoil_consumption[0]
        else:
           nr_gal += 0
           
        if nr_gal != 0:
            nr_gal = '{:,.0f} gallons'.format(nr_gal)
        else:
            nr_gal = "unknown"
            
        eff = res['community data'].get_item('community',
                                                'diesel generation efficiency')
        if hasattr(res['forecast'], 'generation_by_type'):
            if eff == 0:
                eff = np.nan
            
            utility = res['forecast'].\
                    generation_by_type["generation diesel"].iloc[0]
            utility /= eff
            utility = '{:,.0f} gallons'.format(utility)
        else:
            utility = "unknown"  
           
        
        if np.isnan(eff):
            eff = 0;
            
            
        try:
            yes = read_csv(os.path.join(self.model_root,'input_files', com, 'yearly_electricity_summary.csv'),comment='#')
            #~ print yes.columns
        except IOError: 
            yes = None
            
        if not yes is None:
            yes_years = yes[yes.columns[0]].values
            leff_year = int(max(yes_years))
            eff = '{:,.2f} kWh/gallons'.format(yes['efficiency'].values[-1])
            ll = '{:,.2f}%'.format(yes['line loss'].values[-1]*100)
        
            
            
        else:
            leff_year = ""
            eff = '{:,.2f} kWh/gallons'.format(eff)
            
            ll = res['community data'].get_item('community','line losses')
            try:
                ll = '{:,.2f}%'.format(ll*100)
            except:
                ll = "unknown"
        
        g_year = ""
        if hasattr(res['forecast'], 'generation_by_type'):
            if not hasattr(res['forecast'], 'generation_forecast_dataframe'):
                res['forecast'].generate_generation_forecast_dataframe()
            c_map = res['forecast'].c_map
            g_year = c_map[c_map['consumption_qualifier']\
                                                    == 'M'].index.max()
            
            generation = res['forecast'].\
                generation_forecast_dataframe[[
                                'generation_diesel [kWh/year]',
                                'generation_hydro [kWh/year]',
                                'generation_natural_gas [kWh/year]',
                                'generation_wind [kWh/year]',
                                'generation_solar [kWh/year]',
                                'generation_biomass [kWh/year]']].loc[g_year]
                                                                
            g_diesel = '{:,.0f} kWh'.format(generation['generation_diesel [kWh/year]'])
            g_hydro = '{:,.0f} kWh'.format(generation['generation_hydro [kWh/year]'])
            #~ g_ng = generation['generation_natural_gas [kWh/year]']
            g_wind = '{:,.0f} kWh'.format(generation['generation_wind [kWh/year]'])
            #~ g_solar = generation['generation_solar [kWh/year]']
            #~ g_biomass = generation['generation_biomass [kWh/year]']
            
        else:
            g_diesel = "unknown"
            g_hydro = "unknown"
            g_ng = "unknown"
            g_wind = "unknown"
            g_solar = "unknown"
            g_biomass = "unknown"
            
        try:
            al = int(con/hours_per_year)
        except:
            al = "unknown"
        
        table = [[ True, "Demographics", ""],
                 [ False, "Population 2010", int(pop)],
                 [ False, "Households 2010", int(hh)],
                 [ True, "Financial", ""],
                 [ False, "Diesel fuel cost " + str(fuel_year), diesel_c],
                 [ False, "Heating fuel cost " + str(fuel_year), HF_c],
                 [ False, "Electricity cost " + str(fuel_year), elec_c],
                 [ True, "Consumption", ""],
                 [ False, "Total electricity consumption " + str(con_year), con],
                 [ False, 
                    "Estimated residential heating fuel " + str(oil_year),
                    res_gal],
                 [ False, 
                    "Estimated non-residential heating fuel " + str(oil_year),
                    nr_gal],
                 [ False,
                    "Estimated utility diesel " + str(oil_year),
                    utility],
                 [ True, "Generation", ""],
                 [ False, "Total generation kWh " + str(gen_year), gen],
                 [ False, "Average load kW " + str(gen_year), al],
                 [ False, "Generation diesel kWh " + str(g_year), g_diesel],
                 [ False, "Generation hydro kWh " + str(g_year), g_hydro],
                 #~ [ False, "Generation natural gas kWh " + str(g_year), g_ng],
                 [ False, "Generation wind kWh " + str(g_year), g_wind],
                 #~ [ False, "Generation solar kWh " + str(g_year), g_solar],
                #~ [ False, "Generation biomass kWh " + str(g_year), g_biomass],
                 [ False, "Diesel generator efficiency " + str(leff_year) , eff],
                 [ False, "Line losses estimated " + str(leff_year), ll],
                ]
                 
                 
        
        charts.insert(0,{'name':'overview', 'data':table, 
                    'title': 'Community Overview',
                    'table': True,})
        
        
        
        
        
        
        try:
            goals = read_csv(os.path.join(self.model_root,'input_files', 
                                        '__goals_community.csv'),
                            comment='#', index_col=0)
        
            goals = goals.ix[com.replace('_intertie','').\
                                 replace('_',' ')].fillna('')
        except IOError: 
            goals = None
           
        if goals is None:
            charts.append({'name':'goals', 
                    'data':"Community Goals not avaialble", 
                    'title':'Community Goals',
                    })
        else:
            table = [[True,'Priority','Goal']]
            p = 1
            for g in goals['Priority 1':]:
                if g == '':
                    break
                #~ print type(g)
                table.append([False, p, g.decode('unicode_escape').\
                                          encode('ascii','ignore')])
                p += 1
            
            
            charts.append({'name':'goals', 'data':table, 
                    'title':'Community Goals',
                    'table': True,})
        
        it = self.results[com]['community data'].intertie
        if not it is None:
            intertie =  [i for i in res['community data'].\
                                                    intertie_list if i != "''"]
            table = [[True, 'Community', 'Primary or Secondary Generator'],
                     [False, res['community data'].parent, 'Primary']]
            for i in intertie:
                table.append([False, i, 'Secondary'])
                                                    
            charts.append({'name':'interties', 'data':table, 
                    'title':'Intertied Communities',
                    'table': True,})

            
        msg = None
        if com in self.bad_data_coms:
            msg = self.bad_data_msg
        
        pth = os.path.join(self.directory, com.replace("'",""),
                    'Overview'.replace(' ','_').replace('(','').replace(')','').lower() + '.html')
        with open(pth, 'w') as html:
            html.write(template.render( type = 'Overview', 
                                    com = com.replace("'",'') ,
                                    charts = charts,
                                    summary_pages = ['Summary'] + comp_order ,
                                    sections = self.get_summary_pages(),
                                    communities = self.get_cleanded_coms(),
                                    metadata = self.metadata,
                                    message = msg
                                    ))
                                    
    def generate_regional_summaries (self):
        """
        """
        template = self.general_summaries_html
        regions = self.get_regions()
        
        for reg in regions:
            charts = []
            name = reg['region']
            coms = reg['communities']
            
            
            table = []
            for com in coms:
                table.append({'url': com + "/overview.html", 
                                            'text':com.replace('_',' ')})
            charts.append({'name':'coms', 'data':table, 
                        'title':'Communities in region',
                        'links_list': True,})
            
        
            try:
                goals = read_csv(os.path.join(self.model_root,'input_files', 
                                            '__goals_regional.csv'),
                                comment='#', index_col=0)
            
                key = name
                if key == 'Copper River/Chugach':
                    key = 'Copper River'
                elif key == 'Kodiak':
                    key = 'Kodiak Region'
                goals = goals.ix[key].fillna('')
            except IOError: 
                goals = None
               
            if goals is None:
                charts.append({'name':'goals', 
                        'data':"Regional Goals not avaialble", 
                        'title':'Regional Goals',
                        })
            else:
                table = [[True,'Priority','Goal']]
                p = 1
                for g in goals['Priority 1':]:
                    if g == '':
                        break
                    #~ print type(g)
                    table.append([False, p, g.decode('unicode_escape').\
                                              encode('ascii','ignore')])
                    p += 1
                
                
                charts.append({'name':'goals', 'data':table, 
                        'title':'Regional Goals',
                        'table': True,})
    
            pth = os.path.join(self.directory,
                        name.replace(' ','_').replace('(','').replace(')','').replace('/','_').lower() + '.html')
            with open(pth, 'w') as html:
                html.write(template.render( type = 'Region', 
                                        com = name ,
                                        charts = charts,
                                        summary_pages = [],
                                        sections = [],
                                        metadata = self.metadata,
                                        in_root=True
                                        ))
            
                                        

    def make_plot_table (self, xs, ys = None, names = None, sigfig=0,
                         community = None, fname = None):
        """
        make a table
        
        inputs:
        outputs:    
            returns plotting_table, a table that can be used to make a google 
        chart
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
                header.append("{label: '"+name[0].upper() + name[1:].lower()+"', type: 'number'}")
        
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
                                             community.replace("'",""),'csv', fname),
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
            returns plotting_table, a table that can be used to make a google 
        chart
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
    
                                        


