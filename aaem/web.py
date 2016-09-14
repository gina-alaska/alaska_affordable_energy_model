from jinja2 import Environment, PackageLoader
import aaem.driver as driver
from pandas import concat, DataFrame
import os



class WebSummary(object):
    """ Class doc """
    
    def __init__ (self, model_root, directory):
        """ Class initialiser """
        self.model_root = model_root
        model = driver.Driver(self.model_root)
        self.results = model.load_results()
        
        self.directory = directory
        try:
            os.makedirs(os.path.join(self.directory,'csv'))
        except OSError:
            pass
            
        self.env = Environment(loader=PackageLoader('aaem','templates/'))

    def get_viable_components (self, com, cutoff = 1):
        """ Function doc """
        l = []
        for comp in self.results[com]:
            try:
                if self.results[com][comp].get_BC_ratio() >= cutoff:
                    l.append(comp)
            except AttributeError:
                pass
        return l
        
    def generate_component_summaries (self, com):
        """
        """
        comps = self.get_viable_components(com)
        
    def generate_wind_summary (self, community = 'Shishmaref'):
        """
        """
        template = self.env.get_template('wind.html')
        
        
        comp_no_project = self.results[community]['wind power']
        start_year = comp_no_project.start_year
        end_year = comp_no_project.actual_end_year
        
        projects = {}
        for i in [i for i in sorted(self.results.keys()) \
             if i.find(community) != -1 and i.find('wind') != -1]:
                 
            start_year = min(start_year, 
                            self.results[i]['wind power'].start_year)
            end_year = max(end_year,self.results[i]['wind power'].actual_end_year)
            projects[i] = self.results[i]['wind power']
            
        print start_year,end_year
                 

        fc = comp_no_project.forecast
        generation = fc.generation_by_type['generation_diesel [kWh/year]'].\
                                            ix[start_year:end_year]
        diesel_price = self.results[community]['community data'].get_item('community','diesel prices').get_projected_prices(start_year,end_year+1)
                                            
        eff = comp_no_project.cd['diesel generation efficiency']
        base_cost = generation/eff * diesel_price
        base_cost.name = 'Base Cost'
        costs_table = DataFrame(base_cost)
        
        
        
        #~ diesel_price = comp_no_project.diesel_prices[:comp_no_project.actual_project_life]

        net_benefit = DataFrame([range(comp_no_project.start_year,comp_no_project.actual_end_year+1),comp_no_project.get_net_beneft()[:comp_no_project.actual_project_life].tolist()],['Year', 'savings']).T.set_index('Year')
        net_benefit.index = net_benefit.index.astype(int)
        
        costs_table['Estimated Proposed Generation'] = costs_table['Base Cost'] - net_benefit['savings']
        costs_table['year'] = costs_table.index
        
        names = []
        for p in projects:
            project = projects[p]
            name = project.comp_specs['project details']['name']
            if name == 'nan':
                name = p.replace('+', ' ').replace('_',' ')
            net_benefit = DataFrame([range(project.start_year,project.actual_end_year+1),project.get_net_beneft()[:project.actual_project_life].tolist()],['Year', 'savings']).T.set_index('Year')
            net_benefit.index = net_benefit.index.astype(int)
            costs_table[name] = costs_table['Base Cost'] - net_benefit['savings']
            names.append(name)
        
        #~ print costs_table
        #~ costs_table = costs_table.fillna('null')
        #~ print comp_no_project.start_year, net_benefit

        costs_table = costs_table[['year','Base Cost','Estimated Proposed Generation'] + names]
        costs_table.columns = ['year','Base Case Cost', 'Cost With Wind'] + names
        costs_table.to_csv(os.path.join(self.directory,'csv', community + "_" + "Wind_Power" + "_" + 'costs.csv'), index=False)
        #~ prop_cost = base_cost - net_benefit
        #~ prop_cost.name = 'Estimated Proposed Generation'
        #~ print prop_cost
        #~ costs_table = concat([base_cost,prop_cost],axis = 1)
        #~ 
        #~ print costs_table
        
        
            
        
        table1 = costs_table.\
                        round().values.tolist()
        #~ print table1
        table1.insert(0,['year','Base Case Cost', 'Modeled Wind'] + names)
        
        
        
        base_con = generation/eff 
        base_con.name = 'Base Consumption'
        
        cons_table = DataFrame(base_con)
        #~ print cons_table
        cons_table['year'] = cons_table.index
        
        reduction = DataFrame([range(comp_no_project.start_year,comp_no_project.actual_end_year+1)],['Year']).T
        reduction['savings'] = comp_no_project.electric_diesel_reduction
        reduction = reduction.set_index('Year')
        reduction.index = reduction.index.astype(int)
        #~ print reduction
        
        cons_table['Est. Diesel Consumed'] =  cons_table['Base Consumption'] - reduction['savings']
        
        
        names = []
        for p in projects:
            project = projects[p]
            name = project.comp_specs['project details']['name']
            if name == 'nan':
                name = p.replace('+', ' ').replace('_',' ')
            reduction = DataFrame([range(project.start_year,project.actual_end_year+1)],['Year']).T
            reduction['savings'] = project.electric_diesel_reduction
            reduction = reduction.set_index('Year')
            reduction.index = reduction.index.astype(int)
            cons_table[name] =  cons_table['Base Consumption'] - reduction['savings']
            names.append(name)
        
        
        cons_table = cons_table[['year','Base Consumption', 'Est. Diesel Consumed'] + names]
        
        cons_table.columns = ['year','Base Case Diesel Consumed','Wind Diesel Consumed']+names
        cons_table.to_csv(os.path.join(self.directory,'csv', community + "_" + "Wind_Power" + "_" + 'consumption.csv'), index=False)
        
        table2  = cons_table.\
                        round().values.tolist()
        table2.insert(0,['year',
                         'Base Case Diesel Consumed',
                         'Modeled Wind']+names)
        
        info = [{'words':'Investments Needed', 
                    'value': '${:,.0f}'.format(comp_no_project.get_NPV_costs())},
                {'words':'Net Lifetime Savings', 
                    'value': '${:,.0f}'.format(comp_no_project.get_NPV_benefits())},
                {'words':'Expected kWh/year', 
                    'value': '{:,.0f}'.format(comp_no_project.load_offset_proposed*8760)},
                {'words':'Proposed Capacity(kW)', 
                    'value': '{:,.0f}'.format(comp_no_project.load_offset_proposed)},
                {'words':'Assumed Wind Class', 
                    'value': int(float(comp_no_project.comp_specs['resource data']\
                                                    ['Assumed Wind Class']))},
                {'words':'Assumed Capacity Factor', 
                    'value': comp_no_project.comp_specs['resource data']\
                                                 ['assumed capacity factor']},
                {'words':'Existing Wind', 
                    'value': comp_no_project.comp_specs['resource data']['existing wind'],
                    'units': 'kW'},
                {'words':'Existing Solar',
                    'value': comp_no_project.comp_specs['resource data']['existing solar'], 
                    'units' :'kW'},
                ]
                
        info_for_projects = [{'name':'Modeled Wind Project','info':info}]
        
        for p in projects:
            project = projects[p]
            name = project.comp_specs['project details']['name']
            info = [{'words':'Investments Needed', 
                    'value': '${:,.0f}'.format(project.get_NPV_costs())},
                {'words':'Net Lifetime Savings', 
                    'value': '${:,.0f}'.format(project.get_NPV_benefits())},
                {'words':'Expected kWh/year', 
                    'value': '{:,.0f}'.format(project.load_offset_proposed*8760)},
                {'words':'Proposed Capacity(kW)', 
                    'value': '{:,.0f}'.format(project.load_offset_proposed)},
                {'words':'Assumed Wind Class', 
                    'value': int(float(project.comp_specs['resource data']\
                                                    ['Assumed Wind Class']))},
                {'words':'Assumed Capacity Factor', 
                    'value': project.comp_specs['resource data']\
                                                 ['assumed capacity factor']},
                {'words':'Existing Wind', 
                    'value': project.comp_specs['resource data']['existing wind'],
                    'units': 'kW'},
                {'words':'Existing Solar',
                    'value': project.comp_specs['resource data']['existing solar'], 
                    'units' :'kW'},
                ]
                
            info_for_projects.append({'name':name,'info':info})
                
        
        charts = [{'name':'costs', 'data': str(table1).replace('nan','null'), 
                    'title': 'Estimated Electricity Generation Fuel Costs per Year',
                    'type': "'$'"},
                  {'name':'consumption', 'data': str(table2).replace('nan','null'), 
                    'title':'Diesel Consumed for Generation Electricity per Year',
                    'type': "'other'"}]
            
        pth = os.path.join(self.directory, community +'_wind_summary.html')
        with open(pth, 'w') as html:
            html.write(template.render( info = info_for_projects,
                                        type = "Wind Power", 
                                        com = community ,
                                        charts = charts ))

