"""
Residential Efficiency outputs
------------------------------

output functions for Residential Efficiency component

"""
import os.path
import numpy as np
from pandas import DataFrame
from config import COMPONENT_NAME
import aaem.constants as constants
from aaem.components import comp_order, definitions


## component summary
def component_summary (results, res_dir):
    """Creates the regional and communities summary for the component in provided
    directory

    Parameters
    ----------
    results : dictionay
        results from the model, dictionary with each community or project
        as key
    res_dir :  path
        location to save file

    """
    communities_summary (results, res_dir)
    save_regional_summary(create_regional_summary (results), res_dir)

def communities_summary (coms, res_dir):
    """Saves the summary by: community residential_building_summary.csv

    Parameters
    ----------
    coms : dictionay
        results from the model, dictionary with each community or project
        as key
    res_dir :  path
        location to save file


    """
    out = []
    for c in sorted(coms.keys()):
        if c.find('+') != -1 or c.find("_intertie") != -1:
            continue
        try:
            res = coms[c][COMPONENT_NAME]

            name = c
            if name == 'Barrow':
                name = 'Utqiagvik (Barrow)'
            out.append([name,
                res.get_NPV_benefits(),res.get_NPV_costs(),
                res.get_NPV_net_benefit(),res.irr,res.get_BC_ratio(),
                res.hoil_price[0], res.init_HH, res.opportunity_HH,
                res.break_even_cost, res.levelized_cost_of_energy,
                res.baseline_fuel_Hoil_consumption[0]/constants.mmbtu_to_gal_HF,
                (res.baseline_fuel_Hoil_consumption[0] - \
                    res.proposed_fuel_Hoil_consumption[0])/\
                        constants.mmbtu_to_gal_HF,
                round(float(res.fuel_oil_percent)*100,2),
                res.baseline_HF_consumption[0],
                res.baseline_HF_consumption[0] - \
                        res.proposed_HF_consumption[0],
                ])
        except (KeyError,AttributeError) as e :
            #~ print e
            pass

    cols = ['Community',
           'Residential Efficiency NPV Benefit',
           'Residential Efficiency NPV Cost',
           'Residential Efficiency NPV Net Benefit',
           'Residential Internal Rate of Return',
           'Residential Efficiency B/C Ratio',
           'Heating Oil Price - year 1',
           'Occupied Houses',
           'Houses to Retrofit',
           'Breakeven Heating Fuel Price [$/gal heating oil equiv.]',
           'Levelized Cost of Energy [$/MMBtu]',
           'Residential Heating Oil Consumed (MMBtu) - year 1',
           'Residential Efficiency Heating Oil Saved (MMBtu/year)',
           'Residential Heating Oil as percent of Total Heating Fuels',
           'Total Residentital Heating Fuels (MMBtu) - year 1',
           'Residential Efficiency Total Heating Fuels Saved (MMBtu/year)',
            ]
    data = DataFrame(out,columns = cols).set_index('Community').round(2)
    f_name = os.path.join(res_dir,
                COMPONENT_NAME.lower().replace(' ','_') + '_summary.csv')
    fd = open(f_name,'w')
    fd.write(("# residental building component summary by community\n"
           '# community: '+ definitions.COMMUNITY + '\n'
           '# Residential Efficiency NPV Benefit: ' + definitions.NPV_BENEFITS + '\n'
           '# Residential Efficiency NPV Cost: ' + definitions.NPV_COSTS + '\n'
           '# Residential Efficiency NPV Net Benefit: ' + definitions.NPV_NET_BENEFITS + '\n'
           '# Residential Internal Rate of Return: ' + definitions.IRR +'\n'
           '# Residential Efficiency B/C Ratio: ' + definitions.NPV_BC_RATIO + '\n'
           '# Heating Oil Price - year 1: ' + definitions.PRICE_HF + '\n'
           '# Occupied Houses: Occupied homes in communities.\n'
           '# Houses to Retrofit: Houses that are to be retrofit.\n'
           '# Breakeven Heating Fuel Price [$/gal heating oil equiv.]: ' + definitions.BREAK_EVEN_COST_HF + '\n'
           '# Levelized Cost of Energy [$/MMBtu]: ' + definitions.LCOE + '\n'
           '# Residential Heating Oil Consumed (MMBtu) - year 1: Heating oil consumed by current systems.\n'
           '# Residential Efficiency Heating Oil Saved (MMBtu/year): Heating oil saved by retrofit systems.\n'
           '# Residential Heating Oil as percent of Total Heating Fuels: Percentage of heating fuels that is heating oil.\n'
           '# Total Residentital Heating Fuels (MMBtu) - year 1: Heating fuel consumed by current systems.\n'
           '# Residential Efficiency Total Heating Fuels Saved (MMBtu/year): Heating fuel consumed by current systems.\n'
        ))
    fd.close()
    data.to_csv(f_name, mode='a')

def create_regional_summary (results):
    """Creates the regional summary

    Parameters
    ----------
    results : dictionary
        results from the model, dictionary with each community or project
        as key

    Returns
    -------
    DataFrame
        containg regional results

    """
    #~ print "start"
    regions = {}
    for c in results:
        c_region = results[c]['community data'].get_item('community','region')
        comp = results[c][COMPONENT_NAME]
        #~ print comp
        bc_ratio = comp.get_BC_ratio()
        bc_ratio = (not type(bc_ratio) is str) and (not np.isinf(bc_ratio))\
                                              and (bc_ratio > 1)
        #~ print bc_ratio ,comp.get_BC_ratio()
        #~ return
        capex = round(comp.get_NPV_costs(),0)  if bc_ratio else 0
        net_benefit = round(comp.get_NPV_net_benefit(),0)  if bc_ratio else 0

        displaced_fuel = \
            round((comp.baseline_fuel_Hoil_consumption[0] - \
                    comp.proposed_fuel_Hoil_consumption[0])/\
                        constants.mmbtu_to_gal_HF, 0) if bc_ratio else 0

        if (c.find('+') != -1 or c.find("_intertie") != -1):
            #~ print c
            continue
        if c_region in regions.keys():
            ## append entry
            regions[c_region]['Number of communities/interties in region'] +=1
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] += 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] += capex
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] += net_benefit
            k = 'Heating oil displaced yearly (gallons)'
            regions[c_region][k] += displaced_fuel

        else:
            ## set up "first" entry
            regions[c_region] = {'Number of communities/interties in region':1}
            k = 'Number of communities with cost effective projects'
            regions[c_region][k] = 1 if bc_ratio else 0
            k = 'Investment needed for cost-effective projects ($)'
            regions[c_region][k] = capex
            k = 'Net benefit of cost-effective projects ($)'
            regions[c_region][k] = net_benefit
            k = 'Heating oil displaced yearly (gallons)'
            regions[c_region][k] = displaced_fuel

    cols = ['Number of communities/interties in region',
            'Number of communities with cost effective projects',
            'Investment needed for cost-effective projects ($)',
            'Net benefit of cost-effective projects ($)',
            'Heating oil displaced yearly (gallons)']

    try:
        summary = DataFrame(regions).T[cols]
    except KeyError:
        summary = DataFrame(columns = cols)

    summary.ix['All Regions'] = summary.sum()
    #~ print summary
    return summary

def save_regional_summary (summary, res_dir):
    """Saves the summary by region

    Parameters
    ----------
    summary : Dataframe
        compiled regional results
    res_dir :  path
        location to save file

    """
    f_name = os.path.join(res_dir, '__regional_' +
                COMPONENT_NAME.lower().replace(' ','_').\
                    replace('(','').replace(')','') + '_summary.csv')
    summary.to_csv(f_name, mode='w', index_label='region')
