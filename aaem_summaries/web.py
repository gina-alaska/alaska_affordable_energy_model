from jinja2 import Environment, PackageLoader
import aaem.driver as driver
from pandas import concat, DataFrame, read_csv
import os
import shutil

from importlib import import_module
from aaem.components import comp_lib, comp_order
from aaem.constants import *
from aaem import  __version__ as model_version
from aaem_summaries import __file__, __version__

from datetime import datetime

import numpy as np
import yaml
from pickle import PicklingError
import copy

class WebSummary(object):
    """Tool for generating html web summaries """
    def __init__ (self, model_root, directory, tag = ''):
        """Tool for generating html web summaries
        
        Parameters
        ----------
        model_root: path
            path to model version to create summaries for
        directory: path
            output path
        tag: str
            resultes tag to use
        """
        self.max_year = 2040
        self.viable_communities = {"Residential Energy Efficiency":set(),
              "Non-residential Energy Efficiency":set(),
              "Water and Wastewater Efficiency":set(),
              "Wind Power":set(),
              'Solar Power':set(),
              'Biomass for Heat (Cordwood)':set(),
              'Biomass for Heat (Pellet)':set(),
              'Residential ASHP':set(),
              'Non-Residential ASHP':set(),
              'Hydropower':set(),
              'Transmission and Interties':set(),
              'Heat Recovery':set(),
              'Diesel Efficiency':set()}
        self.model_root = model_root
        model = driver.Driver(self.model_root)
        self.results = model.load_results(tag)
        #~ print self.results
        self.bad_data_msg = \
            "This community is known to have missing/incomplete data."
        self.bad_data_coms = []
        try:
            for c in self.get_coms():
                if len(self.results[c]['community data'].get_item('community',
                    'utility info')) == 0:
                    self.bad_data_coms.append(c)
            
        except StandardError as e:
            #~ print e
            print "Could not analyze bad commuities"
            pass
        self.version = model_version
        self.version_summary = __version__
        try:
            with open(os.path.join(self.model_root,'config',
                '__metadata','preprocessor_metadata.yaml'), 'r') as md:
                self.data_version = yaml.load(md)['data version']
        except IOError:
            self.data_version = 'UNKNOWN'
            
        self.metadata = {"date": datetime.strftime(datetime.now(),'%Y-%m-%d'),
                         "version": self.version, 
                         "data_version": self.data_version,
                         "summary_version": self.version_summary}
        
        self.directory = directory
        try:
            os.makedirs(self.directory)
        except OSError as e:
            #~ print e
            pass
        #~ print "fine"
        self.env = Environment(loader=PackageLoader('aaem_summaries','templates/'))
        
        self.component_html = self.env.get_template('component.html')
        self.general_summaries_html = self.env.get_template('demo.html')
        self.potential_projects_html = \
                        self.env.get_template('potential_projects.html')
        self.no_results_html = self.env.get_template('no_results.html')
        self.index_html = self.env.get_template('index.html')
        self.comp_redir_html = self.env.get_template('intertie_redir.html')
        self.tech_html = self.env.get_template('tech.html')
        self.get_ratios_greater_than_limit()
    
    #### -----------------------------------------------------------------------
    #### Driving functions
    #### -----------------------------------------------------------------------
    def generate_all (self):
        """Generate all html summaries and support files"""
        keys = sorted([k for k in self.results.keys() if k.find('+') == -1])
        self.copy_static()
        self.generate_tech_summaries()
        self.create_index()
        self.generate_regional_summaries()
        #~ import sys
        #~ sys.exit()
        try:
            ### try Multiprocessing
            os.fork
            from multiprocessing import Process, Lock,active_children, cpu_count
            
            lock = Lock()
    
            for com in ['Adak']: #keys: #["Stebbins","Adak","Brevig_Mission"]:
                while len(active_children()) >= cpu_count():
                    continue
                lock.acquire()
                print com, "started"
                lock.release()
                Process(
                    target=self.multiprocess_community_summaries,
                    args=(com, lock)
                ).start()
                
            while len(active_children()) > 0:
                continue
        except (ImportError,
            NotImplementedError,
            PicklingError,
            AttributeError):
            ### do it one at a time.
            for com in keys: #["Stebbins","Adak","Brevig_Mission"]:
                start = datetime.now()
                self.generate_community_summaries(com)
                print com, datetime.now() - start
    
    
    #### -----------------------------------------------------------------------
    #### "index" pages
    #### -----------------------------------------------------------------------
    def create_index (self):
        """Generate index page
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
    
    def generate_regional_summaries (self):
        """Generate regional summaries
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
                name.replace(' ','_').replace('(','').replace(')','').\
                replace('/','_').lower() + '.html')
            with open(pth, 'w') as html:
                html.write(template.render( type = 'Region', 
                                        com = name ,
                                        charts = charts,
                                        summary_pages = [],
                                        sections = [],
                                        metadata = self.metadata,
                                        in_root=True
                                        ))
   
    def generate_tech_summaries (self):
        """Generate tech related summaries
        """
        for comp in comp_order:
            #~ try:
            coms = str(list(self.viable_communities[comp])).replace('_', ' ')
            #~ coms = coms.decode('unicode_escape').encode('ascii','ignore')
            clean = comp.replace('(','').replace(')','').replace(' ','_')
            cols = self.get_tech_summary(comp_lib[comp]).columns
            
            regions = self.get_tech_summary(comp_lib[comp]).index
            
            data = []
            for row in regions:
                d = self.get_tech_summary(comp_lib[comp]).ix[row].values
                
                
                r = [row] 
                for i in range(len(d)):
                    ## cols 2 & 3 are in $
                    if i == 2 or i == 3:
                        r.append('${:,.0f}'.format(d[i]))
                    else:
                        r.append('{:,.0f}'.format(d[i]))
                data.append(r)
            
            
            
            template = self.tech_html
            with open(os.path.join(self.directory,
                                    clean+'.html'), 'w') as html:
                html.write(template.render(coms=coms,
                                    metadata = self.metadata,
                                    columns = ['Region'] + list(cols),
                                    data = data,
                                    tech = comp,
                                    bc_limit = 1.0,
                                    in_root=True))
                
            #~ except StandardError as e:
                #~ print e
                
                
    #### -----------------------------------------------------------------------
    #### community summaries
    #### ----------------------------------------------------------------------- 
    def generate_community_summaries (self, com):
        """generate all summaries for a community
        
        Parameters
        ----------
        com: str
            a community or project in the results
        """
        os.makedirs(os.path.join(self.directory, com.replace("'",""), 'csv'))
        
        ## General summaries
        self.create_community_overview(com)
        self.create_community_finances_demo_summary(com)
        self.create_community_consumption_summary(com)
        self.create_community_generation_summary(com)
        self.create_community_projects_summary(com)
        
        ## tech/componet summaries
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
                print e
                template = self.no_results_html
                pth = os.path.join(
                    self.directory,
                    com.replace("'",""),
                    c_clean +'.html'
                )
                msg = None
                if com in self.bad_data_coms:
                    msg = self.bad_data_msg
                with open(pth, 'w') as html:
                    reason = self.results[com][comp].reason
                    if reason.lower() == 'ok':
                        reason = "The component could not be run"
                    # make a proper sentence.
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
            pth = os.path.join(
                self.directory, 
                com.replace("'",""),
                c_clean +'.html'
            )

            with open(pth, 'w') as html:
                parent = True
                intertie = self.results[com]['community data'].\
                    get_item('community','intertie')
                if it == "child":
                    parent = False
                    intertie = [ intertie[0] +"_intertie"]
                    
                msg = None
                if com in self.bad_data_coms:
                    msg = self.bad_data_msg
    
                html.write(
                    template.render( 
                        type = comp, 
                        com = com.replace("'",'') ,
                        sections = self.get_summary_pages(),
                        communities = self.get_cleanded_coms(),
                        metadata = self.metadata,
                        message = msg,
                        parent = parent,
                        intertie = intertie
                    )
                )

    def create_community_overview (self, com):
        """Generate overview.html for the community
        
        Parameters
        ----------
        com: str
            community in question
        
        """
        template = self.general_summaries_html
        res = self.results[com]
        charts = []
        
        ## Community overview table
        #### Demographics section
        pop = res['community data'].get_item('community','population')\
            .ix[2010]['population']
        hh = res['Residential Energy Efficiency']\
            .comp_specs['data']['Total Occupied']
            
        #### Financial section
        ###### get data
        diesel = res['community data'].get_item('community','diesel prices')
        fuel_year = diesel.index[0]
        diesel_c = float(diesel.ix[fuel_year])
        HF_c = diesel_c + \
            res['community data'].get_item('community','heating fuel premium')
        elec_price = res['community data'].get_item('community',
            'electric non-fuel prices')
        ###### as strings
        diesel_c = '${:,.2f}/gallon'.format(diesel_c)
        HF_c = '${:,.2f}/gallon'.format(HF_c)
        
        elec_price = float(elec_price.ix[fuel_year])
        if np.isnan( elec_price ):
            elec_c = "unknown"
        else:
            elec_c = '${:,.2f}/kWh'.format(elec_price)
         
        #### Consumption & Generation sections
        ###### measured consumption & generation
        try:
            c_map = res['forecast'].consumption['consumption_qualifier']
            year = c_map[c_map == 'M'].index.max()

            gen = '{:,.0f} kWh'.format(res['forecast'].\
                generation.ix[year].values[0])
            gen_year = year
        
            int_con = res['forecast'].consumption['consumption'].ix[year]
            con = '{:,.0f} kWh'.format(int_con)
            con_year = year 
        except AttributeError:
            c_map = None
            gen_year = ''
            con_year = ''
            gen = "unknown"
            con = gen
          
        ###### forecasted residential (first year)
        oil_year = res['Residential Energy Efficiency'].start_year
        if hasattr(res['Residential Energy Efficiency'], 
            'baseline_fuel_Hoil_consumption'):
            res_gal = res['Residential Energy Efficiency'].\
                baseline_fuel_Hoil_consumption[0]
            res_gal = '{:,.0f} gallons'.format(res_gal)
        else:
            res_gal = "unknown"
        
        ###### forecasted non-residential (first year) -- NR + WWW
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
        
            
        
        ###### diesel generator efficiency
        eff = res['community data'].get_item('community',
            'diesel generation efficiency')
         
        ###### forecasted utility diesel (first year)    
        if hasattr(res['forecast'], 'generation'):
            if eff == 0:
                eff = np.nan
            
            utility = res['forecast'].generation["generation diesel"].iloc[0]
            utility /= eff
            utility = '{:,.0f} gallons'.format(utility)
        else:
            utility = "unknown"  
           
        if np.isnan(eff):
            eff = 0;
            
        
        ###### efficiency and line loss
        yes = res['community data'].get_item('community','utility info')    
        
        try:
            leff_year = int(max(yes.index))
            eff = '{:,.2f} kWh/gallons'.format(yes['efficiency'].values[-1])
            ll = '{:,.2f}%'.format(yes['line loss'].values[-1]*100)
        except ValueError:
            leff_year = ""
            eff = res['community data']\
                .get_item('community','diesel generation efficiency')
            eff = '{:,.1f} kWh/gallons'.format(eff)
            ll = "unknown"
            
        
                #~ res['forecast'].generate_generation_forecast_dataframe()
        #~ c_map = res['forecast'].consumption['consumption_qualifier']
        if not c_map is None:
            g_year = c_map[c_map == 'M'].index.max()
                
            generation = res['forecast'].\
                generation[[
                    'generation diesel',
                    'generation hydro',
                    'generation natural gas',
                    'generation wind',
                    'generation solar',
                    'generation biomass'
                ]].loc[g_year]
                                                                    
            g_diesel = '{:,.0f} kWh'.\
                format(generation['generation diesel'])
            g_hydro = '{:,.0f} kWh'.\
                format(generation['generation hydro'])
            #~ g_ng = generation['generation natural gas']
            g_wind = '{:,.0f} kWh'.\
                format(generation['generation wind'])
            #~ g_solar = generation['generationsolar']
            #~ g_biomass = generation['generation biomass']
                
        else:
            g_year = ''
            g_diesel = "unknown"
            g_hydro = "unknown"
            #~ g_ng = "unknown"
            g_wind = "unknown"
            #~ g_solar = "unknown"
            #~ g_biomass = "unknown"
            
        try:
            al = str(int(int_con/hours_per_year))  + ' kW'
        except StandardError as e:
            #~ print e
            al = "unknown"
        
        ### create table
        fuel_year = '(' + str(fuel_year) + ')'
        con_year = '(' + str(con_year) + ')'
        oil_year = '(' + str(oil_year) + ')'
        gen_year = '(' + str(gen_year) + ')'
        g_year = '(' + str(g_year) + ')'
        leff_year = '(' + str(leff_year) + ')'
        
        if res['community data'].intertie != 'child':
            table = [
             [ False, "<b>Demographics</b>", "", "[DIVIDER]",
                "<b>Generation</b>", ""],
             [ False, "Population (2010)", int(pop),"[DIVIDER]", 
                "Total generation " + str(gen_year), gen],
             [ False, "Households (2010)", int(hh),"[DIVIDER]", 
                "Average load " + str(gen_year), al],
             [ False, "<b>Financial</b>", "","[DIVIDER]", 
                "Generation from diesel " + str(g_year), g_diesel],
             [ False, "Forecasted diesel fuel cost " + str(fuel_year),
                diesel_c,"[DIVIDER]", 
                "Generation from hydropower " + str(g_year), g_hydro],
             [ False, "Forecasted heating fuel cost " + str(fuel_year),
                HF_c, "[DIVIDER]",
                "Generation from wind " + str(g_year), g_wind],
             [ False, "Forecasted electricity cost " + str(fuel_year),
                elec_c,"[DIVIDER]",  
                "Diesel generator efficiency " + str(leff_year) , eff],
             [ False, "<b>Consumption</b>", "", "[DIVIDER]",
                "Line losses estimated " + str(leff_year), ll],
             [ False, "Total electricity consumption " + str(con_year), con,
                "[DIVIDER]",'',''],
             [ False, 
                "Estimated residential heating fuel " + str(oil_year),
                res_gal, "[DIVIDER]",'',''],
             [ False, 
                "Estimated non-residential heating fuel " + str(oil_year),
                nr_gal, "[DIVIDER]",'',''],
             [ False,
                "Estimated utility diesel " + str(oil_year),
                utility, "[DIVIDER]",'',''],
        ]
        else:
            # -> parent is in first position of 'intertie' list
            parent = res['community data'].get_item('community','intertie')[0]
            link = '../' + parent.replace(' ','_') +\
                "_intertie/overview.html"
            link_text = "See " + parent + " intertie"
            link_element = '<a href="' + link + '">' + link_text + '</a>'
            table = [
             [ False, "<b>Demographics</b>", "", "[DIVIDER]",
                "<b>Generation</b>", ""],
             [ False, "Population (2010)", int(pop),"[DIVIDER]",
                "Total generation " + str(gen_year), link_element],
             [ False, "Households (2010)", int(hh),"[DIVIDER]",
                "Average load " + str(gen_year), link_element],
             [ False, "<b>Financial</b>", "","[DIVIDER]",
                "Generation from diesel " + str(g_year), link_element],
             [ False,
                "Forecasted diesel fuel cost " + str(fuel_year),
                diesel_c,"[DIVIDER]",
                "Generation from hydropower " + str(g_year), link_element],
             [ False,
                "Forecasted heating fuel cost " + str(fuel_year),
                 HF_c, "[DIVIDER]", "Generation from wind " + str(g_year),
                link_element],
             [ False, "Forecasted electricity cost " + str(fuel_year),
                elec_c,"[DIVIDER]",
                "Diesel generator efficiency " + str(leff_year), link_element],
             [ False, "<b>Consumption</b>", "", "[DIVIDER]",
                "Line losses estimated " + str(leff_year),
                link_element],
             [ False, "Total electricity consumption " + str(con_year), 
                link_element, 
                "[DIVIDER]", "",""],#,'',''],
             [ False, 
                "Estimated residential heating fuel " + str(oil_year),
                res_gal, "[DIVIDER]",'',''],
             [ False, 
                "Estimated non-residential heating fuel " + str(oil_year),
                nr_gal, "[DIVIDER]",'',''],
             [ False,
                "Estimated utility diesel " + str(oil_year),
                link_element,
                "[DIVIDER]",'',''],
        ]     
                 
        #### insert into page
        charts.insert(0,{'name':'overview', 'data':table, 
                    'title': 'Community Overview',
                    'table': True,})
        
        ## END community overview table
        
        
        
        #### Goals Table
        goals = res['community data'].get_item('community','community goals')
         
        if goals == []:
            goals = None
           
        if goals is None:
            charts.append({'name':'goals', 
                    'data':"Community Goals not avaialble", 
                    'title':'Community Goals',
                    })
        else:
            table = [[True,'Priority','Goal']]
            p = 1
            for g in goals:
                table.append([False, p, g])
                p += 1
            charts.append({'name':'goals', 'data':table, 
                    'title':'Community Goals',
                    'table': True,})
        
        ## Intertie Info
        it = self.results[com]['community data'].intertie
        if it != 'not in intertie':
            intertie = res['community data'].get_item('community','intertie')
            table = [[True, 'Community', 'Primary or Secondary Generator'],
                     [False, intertie[0], 'Primary']]
            for i in intertie[1:]:
                table.append([False, i, 'Secondary'])
                                                    
            charts.append({'name':'interties', 'data':table, 
                    'title':'Intertied Communities',
                    'table': True,})

            
        msg = None
        if com in self.bad_data_coms:
            msg = self.bad_data_msg
        
        pth = os.path.join(self.directory, com.replace("'",""),
                    'Overview'.replace(' ','_').replace('(','').\
                    replace(')','').lower() + '.html')
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
                                    
    def create_community_finances_demo_summary (self, com):
        """Generate financial_and_demographic.html for the community
        
        Parameters
        ----------
        com: str
            community in question
        
        """
        template = self.general_summaries_html
        res = self.results[com]
        
        ## Population
        population = res['community data'].get_item('community','population')
        p1 = population
        p1['year'] = p1.index
        population_table = self.make_plot_table(p1[['year','population']], 
            community = com, fname = com+"_population.csv")
        #~ print com
        
        charts = [
        {'name':'population',
         'data': str(population_table).replace('nan','null'), 
         'title': 'Population Forecast',
         'type': "'people'",
         'plot': True,},
            ]
        
        ## Electric price chart
        elec_price = \
            res['community data'].get_item('community', 
            'electric non-fuel prices')
        elec_price['year'] = elec_price.index
        elec_price.columns = ['price','year']
        
        start_year = elec_price.index[0]
        utility_data = \
            res['community data'].get_item('community', 'utility info')
       
        measured_data = utility_data[['residential rate']]
        measured_data.columns = ['price']
        measured_data['year'] = utility_data.index
        
        elec_price = concat([measured_data,elec_price])
        
        elec_price['annotation'] = np.nan 
        elec_price['annotation'][start_year] = 'start of forecast'
        elec_price = elec_price[['year','annotation','price']]
        elec_price.columns = ['year','annotation','Electricity price ($/kwh)']

        ep_table = self.make_plot_table(
            elec_price,
            sigfig = 2,
            community = com, 
            fname = com + "_e_price.csv")
        charts.append({
            'name':'e_price', 
            'data': str(ep_table).replace('nan','null'), 
            'title':'Electricity Price ($/kWh)',
            'type': "'currency'",
            'plot': True,
        })
        
        #~ else:
            #~ diesel_data = None
            #~ charts.append({'name':'e_price', 'data': "No electricity price for community.", 
                        #~ 'title':'Electricity Price ($/kWh)',
                        #~ 'type': "'currency'",})
        
        ## Diesel & fuel Prices chart
        diesel_data = utility_data[['diesel price']]
        
        diesel_data['year'] = utility_data.index

        diesel = res['community data'].get_item('community','diesel prices')
        diesel.columns = ['Diesel Price ($/gal)']

        diesel['year'] = diesel.index
        
        #~ print diesel
        diesel['Heating Fuel ($/gal)'] = \
            diesel['Diesel Price ($/gal)'] + \
            res['community data'].get_item('community','heating fuel premium')
        
        start_year = diesel.index[0]

        m_data = res['community data'].get_item('community',
            'heating fuel prices')
        
        m_data.columns = ['Heating Fuel ($/gal)']

        diesel_data = diesel_data.set_index('year')
        m_data['Diesel Price ($/gal)'] = diesel_data['diesel price']
        m_data['year'] = m_data.index

        diesel = concat([m_data,diesel])
        #~ except IOError as e:
            #~ print e
            #~ pass
        #~ if not diesel_data is None:
            #~ for row in diesel_data:
                #~ diesel['Diesel Price ($/gal)'].ix[row['year']] = \
                                                            #~ row['diesel_price']
        #~ print diesel
        try:
            diesel['annotation'] = np.nan 
            diesel['annotation'][start_year] = 'start of forecast'
        except StandardError as e:
            diesel['annotation'] = np.nan 
            diesel['annotation'][2016.0] = 'start of forecast'
            #~ print diesel
            #~ print str(e), '<-------------------->', com
        
        d_table = self.make_plot_table(
            diesel[['year',
                'annotation','Diesel Price ($/gal)',
                'Heating Fuel ($/gal)']], 
            sigfig = 2, 
            community = com, 
            fname = com+"_d_price.csv")
        charts.insert(-1,{
            'name':'d_price',
            'data': str(d_table).replace('nan','null'), 
            'title':'Fuel Price',
            'type': "'currency'",
            'plot': True,})  
                        
        
        
        ## save page
        msg = None
        if com in self.bad_data_coms:
            msg = self.bad_data_msg
            
        
        pth = os.path.join(self.directory, com.replace("'",""),
            'Financial and Demographic'.replace(' ','_').\
            replace('(','').replace(')','').lower() + '.html')
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
                                
    def create_community_consumption_summary (self, com):
        """Generate consumption.html for the community
        
        Parameters
        ----------
        com: str
            community in question
        
        """
        template = self.general_summaries_html
        res = self.results[com]
        charts = []
        
        ## Heating degree day chart
        HDD = res['community data'].get_item('community','heating degree days')
        charts.append({'name':'hdd', 
                'data': [[False, 'Heating Degree Days per year', 
                                                '{:,.0f}'.format(HDD)]],
                'title':'Heating Degree Days',
                'table': True,})
        
        ## Residential building chart
        r = res['Residential Energy Efficiency'] # res. eff. component
        rd = r.comp_specs['data'] # res. data
        
        table = [[ True, "", "Number Houses",
                        "Houshold Avg. Square Feet",
                         "Avg. EUI" ],
                 [ False, "BEES", 
                            '{:,.0f}'.format(float(rd["BEES Number"])),
                            '{:,.0f}'.format(float(rd['BEES Avg Area (SF)'])),
                            '{:,.2f}'.format(\
                                float(rd['BEES Avg EUI (MMBtu/sf)']))],
                 [ False, "Post-Retrofit", 
                            '{:,.0f}'.format(float(rd["Post-Retrofit Number"])),
                            '{:,.0f}'.format(\
                                float(rd['Post-Retrofit Avg Area (SF)'])),
                            '{:,.2f}'.format(\
                                float(rd['Post-Retrofit Avg EUI (MMBtu/sf)']))],
                 [ False, "Pre-Retrofit", 
                            '{:,.0f}'.format(r.opportunity_HH),  
                            '{:,.0f}'.format(float(\
                                        rd['Pre-Retrofit Avg Area (SF)'])), 
                            '{:,.2f}'.format(\
                                float(rd['Pre-Retrofit Avg EUI (MMBtu/sf)']))],
                ]
        
        charts.append({'name':'residential_buildings', 
                'data': table,
                'title':'Residential Buildings',
                'table': True,})
        
        
        ## Non-res pie chart
        nr = res['Non-residential Energy Efficiency']
        measurments = nr.buildings_df
        estimates = copy.copy(nr.comp_specs["building inventory"]).fillna(0)
        num = 0
        if len(estimates) != 0:
            estimates = estimates.set_index('Building Type')
            estimates = estimates.astype(float)
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
                    '{:,.1f}%'.format(percent_id*100) + " of the buildings " +\
                    "have been identified. The others are assumed to exist. " +\
                    '{:,.1f}%'.format(percent_sf*100) + " of the assumed" +\
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
                             
                          
            #~ print table
            charts.append({'name':'non_residential_buildings', 
                'data': str(table),
                'title':'Non-residential Buildings',
                'pie': True,
                'plot':True,
                'type': "'pie'",
                'description': description})
        else:
            charts.append({'name':'non_residential_buildings', 
                'data': "No Building data avaialble." ,
                'title':'Non-residential Buildings'})
        
        ## Consumption chart
        if res['community data'].intertie == 'child':
            parent = res['community data'].get_item('community','intertie')[0]
            url = '../' + parent.lower()  + "_intertie/consumption.html"
            
            charts.append({'name':'consumption', 'data': 
                                [{'url': url, 
                                    'text': "See " + parent + \
                                     " intertie for consumption plot for" + \
                                     " all communities on the intertie."}
                                    ],
                                'title':'Electricity Consumed',
                                'links_list': True,})
                                
        elif hasattr(res['forecast'], 'consumption'):
           
            consumption = res['forecast'].consumption
            #~ print consumption 
            cols = ['year',
                "consumption",
                'consumption residential',
                'consumption non-residential']
            names = ['Year', 'Total', 'Residential', 'Non-residential']
            
            consumption['year'] = consumption.index
            c_map = res['forecast'].consumption['consumption_qualifier']
            annotation = c_map[c_map == 'M'].index.max() + 1
            
            consumption['annotation'] = np.nan 
            consumption['annotation'][annotation] = 'start of forecast'
            
            #~ print consumption 
            
            names.insert(1, 'annotation')
            cols.insert(1, 'annotation')
        
            consumption_table = self.make_plot_table(
                consumption[cols] ,
                names = names, 
                community = com, 
                fname = com+"_consumption.csv" 
            )
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
            
        ## energy consumption pie chart
        diesel_consumption = DataFrame(
            index=range(res['Residential Energy Efficiency'].start_year,
            res['Residential Energy Efficiency'].end_year + 1 ))
        
        #~ print res['Residential Energy Efficiency'].end_year
        diesel_consumption['year']=diesel_consumption.index
        #~ print diesel_consumption
        if hasattr(res['Residential Energy Efficiency'],
                    'baseline_fuel_Hoil_consumption'):
            diesel_consumption['Residential Heating Oil (gallons)'] = \
                                        res['Residential Energy Efficiency'].\
                                        baseline_fuel_Hoil_consumption
        else:
            diesel_consumption['Residential Heating Oil (gallons)'] = np.nan
        
        
        if hasattr(res['Non-residential Energy Efficiency'], 
                    'baseline_fuel_Hoil_consumption'):
            diesel_consumption['Non-residential Heating Oil (gallons)'] = \
                                    res['Non-residential Energy Efficiency'].\
                                    baseline_fuel_Hoil_consumption
        else:
            diesel_consumption['Non-residential Heating Oil (gallons)'] = np.nan
        
        if hasattr(res['Water and Wastewater Efficiency'], 
                    'baseline_fuel_Hoil_consumption'):
            diesel_consumption['Water/Wastewater Heating Oil (gallons)'] = \
                                        res['Water and Wastewater Efficiency'].\
                                        baseline_fuel_Hoil_consumption
        else:
            diesel_consumption['Water/Wastewater Heating Oil (gallons)'] =\
                np.nan
            
        if hasattr(res['forecast'], 'generation'):
            eff = res['community data'].get_item("community",
                                            "diesel generation efficiency")
            if eff == 0:
                eff = np.nan
                
            #~ print res['forecast'].generation["generation diesel"]
            diesel_consumption['Utility Diesel (gallons)'] = \
                res['forecast'].generation["generation diesel"] / eff
            #~ diesel_consumption['Utility Diesel(gallons)']
        else:
            diesel_consumption['Utility Diesel (gallons)'] = np.nan
         
        diesel_consumption = diesel_consumption[['year'] + \
                list(diesel_consumption.columns)[1:][::-1]]
        

        if not diesel_consumption[diesel_consumption.columns[1:]]\
            .isnull().all().any():    
            
            diesel_consumption_table = self.make_plot_table(
                diesel_consumption, 
                sigfig = 2, 
                community = com, 
                fname = com+"_diesel_consumption.csv"
            )
            
            
            dt2 = [[diesel_consumption_type] for \
                diesel_consumption_type in diesel_consumption.columns]
            for idx in range(len(dt2)):
                dt2[idx].append(float(diesel_consumption[dt2[idx][0]].iloc[0]))
            diesel_consumption_table = dt2[1:]
            diesel_consumption_table.insert(0,['name','value'])
            
            charts.append({'name':'diesel_consumption',
                            'data': str(diesel_consumption_table),
                            'title':'Energy Consumption by sector',
                            'pie': True,
                            'plot':True,
                            'type': "'pie'",})  
        else:
            charts.append({
                'name':'diesel_consumption',
                'data': 'Data not available',
                'title':'Energy Consumption by sector',
            })    
        
        ## costs by sector pie chart
        ## ========================= Start Energy costs by Sector ==============
        costs = DataFrame(
            index=range(res['Residential Energy Efficiency'].start_year,
                        res['Residential Energy Efficiency'].end_year + 1))
                            
        costs['year']=costs.index
        #~ costs_data = False
        if hasattr(res['Residential Energy Efficiency'], 'baseline_kWh_cost'):
            costs['Residential Electricity'] = \
                res['Residential Energy Efficiency'].baseline_kWh_cost
        else:
            costs['Residential Electricity'] = np.nan
                              
        if hasattr(res['Non-residential Energy Efficiency'], 
            'baseline_kWh_cost'):
            costs['Non-residential Electricity'] = \
                res['Non-residential Energy Efficiency'].baseline_kWh_cost
        else:
            costs['Non-residential Electricity'] = np.nan
        
        if hasattr(res['Water and Wastewater Efficiency'], 'baseline_kWh_cost'):
            costs['Water/Wastewater Electricity'] = \
                res['Water and Wastewater Efficiency'].baseline_kWh_cost
        else: 
            costs['Water/Wastewater Electricity'] =  np.nan
            
        if hasattr(res['Residential Energy Efficiency'], 'baseline_HF_cost'):
            costs['Residential Heating Fuel'] = \
                res['Residential Energy Efficiency'].baseline_HF_cost
        else:
            costs['Residential Heating Fuel'] = np.nan
            
        if hasattr(res['Non-residential Energy Efficiency'], 
            'baseline_HF_cost'):
            costs['Non-residential Heating Fuel'] = \
                res['Non-residential Energy Efficiency'].baseline_HF_cost
        else:
            costs['Non-residential Heating Fuel'] = np.nan
            
        if hasattr(res['Water and Wastewater Efficiency'], 'baseline_HF_cost'):
            costs['Water/Wastewater Heating Fuel'] = \
                res['Water and Wastewater Efficiency'].baseline_HF_cost
        else:
            costs['Water/Wastewater Heating Fuel'] = np.nan
            

        costs = costs[['year'] + list(costs.columns)[1:][::-1]]
        if not costs[costs.columns[1:]].isnull().all().all():
       
            costs_table = self.make_plot_table(
                costs,
                sigfig = 2,
                community = com,
                fname = com+"_costs.csv")
            
            
            #~ print costs_table[0]
            #~ costs_table
            ct2 = [[cost_type] for cost_type in costs.columns]
            for idx in range(len(ct2)):
                ct2[idx].append(float(costs[ct2[idx][0]].iloc[0]))
            costs_table = ct2[1:]
            costs_table.insert(0,['name','value'])
            #~ if costs_data:
            charts.append({'name':'costs', 'data': str(costs_table),
                                'title':'Energy costs by Sector',
                                'type': "'percent'",
                                'pie': True,
                                'plot':True,
                                'type': "'pie'",})  
        else:
            charts.append({
                'name':'costs',
                'data': 'Data not available',
                'title':'Energy costs by Sector',})    
        ## ========================= END Energy costs by Sector ================

        ## save to page
        msg = None
        if com in self.bad_data_coms:
            msg = self.bad_data_msg
            
        pth = os.path.join(self.directory, com.replace("'",""),
            'Consumption'.replace(' ','_').\
            replace('(','').replace(')','').lower() + '.html')
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
        
    def create_community_generation_summary (self, com):
        """Generate generation.html for the community
        
        Parameters
        ----------
        com: str
            community in question
        
        """
        template = self.general_summaries_html
        res = self.results[com]
        charts = []
        
        
        ## Generation plot
        if res['community data'].intertie != 'child':    
            if hasattr(res['forecast'], 'generation'):
                generation = res['forecast'].generation[[
                    'generation diesel',
                    'generation hydro',
                    'generation natural gas',
                    'generation wind',
                    'generation solar',
                    'generation biomass'
                ]]
            
                     
                generation.columns = ['generation diesel [kWh/year]',
                                    'generation hydro [kWh/year]',
                                    'generation natural gas [kWh/year]',
                                    'generation wind [kWh/year]',
                                    'generation solar [kWh/year]',
                                    'generation biomass [kWh/year]']
                  
                 
                generation["Generation total [kWh/year]"] =  generation.sum(1)
                #~ print generation
                
                try:
                    generation\
                        ["Maximum expected generation solar [kWh/year]"] = \
                        res['Solar Power'].generation_proposed[0]
                except AttributeError:
                    generation["Maximum expected generation solar [kWh/year]"]\
                        = 0
                    
                generation["Maximum expected generation wind [kWh/year]"] = \
                    res['community data'].get_item('community',
                    'wind generation limit')
                generation["Maximum expected generation hydro [kWh/year]"] = \
                    res['community data'].get_item('community',
                    'hydro generation limit')
                
                                                                        
                generation['year']=generation.index
                generation = generation[['year'] + \
                    list(generation.columns)[:-1][::-1]]
                #~ print res['forecast'].consumption
                c_map = res['forecast'].consumption['consumption_qualifier']
                annotation = c_map[c_map == 'M'].index.max() + 1
                generation['annotation'] = np.nan 
                generation['annotation'][annotation] = 'start of forecast'
            
                generation = generation[['year','annotation'] +\
                    list(generation.columns[1:-1])]
                
                generation_table = self.make_plot_table(generation, sigfig = 2,
                                                community = com, 
                                                fname = com+"_generation.csv")
                charts.append({'name':'generation', 'data': 
                           str(generation_table).replace('nan','null'), 
                                'title':'generation',
                                'type': "'kWh'",'plot': True,
                            'dashed': ("series: {0: { lineDashStyle: [4, 2] },"
                                         "1: { lineDashStyle: [4, 2] },"
                                        "2: { lineDashStyle: [4, 2] },},"),})  
            
                    
                                 
            else:
                charts.append({'name':'generation',
                                'data': "No generation data available.",
                                    'title':'generation',
                                    'type': "'kWh'",})
            ## END generation
            
            #~ hh = DataFrame(costs['year'])
            #~ hh['households']=res['Residential Energy Efficiency'].households
            #~ print hh
            #~ hh_table = self.make_plot_table(hh)
            #~ charts.append({'name':'hh', 'data': str(hh_table).replace('nan','null'), 
                                #~ 'title':'housholds',
                                #~ 'type': "'households'"}) 
                
            ## Average load chart
            if hasattr(res['forecast'], 'consumption'):
                
                avg_load = res['forecast'].consumption
            
                names = ['Year', 'annotation', 'Average Load']
                avg_load = avg_load
                avg_load['year'] = avg_load.index
                
                c_map = res['forecast'].consumption['consumption_qualifier']
                annotation = c_map[c_map == 'M'].index.max() + 1
                avg_load['annotation'] = np.nan 
                avg_load['annotation'][annotation] = 'start of forecast'
                
                
                avg_load['Average Load'] = \
                    avg_load["consumption"]/hours_per_year
            
                avg_load_table = self.make_plot_table(
                    avg_load[['year', 'annotation', 'Average Load']],
                     names = names,
                    community = com,
                    fname = com+"_avg_load.csv")
            
                charts.append({'name':'avg_load',
                        'data': str(avg_load_table).replace('nan','null'), 
                        'title':'Average Load',
                        'type': "'kW'",'plot': True,})
            else:
                charts.append({'name':'avg_load', 
                    'data': 
                        "No Consumption available to calculate average load", 
                    'title':'Average Load',
                    'type': "'kW'",})
            
            ## ENdAverage load chart
            
            ## Line loss and efficiency plots
            #~ try:
            yes = res['community data'].get_item('community','utility info')
                #~ print yes.columns
            #~ except IOError: 
                #~ yes = None
            #~ print yes
            if not yes is None:
                yes_years = yes.index
            
            #~ if not yes is None:
                #~ start = min(yes_years)
            #~ else:
            start = res['community data'].get_item('community',
                    'current year')
            try:
                end = res['forecast'].consumption.index[-1]
            except AttributeError:
                end = self.max_year
            years = range(int(start),int(end))
            
            line_loss = DataFrame(years, columns = ['year'], index = years)
            line_loss['line losses'] = \
                res['community data'].get_item('community','line losses') /\
                100.0
            line_loss['diesel generation efficiency'] = \
                res['community data'].get_item('community',
                'diesel generation efficiency')
            #~ print line_loss
            measured_values = yes[['line loss', 'efficiency']]
            measured_values['year'] = measured_values.index
            measured_values = \
                measured_values[['year','line loss', 'efficiency']]
            measured_values.columns = \
                ['year','line losses','diesel generation efficiency']
            line_loss = concat([measured_values,line_loss])

    
            
            try:
                line_loss['annotation'] = np.nan 
                line_loss['annotation'][max(yes_years.index) + 1] = \
                    'start of forecast'
            except:
                line_loss['annotation'] = np.nan 
                line_loss['annotation'][start] = 'start of forecast'
    
            line_loss = line_loss.replace([np.inf, -np.inf], np.nan)
            line_loss_table = self.make_plot_table(
                line_loss[['year', 'annotation', "line losses"]],
                sigfig = 2,  
                community = com,
                fname = com+"_line_loss.csv")
            charts.append({'name':'line_loss',
                    'data': str(line_loss_table).\
                        replace('nan','null').replace('None','null'), 
                    'title':'line losses',
                    'type': "'percent'",'plot': True,})
    
            gen_eff_table = self.make_plot_table(
                line_loss[['year', 'annotation', 
                    'diesel generation efficiency']],
                sigfig = 2,
                community = com,
                fname = com+"_generation_efficiency.csv")
            charts.append({'name':'generation_efficiency',
                    'data': str(gen_eff_table).replace('nan','null'), 
                    'title':'Diesel Generation Efficiency',
                    'type': "'gal/kWh'",'plot': True,})
                    
                    
            eff = res['community data'].get_item('community',
                'diesel generation efficiency')
            #~ ph_data = res['community data'].get_item('Diesel Efficiency',
                #~ 'data')
            #~ try:
            num_gens = res['community data'].get_item('community',
                'number diesel generators')
            #~ except ValueError:
                #~ num_gens = ph_data['Total Number of generators']
            
            total_cap = \
                res['community data'].get_item('community','total capacity')
            if np.isnan(float(total_cap)):
                total_cap = 'N/a'
            try:
                cap = '{:,.0f} kW'.format(float(total_cap))
                c2 = float(total_cap)
            except ValueError:
                c2 = 0
                cap = total_cap
            
            
                
            try:
                largest = '{:,.0f} kW'.format(\
                    float(res['community data'].\
                    get_item('community','largest generator')))
            except ValueError:
                largest = \
                    res['community data'].\
                    get_item('community','largest generator')
            
            size = res['community data'].\
                get_item('community', 'diesel generator sizing')
            
            try:
                ratio = float(c2)/ \
                            float(avg_load['Average Load']\
                            [avg_load['annotation'] == 'start of forecast']) 
            except (ValueError, UnboundLocalError):
                ratio = 0
                             
            hr_data = res['community data'].get_section('Heat Recovery')
            hr_opp = res['community data'].get_item('community',
                'heat recovery operational')
            hr_opp = 'Yes' if hr_opp else 'No'
            #~ hr_opp = "TBD"
            hr_ava = \
                hr_data['est. current annual heating fuel gallons displaced']
            #~ hr_ava = 0
            if type(hr_ava) is str or np.isnan(hr_ava):
                hr_ava = 0
                
            wind = res['community data'].get_section('Wind Power')
                                                      
            w_cap = float(res['community data'].get_item('community',
                'wind capacity'))
            
            w_fac = float(wind['capacity factor'])
            
            solar = res['community data'].get_section('Solar Power')
                                                      
            s_cap = float(res['community data'].get_item('community',
                'solar capacity'))
            s_pv = solar['output per 10kW solar PV']
            
            h_cap = float(res['community data'].get_item('community',
                'hydro capacity'))
                                            
            try:
                w_gen = float(res['community data'].get_item('community',
                    'utility info')['generation wind'].iloc[-1:])
                s_gen = float(res['community data'].get_item('community',
                    'utility info')['generation solar'].iloc[-1:])
                h_gen = float(res['community data'].get_item('community',
                    'utility info')['generation hydro'].iloc[-1:])
                
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
                [False, "Total capacity", cap], 
                [False, "Largest generator", largest],
                [False, "Sizing", size],
                [False, "Ratio of total capacity to average load", 
                                                        '{:,.2f}'.format(ratio)],
                [True, "Heat Recovery", ""],
                [False, "Operational",  hr_opp],
                [False, 
                    "Estimated number of gallons of heating oil displaced", 
                                            '{:,.0f} gallons'.format(hr_ava)],
                [True, "Wind Power", ""],
                [False, "Current wind capacity", '{:,.0f} kW'.format(w_cap)],
                [False, "Current wind generation", w_gen],
                [False, "Current wind capacity factor", '{:,.2f}'.format(w_fac)],
                [True, "Solar Power", ""],
                [False, "Current solar capacity",  '{:,.0f} kW'.format(s_cap)],
                [False, "Current solar generation",  s_gen],
                [False, "Current output per 10kW Solar PV",
                    '{:,.0f}'.format(s_pv)],
                [True, "Hydropower", ""],
                [False, "Current hydro capacity",  '{:,.0f} kW'.format(h_cap)],
                [False, "Current hydro generation",  h_gen],
                
                ]
    
                
            charts.insert(0,{'name':'gen_summary', 'data':table, 
                    'title':'Generation Overview',
                    'table': True,})
        else:
            parent = res['community data'].get_item('community','intertie')[0]
            url = '../' + parent.lower()  + "_intertie/generation.html"
                #~ print url
            charts.append({'name':'generation', 'data': 
                                [{'url': url, 
                                    'text': "See " +\
                                     parent + \
                                     " intertie for generation plot for" + \
                                     " all communities on the intertie."}
                                    ],
                                'title':'generation',
                                'links_list': True,})
        
        ## Intertie list
        intertie = res['community data'].get_item('community','intertie')
        if intertie != 'not in intertie':
            
            if intertie != []:
                table = [
                    [True, "Community", "Parent/Child"],
                    [False, intertie[0], 'Parent']
                    ]
                
                
                for c in intertie[1:]:
                    if c == "''":
                        break
                    table.append([False,c,'Child'])
            
                charts.insert(0,{'name':'it_l', 'data':table, 
                    'title':'Intertied Communities',
                    'table': True,})
        
        ## End Intertie list
        
        ## save to page
        msg = None
        if com in self.bad_data_coms:
            msg = self.bad_data_msg

        pth = os.path.join(self.directory, com.replace("'",""),
            'Generation'.replace(' ','_').replace('(','').\
            replace(')','').lower() + '.html')
        with open(pth, 'w') as html:
            html.write(
                template.render( 
                    type = 'Generation', 
                    com = com.replace("'",'') ,
                    charts = charts,
                    summary_pages = ['Summary'] + comp_order ,
                    sections = self.get_summary_pages(),
                    communities = self.get_cleanded_coms(),
                    metadata = self.metadata,
                    message = msg
                )
            )
        
    def create_community_projects_summary (self, com):
        """Generate potential_projects.html for the community
        
        Parameters
        ----------
        com: str
            community in question
        
        """
        template = self.potential_projects_html
        res = self.results[com]
       
        cats = {}
        
        for i in [i for i in sorted(self.results.keys()) if i.find(com) != -1 ]:
            if com != i.split('+')[0]:
                continue
            #~ print cats
            #~ print i
            if com.find('_intertie') == -1 and i.find('_intertie') != -1:
                continue
            #~ if com != i:
                #~ continue
            comps = self.results[i]
            if i.find('hydro') != -1:
                comps = ['Hydropower']
            elif i.find('wind') != -1:
                comps = ['Wind Power']
            elif i.find('heat_recovery') != -1:
                comps =['Heat Recovery']
            
            it = self.results[com]['community data'].intertie    
            
            for comp in comps:  
                #~ print i
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
                
                fs = "N/A"
                lcoe_e = "N/A"
                lcoe_hf = "N/A"
                if (not type(ratio) is str):
                    fs = c.get_fuel_total_saved() 
                    if type(fs) in [list, np.array, np.ndarray]:
                        fs = fs[0]
                        
                    if type(c.levelized_cost_of_energy) is dict:
                        lcoe_e = c.levelized_cost_of_energy['kWh'] #* mmbtu_to_kWh
                        ## lcoe_hf units are already in gal/year
                        lcoe_hf = c.levelized_cost_of_energy['MMBtu'] #* mmbtu_to_gal_HF 
                    
                    elif comp in ["Wind Power",'Solar Power','Hydropower',
                                  'Transmission and Interties',
                                  'Diesel Efficiency']:
                        #~ if comp == 'Diesel Efficiency':
                            #~ print c.levelized_cost_of_energy
                        lcoe_e = c.levelized_cost_of_energy
                    else:
                        lcoe_hf = c.levelized_cost_of_energy
                
                
                
                net = c.get_NPV_net_benefit()
                #~ if net == 'N/A': 
                    #~ net = 0
                
                benefit = c.get_NPV_benefits()
                #~ if benefit == 'N/A': 
                    #~ benefit = 0
                    
                costs = c.get_NPV_costs()
                #~ if costs == 'N/A': 
                    #~ costs = 0
                
                #~ if 'N/A' == ratio:
                    #~ ratio = 0
  
                
                try:
                    name = c.comp_specs['project details']['name']
                except (KeyError, TypeError):
                    name = comp
                if name == 'None':
                    name = comp
                
                name = name.decode('unicode_escape').encode('ascii','ignore')
                
                #~ print name
                try:
                    success = True if ratio > 1.0 and ratio != 'N/A' else False
                except TypeError:
                    success = True if ratio > 1.0 else False
                cats[comp].append({'name': name,
                              'sucess': success,
                              'negitive': True if ratio < 0 else False,
                              'comp':comp,
                              'benefits': '${:,.0f}'.format(benefit) if benefit != 'N/A' else benefit,
                              'costs': '${:,.0f}'.format(costs) if costs != 'N/A' else costs,
                              'net': '${:,.0f}'.format(net) if net != 'N/A' else net,
                              'ratio': '{:,.1f}'.format(ratio) if ratio != 'N/A' else ratio,
                              'lcoe_e':'${:,.2f}'.format(lcoe_e) if lcoe_e != 'N/A' else lcoe_e,
                        'lcoe_hf':'${:,.2f}'.format(lcoe_hf/mmbtu_to_gal_HF) if lcoe_hf != 'N/A' else lcoe_hf,
                              'fuel_saved': '{:,.0f}'.format(fs) if fs != 'N/A' else fs})
         
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
                #~ print comp
                #~ print cats[comp]
                projs += cats[comp]
            except KeyError:
                pass
        
        #~ p_set = set([])
        #~ p_temp = []
        #~ for p in projs:
            #~ if p['name'] in p_set:
                #~ continue
            #~ p_set = p_set.union([p['name']])
            #~ p_temp.append(p)
        #~ projs = p_temp
        #~ print projs
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
                                    message = msg,
                                    bc_limit = 1.0
                                    ))
                                    

    #### -----------------------------------------------------------------------
    #### Helper and utility functions
    #### -----------------------------------------------------------------------
    def copy_static (self):
        """copy all of the css and js stuff
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
        shutil.copy(os.path.join(pth,'templates','tech_map.js'),self.directory)
        shutil.copy(os.path.join(pth,'templates',
            'leaflet.ajax.min.js'),self.directory)
        template = self.env.get_template('navbar.js')
        
        
        
        #~ print self.get_house_dists()
        techs = []

        for comp in sorted(self.viable_communities.keys()):
            temp = []
            for com in sorted(self.viable_communities[comp]):
                try:
                    temp.append(com.replace("'",''))
                except:
                    temp = [com.replace("'",'')]
            
            techs.append({'communities':temp,
                          'clean': comp.replace('(','').\
                                        replace(')','').replace(' ','_'),
                          'district': comp})

        
        with open(os.path.join(self.directory,'navbar.js'), 'w') as html:
            html.write(template.render(communities = self.get_cleanded_coms(),
                                       regions=self.get_regions(),
                                       senate_dist=self.get_senate_dists(),
                                       house_dist=self.get_house_dists(),
                                       techs = techs
                        ))
                        
    def make_plot_table (self, xs, ys = None, names = None, sigfig=0,
                         community = None, fname = None):
        """make a table for a plot
        
        Parameters
        ----------
        xs: list
        ys: list
        name: list
        sigfig: int
        community: str
        fname: str
        
        Returns
        -------    
        plotting_table, List of lists,
            a table that can be used to make a google chart plot
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
                header.append(
                    "{label: '" +name[0].upper() + name[1:].lower()+ \
                    "', type: 'number'}"
                )
        
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
            xs[cols].round(sigfig).to_csv(
                os.path.join(
                    self.directory, community.replace("'",""),'csv', fname),
                index=False)
        plotting_table.insert(0,header)
        #~ print plotting_table
        return plotting_table 
        
    def make_table (self, xs, ys = None, names = None, sigfig=0,
                    community = None, fname = None):
        """make a table for a google charts table
        
        Parameters
        ----------
        xs: list
        ys: list
        name: list
        sigfig: int
        community: str
        fname: str
        
        Returns
        -------    
        plotting_table, List of lists,
            a table that can be used to make a google chart table
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
    
    def multiprocess_community_summaries (self, com, lock, log = True):
        """Multi-processing helper
        
        Parameters
        ----------
        com: str
            a community
        lock: Lock
            a lock for multiprocessing
        log: bool
            log the data
        """
        start = datetime.now()
        self.generate_community_summaries(com)
        if log:
            lock.acquire()
            print com, datetime.now() - start
            lock.release()

    def get_tech_summary(self, component):
        """get the tech summaries
        
        Parameters
        ----------
        component: str
            name of a component
            
        Returns
        -------
        tech summary info
        """
        try:
            return self.tech_summaries[component]
        except AttributeError as e:
            #~ print e
            self.tech_summaries = {}
        except KeyError as e:
            #~ print e
            pass

        ## get regional summaries from main component
        self.tech_summaries[component] = \
            import_module("aaem.components." + component).\
            create_regional_summary(self.results)
        return self.tech_summaries[component]
        
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
            import_module("aaem_summaries.components." + component).summary
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
    
    def get_senate_dists (self):
        try:
            return self.senate
        except AttributeError:
            pass
            
        temp = {}
        for com in self.get_coms():
            reg = self.results[com]['community data']\
                                            .get_item('community', 
                                                        'senate district')
            for d in reg:
                try:
                    temp[d.replace("'",'')].append(com.replace("'",''))
                except:
                    temp[d.replace("'",'')] = [com.replace("'",'')]
            
        senate = []
        for k in sorted(temp.keys()):
            senate.append({"district":k, "communities":temp[k], 
                            "clean": k.replace(' ','_').replace('(','').\
                                replace(')','').replace('/','_').lower()})
        
        
        self.senate = senate
        return self.senate
        
    def get_house_dists (self):
        try:
            return self.house
        except AttributeError:
            pass
            
        temp = {}
        for com in self.get_coms():
            reg = self.results[com]['community data']\
                                            .get_item('community', 
                                                        'house district')
            for d in reg:
                try:
                    temp[d].append(com.replace("'",''))
                except:
                    temp[d] = [com.replace("'",'')]
            
        house = []
        for k in sorted(temp.keys()):
            house.append({"district":str(k), "communities":temp[k], 
                            "clean": str(k)})
        
        
        self.house = house
        return self.house
    
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
        
    def get_ratios_greater_than_limit (self, limit = 1.0):
        """ Function doc """
        #~ keys = sorted([k for k in self.results.keys() if k.find('+') == -1])
        for com in self.results.keys():
            for comp in self.results[com]:
                try:
                    
                    
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
                    
                    ratio =  self.results[com][comp].get_BC_ratio()
                    if ratio == 'N/A':
                        continue
                    if ratio > limit:
                        #~ print ratio, type(ratio)
                        #~ self.viable_communities[comp].add(com.split('+')[0])
                        self.viable_communities[comp].add(com.split('+')[0].replace("_intertie",""))
                except AttributeError as e:
                    #~ print e
                    pass
                
        #~ print self.viable_communities
        


