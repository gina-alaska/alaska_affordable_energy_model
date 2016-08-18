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

def res_log (coms, res_dir):
    """
    creates a log for the residental component outputs by community
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communites outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
    
    post:
        a csv file "residential_summary.csv" log is saved in res_dir   
    
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find('+') != -1 or c.find("_intertie") != -1:
            continue
        try:
            res = coms[c]['model'].comps_used['residential buildings']
            out.append([c,
                res.get_NPV_benefits(),res.get_NPV_costs(),
                res.get_NPV_net_benefit(),res.get_BC_ratio(),
                res.hoil_price[0], res.init_HH, res.opportunity_HH,
                res.break_even_cost, res.levelized_cost_of_energy,
                res.baseline_fuel_Hoil_consumption[0]/mmbtu_to_gal_HF,
                res.baseline_fuel_Hoil_consumption[0]/mmbtu_to_gal_HF - \
                        res.refit_fuel_Hoil_consumption[0]/mmbtu_to_gal_HF,
                round(float(res.fuel_oil_percent)*100,2),
                res.baseline_HF_consumption[0],
                res.baseline_HF_consumption[0] - \
                        res.refit_HF_consumption[0],
                ])
        except (KeyError,AttributeError) :
            pass
            
    cols = ['community',
           'Residential Efficiency NPV Benefit',
           'Residential Efficiency NPV Cost', 
           'Residential Efficiency NPV Net Benefit',
           'Residential Efficiency B/C Ratio',
           'Heating Oil Price - year 1',
           'Occupied Houses', 
           'Houses to Retrofit', 
           'Break Even Heating Fuel Price [$/gal]',
           'Levelized Cost of Energy [$/MMBtu]',
           'Residential Heating Oil Consumed(mmbtu) - year 1',
           'Residential Efficiency Heating Oil Saved(mmbtu/year)',
           'Residential Heating Oil as percent of Total Heating Fuels',
           'Total Residentital Heating Fuels (mmbtu) - year 1',
           'Residential Efficiency Total Heating Fuels Saved (mmbtu/year)',
            ]
    data = DataFrame(out,columns = cols).set_index('community').round(2)
    f_name = os.path.join(res_dir,'residential_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write("# residental building component summary by community\n")
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
def com_log (coms, res_dir): 
    """
    creates a log for the non-residental component outputs by community
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communites outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
    
    post:
        a csv file "non-residential_summary.csv"log is saved in res_dir   
    
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find('+') != -1:# or c.find("_intertie") != -1:
            continue
        try:
            com = coms[c]['model'].comps_used['non-residential buildings']
            savings = com.baseline_fuel_Hoil_consumption -\
                      com.refit_fuel_Hoil_consumption
            out.append([c,
                com.get_NPV_benefits(),com.get_NPV_costs(),
                com.get_NPV_net_benefit(),com.get_BC_ratio(),
                com.hoil_price[0], com.elec_price[0], 
                com.num_buildings , com.refit_sqft_total,
                com.break_even_cost,
                com.levelized_cost_of_energy['MMBtu'],
                com.levelized_cost_of_energy['kWh'],
                com.baseline_fuel_Hoil_consumption,
                com.baseline_kWh_consumption,
                savings,
                com.baseline_kWh_consumption - com.refit_kWh_consumption])
        except (KeyError,AttributeError) as e:
            #~ print c +":"+ str(e)
            pass
            
            
    cols = ['community',
            'Nonresidential Efficiency NPV Benefit',
            'Nonresidential Efficiency NPV Cost',
            'Nonresidential Efficiency NPV Net Benefit',
            'Nonresidential Efficiency B/C Ratio',
            'Heating Oil Price - year 1',
            '$ per kWh - year 1',
            'Number Nonresidential Buildings',
            'Nonresidential Total Square Footage',
            'Break Even Heating Fuel Price [$/gal]',
            'Levelized Cost of Energy [$/MMBtu]',
            'Levelized Cost of Energy [$/kWh]',
            'Nonresidential Heating Oil Consumed(gal) - year 1',
            'Nonresidential Electricity Consumed(kWh) - year 1',
            'Nonresidential Efficiency Heating Oil Saved[gal/year]',
            'Nonresidential Efficiency Electricity Saved[kWh/year]']
            
    data = DataFrame(out,columns = cols).set_index('community').round(2)
    f_name = os.path.join(res_dir,'non-residential_summary.csv')
    #~ fd = open(f_name,'w')
    #~ fd.write("# non residental building component summary by community\n")
    #~ fd.close()
    data.to_csv(f_name, mode='w')
    
def building_log(coms, res_dir):
    """
    creates a log for the non-residental component buildings outputs by community
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communites outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
    
    post:
        a csv file "non-residential_summary.csv"log is saved in res_dir   
    
    """
    out = []
    for c in sorted(coms.keys()):
        if c.find('+') != -1 or c.find("_intertie") != -1:
            continue
        try:
            com = coms[c]['model'].comps_used['non-residential buildings']
            
            
            types = coms[c]['model'].cd.get_item('non-residential buildings',
                                                "com building estimates").index
            estimates =coms[c]['model'].cd.get_item('non-residential buildings',
                                                "com building data").fillna(0)
            
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
            
            
            out.append([c,percent*100,percent2*100]+ count+act+est+elec+hf)
            
        except (KeyError,AttributeError)as e :
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
    #~ fd.write(("# non residental building component building "
             #~ "summary by community\n"))
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
                        'output dir':<a path to the given communites outputs>
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
            start_year = coms[c]['model'].cd.get_item('community', 
                                                        'current year')
            consumption = int(coms[c]['model'].fc.consumption.ix[start_year])
            population = int(coms[c]['model'].fc.population.ix[start_year])
            try:
                res = coms[c]['model'].comps_used['residential buildings']
                res_con = [res.baseline_HF_consumption[0], 
                                res.baseline_kWh_consumption[0] / mmbtu_to_kWh]
                res_cost = [res.baseline_HF_cost[0], res.baseline_kWh_cost[0]]
            except KeyError:
                res_con = [np.nan, np.nan]
                res_cost = [np.nan, np.nan]
            try:
                com = coms[c]['model'].comps_used['non-residential buildings']
                com_con = [com.baseline_HF_consumption,
                            com.baseline_kWh_consumption / mmbtu_to_kWh]
                com_cost = [com.baseline_HF_cost[0],com.baseline_kWh_cost[0]]
            except KeyError:
                com_con = [np.nan, np.nan]
                com_cost = [np.nan, np.nan]
            try:
                ww = coms[c]['model'].comps_used['water wastewater']
                ww_con = [ww.baseline_HF_consumption[0],
                          ww.baseline_kWh_consumption[0] / mmbtu_to_kWh ]
                ww_cost = [ww.baseline_HF_cost[0],ww.baseline_kWh_cost[0]]
            except KeyError:
                ww_con = [np.nan, np.nan]
                ww_cost = [np.nan, np.nan]
            t = [c, consumption, population, 
                 coms[c]['model'].cd.get_item('community','region')] +\
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
            it = coms[c]['model'].cd.intertie
            if it is None:
                it = 'parent'
                
            if c.find("_intertie") == -1:
                res = coms[c]['model'].comps_used['residential buildings']
                com = coms[c]['model'].comps_used['non-residential buildings']
                wat = coms[c]['model'].comps_used['water wastewater']
            else:
                k = c.replace("_intertie","")
                res = coms[k]['model'].comps_used['residential buildings']
                com = coms[k]['model'].comps_used['non-residential buildings']
                wat = coms[k]['model'].comps_used['water wastewater']
            
            eff = coms[c]['model'].cd.get_item("community",
                                            "diesel generation efficiency")
            if eff == 0:
                eff = np.nan
            
            year = res.start_year
            try:
                try:
                    elec = float(coms[c]['model'].fc.generation_by_type[\
                                "generation diesel"][year]) / eff
                except KeyError:
                    elec = float(coms[c]['model'].fc.generation_by_type[\
                                "generation_diesel [kWh/year]"][year]) / eff
            except KeyError:
                elec = 0
            if it == 'child' or np.isnan(elec):
                elec = 0

            res = res.baseline_fuel_Hoil_consumption[0]
            com = com.baseline_fuel_Hoil_consumption 
            wat = wat.baseline_fuel_Hoil_consumption [0] 
            
            total = res + com + wat + elec
            
            out.append([c,elec,res,com,wat,total])
            
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
                        'output dir':<a path to the given communites outputs>
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
            it = coms[c]['model'].cd.intertie
            if it is None:
                it = 'parent'
            if it == 'child':
                continue
            try:
                it_list = coms[c]['model'].cd.intertie_list
                it_list = [c] + list(set(it_list).difference(["''"]))
            except AttributeError:
                it_list = [c]
            #~ print it_list
            res = coms[c]['model'].comps_used['residential buildings']
            com = coms[c]['model'].comps_used['non-residential buildings']
            wat = coms[c]['model'].comps_used['water wastewater']
            fc = coms[c]['model'].fc
            
            first_year = max([res.start_year,
                              com.start_year,
                              wat.start_year,
                              fc.start_year])
                              
            res_kwh = 0
            com_kwh = 0
            wat_kwh = 0
            
            for ic in it_list:
                try:
                    ires = coms[ic]['model'].comps_used['residential buildings']
                    icom = coms[ic]['model'].\
                        comps_used['non-residential buildings']
                    iwat = coms[ic]['model'].comps_used['water wastewater']
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
            fc_res = float(fc.consumption_to_save.ix[first_year]\
                                ['residential_electricity_consumed [kWh/year]'])
            fc_non_res = float(fc.consumption_to_save.ix[first_year]\
                            ['non-residential_electricity_consumed [kWh/year]'])
            if np.isnan(fc_non_res):
                fc_non_res = 0
            
            fc_total = float(fc.consumption_to_save.ix[first_year]\
                                    ['total_electricity_consumed [kWh/year]'])
            
            if np.isnan(fc_total):
                fc_total = 0
            
            res_diff = fc_res - comp_res
            non_res_diff = fc_non_res - comp_non_res
            total_diff = fc_total - comp_total
            
            res_per = (abs(res_diff)/ (fc_res + comp_res))*100.0
            non_res_per = (abs(non_res_diff)/ (fc_non_res + comp_non_res))*100.0
            total_per = (abs(total_diff)/ (fc_total + comp_total))*100.0
            
            out.append([c,fc_res,comp_res,res_diff,res_per,
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
        try:
            it = coms[c]['model'].cd.intertie
            if it is None:
                it = 'parent'
            if it == 'child':
                continue
            base_cost = float(coms[c]['model'].cd.get_item("community",
                                            "elec non-fuel cost"))
            prices = deepcopy(coms[c]['model'].cd.get_item("community",
                                            "electric non-fuel prices"))
            #~ print prices
            prices[c] = prices['price']
            del prices['price']
            prices = prices.T
            prices["base cost"] = base_cost
            if out is None:
                out = prices
            else:
                out = concat([out,prices])
            
            
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
    out[[out.columns[-1]] + out.columns[:-1].tolist()].to_csv(f_name, mode='w')

def genterate_npv_summary (coms, res_dir):
    """
    generate a log of the npv results
    
    pre:
        coms: the run model outputs: a dictionary 
                    {<"community_name">:
                        {'model':<a run driver object>,
                        'output dir':<a path to the given communites outputs>
                        },
                     ... repeated for each community
                    }
        res_dir: directory to save the log in
        
    post:
        summary may be saved
    """
    for community in coms:
        #~ print community
        components = coms[community]['model'].comps_used
        npvs = []
        for comp in components:
            npvs.append([comp, 
                         components[comp].get_NPV_benefits(),
                         components[comp].get_NPV_costs(),
                         components[comp].get_NPV_net_benefit(),
                         components[comp].get_BC_ratio()
                        ])
        f_name = os.path.join(res_dir,community,community + '_npv_summary.csv')
        cols = ['Component', 
                community +': NPV Benefits',
                community +': NPV Cost', 
                community +': NPV Net Benefit',
                community +': Benefit Cost Ratio']
        npvs = DataFrame(npvs,
                         columns = cols).set_index('Component')
        npvs.to_csv(f_name)
        
def consumption_summary (coms, res_dir):
    """ Function doc """
    consumption = []
    for community in coms:
        if 1 != len(community.split('+')):
            continue
        it = coms[community]['model'].cd.intertie
        region = coms[community]['model'].cd.get_item('community','region')
        if it is None:
            it = 'parent'
        if it == 'child':
            continue
        fc = coms[community]['model'].fc
        try:
            con = fc.consumption.ix[2010:2040].values.T[0].tolist()
            consumption.append([community, region] + con)
        except AttributeError as e:
            #~ print community, e
            continue

    f_name = os.path.join(res_dir,'kWh_consumption_summary.csv')
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
                        'output dir':<a path to the given communites outputs>
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
        except AttributeError:
            continue
            

    
           
    
