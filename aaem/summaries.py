"""
summaries.py
ross spicer

functions for the creation of log and summary files form model results 
"""
from pandas import DataFrame, read_csv, concat
import os
import numpy as np
from importlib import import_module

from constants import mmbtu_to_kWh, mmbtu_to_gal_HF
from constants import mmbtu_to_gal_LP, mmbtu_to_Mcf, mmbtu_to_cords
from aaem.components import comp_lib
from copy import deepcopy

def building_log(coms, res_dir):
    """
    creates a log for the non-residental component buildings outputs by community
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communities outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
    
    post:
        a csv file "non-residential_summary.csv"log is saved in res_dir   
    
    """
    out = []
    #~ print 'NRB LOG'
    for c in sorted(coms.keys()):
        if c.find('+') != -1 or c.find("_intertie") != -1:
            continue
        try:
            com = coms[c]['Non-residential Energy Efficiency']
            
            #~ print  coms[c]['community data'].get_section('Non-residential Energy Efficiency')
            types = coms[c]['community data'].get_item('Non-residential Energy Efficiency',
                                                "consumption estimates").index
            estimates = deepcopy(com.comp_specs["building inventory"]).fillna(0)
            
            estimates = estimates.set_index('Building Type')
            estimates = estimates.astype(float)

            
            #~ print estimates
            
            num  = 0
            try:
                
                if 'Average' in set(estimates.ix['Average'].index):
                    num = len(estimates.ix['Average'])
                else:
                    num = 1
                
            except KeyError:
                pass
            estimates = estimates.groupby(estimates.index).sum()
            try:
                estimates.ix["Unknown"] =  estimates.ix["Average"] 
                estimates = estimates[estimates.index != "Average"]
            except KeyError:
                pass
            count = []
            act = []
            est = []
            elec = []
            hf = []
            
            #~ print types
            for t in types:
                if t in ['Water & Sewer',]:
                    continue
                try:
                    n = 0
                    sf_m = np.nan
                    sf_e = np.nan
                    elec_used = np.nan
                    hf_used = np.nan
                    if t == 'Average':
                        
                        n = num
                        sf_e = estimates['Square Feet']['Unknown']
                        hf_used = \
                            estimates['Fuel Oil']['Unknown']/mmbtu_to_gal_HF + \
                            estimates['Natural Gas']['Unknown']/mmbtu_to_Mcf + \
                            estimates['Propane']['Unknown']/mmbtu_to_gal_LP + \
                            estimates['HW District']['Unknown']/mmbtu_to_cords
                        elec_used = estimates['Electric']['Unknown']/mmbtu_to_kWh
                    else:
                        n = com.buildings_df['count'][t]
                        sf_e = estimates['Square Feet'][t]
                        hf_used = \
                            estimates['Fuel Oil'][t]/mmbtu_to_gal_HF + \
                            estimates['Natural Gas'][t]/mmbtu_to_Mcf + \
                            estimates['Propane'][t]/mmbtu_to_gal_LP + \
                            estimates['HW District'][t]/mmbtu_to_gal_HF +\
                            estimates['Biomass'][t]/mmbtu_to_cords
                        #~ print hf_used
                        elec_used = estimates['Electric'][t]/mmbtu_to_kWh
                    
                    
                    sf_m = com.buildings_df['Square Feet'][t]
                    
                    
                except KeyError as e:
                    #~ print e
                    pass
                count.append(n)
                act.append(sf_m)
                est.append(sf_e)
                elec.append(elec_used)
                hf.append(hf_used)
                
            percent = com.buildings_df['Square Feet'].sum() /\
                      estimates['Square Feet'].sum()
            percent2 = float(com.buildings_df['count'].sum())/\
                      (com.buildings_df['count'].sum()+num)
            
            if np.isnan(percent):
                percent = 0.0
                
            if np.isnan(percent2):
                percent2 = 0.0
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            out.append([name,percent*100,percent2*100]+ count+act+est+elec+hf)
            
        except (KeyError,AttributeError, ZeroDivisionError)as e :
            #~ print c +":"+ str(e)
            pass
    #~ print out
    try:
        l = [n for n in types if n not in  ['Water & Sewer',]]
    except UnboundLocalError:
        return
    c = []
    e = []
    m = []
    ec = []
    hf = []
    for i in range(len(l)):
        if l[i] == 'Average':
            l[i] = 'Unknown'
        c.append('number buildings')
        m.append('square feet(measured)')
        e.append('square feet(including estimates)')
        ec.append("electricity used (mmbtu)")
        hf.append("heating fuel used (mmbtu)")

    
    data = DataFrame(out,columns = ['community',
                                '% sqft measured',
                                '% buildings from inventory'] + l + l + l + l + l
                    ).set_index('community').round(2)
    f_name = os.path.join(res_dir,'non-residential_building_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# non residental building component building "
             "summary by community\n"))
    fd.write(",%,%," + str(c)[1:-1].replace(" '",'').replace("'",'') + "," + \
             str(m)[1:-1].replace("' ",'').replace("'",'') + "," + \
             str(e)[1:-1].replace("' ",'').replace("'",'') + "," +\
             str(ec)[1:-1].replace("' ",'').replace("'",'') + "," +\
             str(hf)[1:-1].replace("' ",'').replace("'",'') +'\n')
    fd.close()
    data.to_csv(f_name, mode='a')
    
    
def village_log (coms, res_dir): 
    """
        creates a log comparing the consumption and costs of the residential,
    non-residential, and water/wastewater components
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communities outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
    
    post:
        a csv file "village_sector_consumption_summary.csv"log is saved 
    in res_dir   
    
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find('+') != -1 or c.find("_intertie") != -1:
            continue
        try:
            start_year = coms[c]['community data'].get_item('community', 
                                                        'current year')
            #~ print coms[c]['forecast'].consumption.ix[start_year]['consumption']
            consumption = \
                int(coms[c]['forecast']\
                .consumption.ix[start_year]['consumption'])
            population = int(coms[c]['forecast'].population.ix[start_year])
            try:
                res = coms[c]['Residential Energy Efficiency']
                res_con = [res.baseline_HF_consumption[0], 
                                res.baseline_kWh_consumption[0] / mmbtu_to_kWh]
                res_cost = [res.baseline_HF_cost[0], res.baseline_kWh_cost[0]]
            except KeyError:
                res_con = [np.nan, np.nan]
                res_cost = [np.nan, np.nan]
            try:
                com = coms[c]['Non-residential Energy Efficiency']
                com_con = [com.baseline_HF_consumption,
                            com.baseline_kWh_consumption / mmbtu_to_kWh]
                com_cost = [com.baseline_HF_cost[0],com.baseline_kWh_cost[0]]
            except KeyError:
                com_con = [np.nan, np.nan]
                com_cost = [np.nan, np.nan]
            try:
                ww = coms[c]['Water and Wastewater Efficiency']
                ww_con = [ww.baseline_HF_consumption[0],
                          ww.baseline_kWh_consumption[0] / mmbtu_to_kWh ]
                ww_cost = [ww.baseline_HF_cost[0],ww.baseline_kWh_cost[0]]
            except KeyError:
                ww_con = [np.nan, np.nan]
                ww_cost = [np.nan, np.nan]
                
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            t = [name, consumption, population, 
                 coms[c]['community data'].get_item('community','region')] +\
                 res_con + com_con + ww_con + res_cost + com_cost + ww_cost 
            out.append(t)
        except AttributeError:
            pass
    start_year = 2017
    data = DataFrame(out,columns = ['community', 'consumption year 1 (kWh)',
                    'Population', 'Region',
                    'Residential Heat (MMBTU)', 
                    'Residential Electricity (MMBTU)',
                    'Non-Residential Heat (MMBTU)', 
                    'Non-Residential Electricity (MMBTU)',
                    'Water/Wastewater Heat (MMBTU)', 
                    'Water/Wastewater Electricity (MMBTU)',
                    'Residential Heat (cost ' + str(start_year)+')', 
                    'Residential Electricity (cost ' + str(start_year)+')',
                    'Non-Residential Heat (cost ' + str(start_year)+')',
                    'Non-Residential Electricity (cost ' + str(start_year)+')',
                    'Water/Wastewater Heat (cost ' + str(start_year)+')', 
                    'Water/Wastewater Electricity (cost ' + str(start_year)+')',
                    ]
                    ).set_index('community')
    f_name = os.path.join(res_dir,'village_sector_consumption_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write("# summary of consumption and cost\n")
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
def fuel_oil_log (coms, res_dir):
    """
    create a 
    
    """
    out = []
    for c in sorted(coms.keys()):
        if c+"_intertie" in coms.keys():
            continue
        try:
            it = coms[c]['community data'].intertie
            if it is None:
                it = 'parent'
                
            if c.find("_intertie") == -1:
                res = coms[c]['Residential Energy Efficiency']
                com = coms[c]['Non-residential Energy Efficiency']
                wat = coms[c]['Water and Wastewater Efficiency']
            else:
                k = c.replace("_intertie","")
                res = coms[k]['Residential Energy Efficiency']
                com = coms[k]['Non-residential Energy Efficiency']
                wat = coms[k]['Water and Wastewater Efficiency']
            
            eff = coms[c]['community data'].get_item("community",
                                            "diesel generation efficiency")
            if eff == 0:
                eff = np.nan
            
            year = res.start_year

            try:
                elec = float(coms[c]['forecast'].generation[\
                                "generation diesel"][year]) / eff
            except KeyError:
                elec = 0
            if it == 'child' or np.isnan(elec):
                elec = 0

            res = res.baseline_fuel_Hoil_consumption[0]
            com = com.baseline_fuel_Hoil_consumption 
            wat = wat.baseline_fuel_Hoil_consumption [0] 
            
            total = res + com + wat + elec
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            out.append([name,elec,res,com,wat,total])
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    data = DataFrame(out,columns = ['community','Utility diesel (gallons)',
                                    'Residential Heating oil (gallons)',
                                    'Non-residential Heating Oil (gallons)',
                                    'Water/wastewater heating oil (gallons)',
                                    'Total (gallons)']
                    ).set_index('community').round(2)
    f_name = os.path.join(res_dir,'fuel_oil_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write("# fuel_oil summary by community\n")
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
def forecast_comparison_log (coms, res_dir):
    """
        creates a table of results for each community comparing the forecast 
    consumption results and the component consumtption results
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communities outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
        
    post:
        a csv file "forecast_comparsion_summary.csv"log is saved in res_dir
    """
    out = []
    for c in sorted(coms.keys()):
        
        try:
            it = coms[c]['community data'].intertie
            if it is None:
                it = 'parent'
            if it == 'child':
                continue
            try:
                it_list = coms[c]['community data'].intertie_list
                it_list = [c] + list(set(it_list).difference(["''"]))
            except AttributeError:
                it_list = [c]
            #~ print it_list
            res = coms[c]['Residential Energy Efficiency']
            com = coms[c]['Non-residential Energy Efficiency']
            wat = coms[c]['Water and Wastewater Efficiency']
            fc = coms[c]['forecast']
            
            first_year = max([res.start_year,
                              com.start_year,
                              wat.start_year,
                              fc.consumption.index[0]])
                              
            res_kwh = 0
            com_kwh = 0
            wat_kwh = 0
            
            for ic in it_list:
                try:
                    ires = coms[ic]['Residential Energy Efficiency']
                    icom = coms[ic]['Non-residential Energy Efficiency']
                    iwat = coms[ic]['Water and Wastewater Efficiency']
                except KeyError:
                    continue
                res_kwh +=  ires.baseline_kWh_consumption[first_year - ires.start_year]
                com_kwh +=  icom.baseline_kWh_consumption
                wat_kwh +=  iwat.baseline_kWh_consumption[first_year - iwat.start_year]
            
            
            comp_res = float(res_kwh)
            comp_wat = float(wat_kwh)
            comp_com = float(com_kwh)
            
            comp_non_res = float(com_kwh + wat_kwh)
            comp_total = float(com_kwh + wat_kwh + res_kwh)
            
            #~ print fc.consumption_to_save.ix[first_year]
            #~ print ""
            fc_res = float(fc.consumption.ix[first_year]\
                                ['consumption residential'])
            fc_non_res = float(fc.consumption.ix[first_year]\
                            ['consumption non-residential'])
            if np.isnan(fc_non_res):
                fc_non_res = 0
            
            fc_total = float(fc.consumption.ix[first_year]\
                                    ['consumption'])
            
            if np.isnan(fc_total):
                fc_total = 0
            
            res_diff = fc_res - comp_res
            non_res_diff = fc_non_res - comp_non_res
            total_diff = fc_total - comp_total
            
            res_per = (abs(res_diff)/ (fc_res + comp_res))*100.0
            non_res_per = (abs(non_res_diff)/ (fc_non_res + comp_non_res))*100.0
            total_per = (abs(total_diff)/ (fc_total + comp_total))*100.0
            
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            
            out.append([name,fc_res,comp_res,res_diff,res_per,
                          fc_non_res,comp_com,comp_wat,comp_non_res,
                          non_res_diff,non_res_per,
                          fc_total,comp_total,total_diff,total_per])
            
        except (KeyError,AttributeError) as e:
            #~ print e
            pass
    data = DataFrame(out,columns = \
       ['community',
        'Forecast (trend line) Residential Consumption [kWh]',
        'Forecast (modeled) Residential Consumption [kWh]',
        'Difference Residential Consumption [kWh]',
        'Percent Difference Residential Consumption [%]',
        'Forecast (trend line) Non-Residential Consumption [kWh]',
        'Forecast (modeled) Non-Residential (non-residential) Consumption [kWh]',
       'Forecast (modeled) Non-Residential (water/wastewater) Consumption [kWh]',
        'Forecast (modeled) Non-Residential Consumption [kWh]',
        'Difference Non-Residential Consumption [kWh]',
        'Percent Difference Non-Residential Consumption [%]',
        'Forecast (trend line) Total Consumption [kWh]',
        'Forecast (modeled) Total Consumption [kWh]',
        'Difference Total Consumption [kWh]',
        'Percent Difference Total Consumption [%]']
                    ).set_index('community').round(2)
    f_name = os.path.join(res_dir,
                'forecast_component_consumption_comparison_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# comparison of forecast kWh consumption vs."
             #~ " component kWh consumption summary by community\n"))
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
def electric_price_summary (coms, res_dir):    
    """
    """
    out = None
    for c in sorted(coms.keys()):
        #~ print c
        #~ print dir(coms[c]['community data'])
        try:
            if c.find('+') != -1:
                continue
            it = coms[c]['community data'].intertie
            if it is None:
                it = 'parent'
            if it == 'child':
                continue
            base_cost = float(coms[c]['community data'].get_item("community",
                                            "electric non-fuel price"))
            prices = deepcopy(coms[c]['community data'].get_item("community",
                                            "electric non-fuel prices"))
            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            prices[name] = prices[prices.columns[0]]#'price']
            #~ del prices[prices.columns[0]]
            prices = prices.T
            prices["base cost"] = base_cost
            if out is None:
                out = prices
            else:
                out = concat([out,prices])
            
            #~ print out
        except (KeyError, TypeError) as e:
            #~ print e
            continue
    if out is None:
        return
        
    f_name = os.path.join(res_dir,
                'electric_prices_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write(("# list of the electricty prices forecasted\n"))
    #~ fd.close()
    out.index = [i.replace('_',' ') for i in out.index]
    out = out.drop_duplicates()
    
    out[[out.columns[-1]] + out.columns[:-1].tolist()].to_csv(f_name, mode='w')

def genterate_npv_summary (coms, res_dir):
    """
    generate a log of the npv results
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communities outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
        
    post:
        summary may be saved
    """
    for community in coms:
        #~ print community
        components = coms[community]
        npvs = []
        for comp in components:
            try:
                npvs.append([comp, 
                         components[comp].get_NPV_benefits(),
                         components[comp].get_NPV_costs(),
                         components[comp].get_NPV_net_benefit(),
                         components[comp].get_BC_ratio()
                        ])
            except AttributeError:
                pass

        name = community
        if name == 'Barrow':
            name = 'Utqiagvik (Barrow)'

        f_name = os.path.join(res_dir,community.replace(' ','_'),
                                community.replace(' ','_') + '_npv_summary.csv')
        cols = ['Component', 
                community +': NPV Benefits',
                community +': NPV Cost', 
                community +': NPV Net Benefit',
                community +': Benefit Cost Ratio']
        npvs = DataFrame(npvs,
                         columns = cols).set_index('Component')
        npvs.to_csv(f_name)
        
def community_forcast_summaries (community,  components, forecast, res_dir):
    """generate community forecast summary
    """
    forecast = deepcopy(forecast)
    componetns = deepcopy(components)
    #~ components = coms[community]
    if community.find('+') != -1:
        return
    #~ print community
    
    #### electricity
    data = forecast.population
    data['community'] = community
    #~ print list(data.columns)[::-1]
    data = data[['community', 'population']]
    data['population_qualifier'] = 'I'
    
    try:
        forecast.consumption.columns
    except AttributeError:
        return
    data[forecast.consumption.columns] =\
        forecast.consumption
        
    data['generation'] = forecast.generation['generation']
        
    
    data.columns = ['community',
        'population',
        'population_qualifier',
        'residential_electricity_consumed [kWh/year]',
        'electricity_consumed/generation_qualifier',
        'non-residential_electricity_consumed [kWh/year]',
        'total_electricity_consumption [kWh/year]',
        'total_electricity_generation [kWh/year]']
    data = data[['community',
        'population',
        'population_qualifier',
        'total_electricity_consumption [kWh/year]',
        'residential_electricity_consumed [kWh/year]',
        'non-residential_electricity_consumed [kWh/year]',
        'total_electricity_generation [kWh/year]',
        'electricity_consumed/generation_qualifier']]

    f_name = os.path.join(res_dir,
        community.replace(' ','_') + '_electricity_forecast.csv')
    
    with open(f_name, 'w') as s:
        s.write((
             '# Electricity Forecast for ' + community + '\n'							
             '# Qualifier info: \n'					
             '#   M indicates a measured value\n'							
             '#   P indicates a projected value\n'
             '#   I indicates a value carried over from the input data.'
             ' May be projected or measured see input data metadata.\n'
        ))
                                     
    data.to_csv(f_name, mode = 'a')
    
    #### generation ####
    
    data = forecast.generation
    data['community'] = community
    data['population'] = forecast.population['population']
    data['population_qualifier'] = 'I'
    data['generation_qualifier'] = \
        forecast.\
        consumption['consumption_qualifier']
    
    data = data[list(data.columns[-4:]) + list(data.columns[:-4])]
    #~ print data
    data.columns = [
        'community',
        'population', 
        'population_qualifer',
        'generation_qualifer',
        'generation total (kWh/year)',
        'generation diesel (kWh/year)',
        'generation hydro (kWh/year)',
        'generation natural gas (kWh/year)',
        'generation wind (kWh/year)',
        'generation solar (kWh/year)',
        'generation biomass (kWh/year)'
    ]
    f_name = os.path.join(res_dir,
        community.replace(' ','_') + '_generation_forecast.csv')
    with open(f_name, 'w') as s:
        s.write((
             '# generation Forecast for ' + community + '\n'							
             '# Qualifier info: \n'					
             '#   M indicates a measured value\n'							
             '#   P indicates a projected value\n'
             '#   I indicates a value carried over from the input data.'
             ' May be projected or measured see input data metadata.\n'
        ))
                                     
    data.to_csv(f_name, mode = 'a')
    
   
    
    ires = components['Residential Energy Efficiency']
    icom = components['Non-residential Energy Efficiency']
    iwat = components['Water and Wastewater Efficiency']
    
    #### heat demand ####
    data =  DataFrame(forecast.population['population'])
    data['population_qualifier'] = 'I'
    data['community'] = community
    data = data[['community', 'population', 'population_qualifier']]
    #~ data['heat_energy_demand_residential [mmbtu/year]'] = \

    df = DataFrame(ires.baseline_HF_consumption,
        columns =['col'],
         index = range(ires.start_year, ires.end_year+1))
    data['heat_energy_demand_residential [mmbtu/year]'] = df['col']
    
    try:
        df = DataFrame(icom.baseline_HF_consumption,
            columns =['col'],
            index = range(icom.start_year, icom.end_year+1))
    except AttributeError:
        return
    data['heat_energy_demand_non-residential [mmbtu/year]'] = df['col']
    df = DataFrame(iwat.baseline_HF_consumption,
        columns =['col'],
         index = range(iwat.start_year, iwat.end_year+1))
    data['heat_energy_demand_water-wastewater [mmbtu/year]'] = df['col']
        
        
    hd_cols = [
        'heat_energy_demand_residential [mmbtu/year]',
        'heat_energy_demand_non-residential [mmbtu/year]',
        'heat_energy_demand_water-wastewater [mmbtu/year]'
    ]
        
    for col in hd_cols:
        yr = data[~data[col].isnull()].index[-1]
        data[col][data.index > yr] = data[col].ix[yr]
    data['heat_energy_demand_total [mmbtu/year]'] = data[hd_cols].sum(1)
    f_name = os.path.join(res_dir,
        community.replace(' ','_') + '_heat_demand_forecast.csv')
    with open(f_name, 'w') as s:
        s.write((
             '# heat demand Forecast for ' + community + '\n'							
             '# Qualifier info: \n'					
             '#   M indicates a measured value\n'							
             '#   P indicates a projected value\n'
             '#   I indicates a value carried over from the input data.'
             ' May be projected or measured see input data metadata.\n'
        ))
    data.to_csv(f_name, mode = 'a')
    
    #### heating fuel ####
    data =  DataFrame(forecast.population['population'])
    data['population_qualifier'] = 'I'
    data['community'] = community
    data = data[['community', 'population', 'population_qualifier']]

    
    df = DataFrame(ires.baseline_fuel_Hoil_consumption,
        columns =['col'],
         index = range(ires.start_year, ires.end_year+1))
    data['heating_fuel_residential_consumed [gallons/year]'] = \
        df['col'].round()
    df = DataFrame(
        ires.baseline_fuel_Hoil_consumption/mmbtu_to_gal_HF,
        columns =['col'],
        index = range(ires.start_year, ires.end_year+1)
    )
    data['heating_fuel_residential_consumed [mmbtu/year]'] = \
        df['col'].round()
   
    df = DataFrame(ires.baseline_fuel_wood_consumption,
        columns =['col'],
         index = range(ires.start_year, ires.end_year+1))
    data['cords_wood_residential_consumed [cords/year]'] = df['col'].round()
    df = DataFrame(
        ires.baseline_fuel_wood_consumption/mmbtu_to_cords,
        columns =['col'],
         index = range(ires.start_year, ires.end_year+1)
    )
    data['cords_wood_residential_consumed [mmbtu/year]'] = df['col'].round()
    
    df = DataFrame(ires.baseline_fuel_gas_consumption,
        columns =['col'],
         index = range(ires.start_year, ires.end_year+1))
    data['gas_residential_consumed [Mcf/year]'] = df['col'].round()
    df = DataFrame(
        ires.baseline_fuel_gas_consumption/mmbtu_to_gal_LP,
        columns =['col'],
         index = range(ires.start_year, ires.end_year+1)
    )
    data['gas_residential_consumed [mmbtu/year]'] = df['col'].round()
    
    df = DataFrame(ires.baseline_fuel_kWh_consumption,
        columns =['col'],
         index = range(ires.start_year, ires.end_year+1))
    data['electric_residential_consumed [kWh/year]'] = df['col'].round()
    df = DataFrame(
        ires.baseline_fuel_kWh_consumption/mmbtu_to_kWh,
        columns =['col'],
         index = range(ires.start_year, ires.end_year+1)
    )
    data['electric_residential_consumed [mmbtu/year]'] = df['col'].round()
    
    df = DataFrame(ires.baseline_fuel_LP_consumption,
        columns =['col'],
         index = range(ires.start_year, ires.end_year+1))
    data['propane_residential_consumed [gallons/year]'] = df['col'].round()
    df = DataFrame(
        ires.baseline_fuel_LP_consumption/mmbtu_to_Mcf,
        columns =['col'],
         index = range(ires.start_year, ires.end_year+1)
    )
    data['propane_residential_consumed [mmbtu/year]'] = df['col'].round()
    
    df = DataFrame(
        icom.baseline_HF_consumption * mmbtu_to_gal_HF,
        columns =['col'],
         index = range(icom.start_year, icom.end_year+1))
    data['heating_fuel_non-residential_consumed [gallons/year]'] = \
        df['col'].round()
    df = DataFrame(
        icom.baseline_HF_consumption,
        columns =['col'],
         index = range(icom.start_year, icom.end_year+1)
    )
    data['heating_fuel_non-residential_consumed [mmbtu/year]'] = \
        df['col'].round()
   
    df = DataFrame(
        iwat.baseline_HF_consumption * mmbtu_to_gal_HF,
        columns =['col'],
         index = range(iwat.start_year, iwat.end_year+1))
    data['heating_fuel_water-wastewater_consumed [gallons/year]'] = \
        df['col'].round()
    df = DataFrame(
        iwat.baseline_HF_consumption,
        columns =['col'],
         index = range(iwat.start_year, iwat.end_year+1)
    )
    data['heating_fuel_water-wastewater_consumed [mmbtu/year]'] = \
        df['col'].round()
    
    
    hf_cols = [
        'heating_fuel_residential_consumed [gallons/year]',
        'heating_fuel_residential_consumed [mmbtu/year]',
        'cords_wood_residential_consumed [cords/year]',
        'cords_wood_residential_consumed [mmbtu/year]',
        'gas_residential_consumed [Mcf/year]',
        'gas_residential_consumed [mmbtu/year]',
        'electric_residential_consumed [kWh/year]',	
        'electric_residential_consumed [mmbtu/year]',
        'propane_residential_consumed [gallons/year]',
        'propane_residential_consumed [mmbtu/year]',
        'heating_fuel_non-residential_consumed [gallons/year]',
        'heating_fuel_non-residential_consumed [mmbtu/year]',
        'heating_fuel_water-wastewater_consumed [gallons/year]',
        'heating_fuel_water-wastewater_consumed [mmbtu/year]',
    ]
    for col in hf_cols:
        yr = data[~data[col].isnull()].index[-1]
        data[col][data.index > yr] = data[col].ix[yr]
    
    data['heating_fuel_total_consumed [gallons/year]'] = \
        data[[
            'heating_fuel_residential_consumed [gallons/year]',
            'heating_fuel_non-residential_consumed [gallons/year]',
            'heating_fuel_water-wastewater_consumed [gallons/year]',
        ]].sum(1)
    data['heating_fuel_total_consumed [mmbtu/year]'] = \
        data[[
            'heating_fuel_residential_consumed [mmbtu/year]',
            'heating_fuel_non-residential_consumed [mmbtu/year]',
            'heating_fuel_water-wastewater_consumed [mmbtu/year]',
        ]].sum(1)
        
    f_name = os.path.join(res_dir,
        community.replace(' ','_') + '_heating_fuel_forecast.csv')
    with open(f_name, 'w') as s:
        s.write((
             '# heating fuel Forecast for ' + community + '\n'							
             '# Qualifier info: \n'					
             '#   M indicates a measured value\n'							
             '#   P indicates a projected value\n'
             '#   I indicates a value carried over from the input data.'
             ' May be projected or measured see input data metadata.\n'
        ))
    data.to_csv(f_name, mode = 'a')
     

        
        
def consumption_summary (coms, res_dir):
    """ Function doc """
    consumption = []
    for community in coms:
        if 1 != len(community.split('+')):
            continue
        it = coms[community]['community data'].intertie
        region = \
            coms[community]['community data'].get_item('community','region')
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        fc = coms[community]['forecast']
        try:
            
            name = community
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            con = fc.consumption.ix[2010:2040].values.T[0].tolist()
            consumption.append([name, region] + con)
        except AttributeError as e:
            #~ print community, e
            continue

    f_name = os.path.join(res_dir,'kwh_consumption_summary.csv')
    cols = ['Community', 'region'] + [str(y) for y in range(2010,2041)]
    summary = DataFrame(consumption,
                     columns = cols).set_index('Community').fillna('N/a')
    summary.to_csv(f_name)

def call_comp_summaries (coms, res_dir):
    """ 
        calls summary fils that may exist in each component 
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communities outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
        
    post:
        summaries may be saved
    """
    genterate_npv_summary(coms, res_dir)
    consumption_summary(coms, res_dir)
    
    for comp in comp_lib:
        try:
            log = import_module("aaem.components." +comp_lib[comp]).\
                                                        component_summary
            log(coms, res_dir)
        except AttributeError as e:
            #~ print e
            continue
            

    
           
    
