"""
preprocessor.py
ross spicer

process data into a format for the model to use 
"""
from pandas import DataFrame,read_csv, concat
import shutil
import os.path
from diagnostics import diagnostics
import numpy as np

class Preprocessor (object):
    def __init__ (self):
        self.diagnostics = diagnostics()
    
    def population (self, in_file, out_dir, com_id, threshold = 20):
        """
        create the population input file
        
        pre:
            in_file is the most current population file in the data-repo
            out dir is a path, com_id is a string ex "Adak"
        post: 
            a file is saved, and the data frame it was generated from is returned
        """
        
        
        pop_data = read_csv(in_file, index_col = 1) # update to GNIS
        pops = pop_data.ix[com_id]["2003":"2014"].values
        years = pop_data.ix[com_id]["2003":"2014"].keys().values.astype(int)
        
        if (pops < threshold).any():
            self.diagnostics.add_warning("preprocessor","population < 20")
        
        
        out_file = os.path.join(out_dir,"population.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " population\n")
        fd.write("# recorded population in a given year\n")
        fd.write("#### #### #### #### ####\n")
        fd.close()
        
        
        df = DataFrame([years,pops],["year","population"]).T.set_index("year")
        df.to_csv(out_dir+"population.csv",mode="a")
        return df
        
    def pce_electricity (self, in_file, com_id):
        """
        parse PCE electricity data 
        
        pre:
            in_file is the most current PCE file in the data-repo
        com_id is a string ex "Adak"
        
        post: 
           a data frame is returned
        """
        df = read_csv(in_file, index_col = 1) # update to GNIS
        data = df.ix[com_id][["year","residential_kwh_sold",
                                         "commercial_kwh_sold",
                                         "community_kwh_sold",
                                         "government_kwh_sold",
                                         "unbilled_kwh","notes"]]
                                         
        self.diagnostics.add_note("preprocessor", 
                "notes from pce data: " + str(data["notes"].tail(1)[0]))
        
        sums = []
        for year in set(data["year"].values):
            if len(data[data["year"] == year]) != 12:
                continue
            temp = data[data["year"] == year].sum()
            temp["year"] = int(year)
            sums.append(temp)
        df = DataFrame(sums).set_index("year")
        for key in df.keys():
            df[key.split('_')[0]] = df[key]
            del(df[key])
        return df
        
    def eia_electricity (self, in_file, com_id):
        """
        parse EIA electricity data 
        
        pre:
            in_file is the most current PCE file in the data-repo
        com_id is a string ex "Sitka"
        
        post: 
           a data frame is returned
        """
        df = read_csv(in_file, index_col = 0, comment='#')
        data = df.ix[com_id][['Data Year','Sum - Residential Megawatthours',
                'Sum - Commercial Megawatthours',
                'Sum - Industrial Megawatthours']].values.astype(int)*1000
        
        df = DataFrame(data,
                     columns=["year","residential",
                              "commercial","industrial"])
        df['year'] /= 1000
        df = df.set_index("year")
        return df
        
    def electricity (self, in_file, out_dir, com_id):
        """
        create the electricity input file
        
        pre:
            in_file is the most current PCE file in the data-repo
            out dir is a path, com_id is a string ex "Adak"
        post: 
            a file is saved, and the data frame it was generated from is returned
        """
        try:
            data = self.pce_electricity (in_file, com_id)
            data["industrial"] = data["residential"]/0-data["residential"]/0
        except KeyError:
            data = self.eia_electricity (in_file, com_id)
            nans = data["residential"]/0-data["residential"]/0
            data["community"] = nans
            data["government"] = nans
            data["unbilled"] = nans
        
            
        res = data['residential']
        non_res = data.sum(1) - res
        data = DataFrame({"year":res.keys(),
                   "residential":res.values,
                   "non-residential":non_res.values,
                   "total":res.values+non_res.values}).set_index("year")

            
            
        out_file = os.path.join(out_dir,"electricity.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " electricity consumption\n")
        fd.write("# all units are in kWh/year for a given year and category\n")
        fd.write("#### #### #### #### ####\n")
        fd.close()    
        
        data.to_csv(out_file, mode="a")
        return data
    
    def wastewater (self, data_file, assumptions_file, out_dir, com_id):
        """
        preprocess wastewater data
        
        pre:
            data_file & assumptions_file are the most current wastewater and 
        assumption files from the AAEM data repo. out dir is a path, com_id is
        a string ex "Adak"
        post:
            a file is saved in out_dir
        exceptions:
            raises a key error if the community is not in the waste water data
        or if the system type is unknown
        """
        
        out_file = os.path.join(out_dir,"wastewater_data.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " wastewater data\n")
        fd.write("# System Type: The system type \n")
        fd.write("# SQFT: system square feet  \n")
        fd.write("# HF Used: gal/yr Heating fuel used pre-retrofit\n")
        fd.write("# HF w/Retro: gal/yr Heating fuel used post-retrofit\n")
        fd.write("# kWh/yr: kWh/yr used pre-retrofit\n")
        fd.write("# kWh/yr w/ retro: kWh/yr used post-retrofit\n")
        fd.write("# Implementation Cost: cost to refit \n")
        fd.write("# HR: heat recovery (units ???) \n")
        fd.write("# Steam District: ??? \n")
        fd.write("# HDD kWh: assumption ??? \n") # JEN: what are these numbers?
        fd.write("# HDD HF: an assumption ??? \n")
        fd.write("# pop kWh: an assumption ??? \n")
        fd.write("# pop HF: an assumption ??? \n")
        fd.write("#### #### #### #### ####\n")
        fd.write("key,value\n")
        fd.close()
        
        try:
        
            ww_d = read_csv(data_file, comment = '#', index_col = 0).ix[com_id]
        except KeyError:
            raise StandardError, str(com_id) + " is not in " + data_file
        
        ## system type mapping From Neil
        ##Circulating/Gravity: Circulating/Gravity, Circulating/Pressure,
        ##                     Circulating/ST/DF
        ##Circulating/Vacuum: Circulating/Vacuum, Closed Haul/Vacuum
        ##Haul:  Closed Haul/Closed, Haul, Watering Point
        ##Pressure/Gravity: Pressure/Gravity, Pressure/NA, Pressure/ST/DF
        ##Washeteria/Honey Bucket: Washeteria
        ##None:  Wells/Gravity, Wells/NA, Wells/ST/DF, Wells/ST/OF 
        
        sys_map = {
                    "Circulating/Gravity":"Circulating/Gravity",
                    "Circulating/Pressurey":"Circulating/Gravity",
                    "Circulating/ST/DF":"Circulating/Gravity",
                    "Circulating/Vacuum":"Circulating/Vac",
                    "Closed Haul/Vacuum":"Circulating/Vac",
                    "Haul":"Haul",
                    "Closed Haul/Closed Haul":"Haul",
                    "Watering Point":"Haul",
                    "Pressure/Gravity": "Pressure/Gravity",
                    "Pressure/NA": "Pressure/Gravity",
                    "Pressure/ST/DF": "Pressure/Gravity",
                    "Washeteria":"Wash/HB",
                  } 
        try:
            sys_type = sys_map[ww_d["System Type"]]
            ww_a = read_csv(assumptions_file, comment = '#', index_col = 0)
            ww_a = ww_a.ix[sys_type]
            ww_a["assumption type used"] = sys_type
        except (KeyError, ValueError )as e:
            self.diagnostics.add_warning("preprocessor",
                                         "wastewater system type unknown")
            ww_d["assumption type used"] = "UNKNOWN"
            ww_d.to_csv(out_file, mode = 'a')
            
            return ww_d
     
        df = concat([ww_d,ww_a])
        df.to_csv(out_file, mode = 'a')
        return df
       
    def residential (self, fuel_file, data_file, out_dir, com_id):
        """
        preprocess the residential data
        pre:
            fuel_file, data_file are files
            out_dir is a path
            com_id is a string 
        post:
            residential data is in a file the model can use
        """
        out_file = out_dir + "residential_data.csv"
        fd = open(out_file,'w')
        fd.write("# " + com_id + " residential data\n")
        fd.write("# energy_region: region used by model \n")
        fd.write("# year: year of data  collected \n")
        fd.write("# total_occupied: # houses occupied \n")
        fd.write("# BEES_number: # of houses at BEES standard \n")
        fd.write("# BEES_avg_area: average Sq. ft. of BEES home \n")
        fd.write("# BEES_avg_EUI: BEES energy use intensity MMBtu/sq. ft.\n")
        fd.write("# BEES_total_consumption: BEES home energy consumption MMBtu \n")
        
        fd.write("# pre_number: # of houses pre-retrofit \n")
        fd.write("# pre_avg_area: average Sq. ft. of pre-retrofit home \n")
        fd.write("# pre_avg_EUI: pre-retrofit energy use intensity MMBtu/sq. ft.\n")
        
        fd.write("# post_number: # of houses at post-retrofit \n")
        fd.write("# post_avg_area: average Sq. ft. of post-retrofithome \n")
        fd.write("# post_avg_EUI: post-retrofit energy use intensity "+\
                 "MMBtu/sq. ft.\n")
        fd.write("# post_total_consumption: post-retrofit home energy consumption"+\
                 " MMBtu \n")
                 
        fd.write("# opportunity_non-Wx_HERP_BEES:  # of houses \n")
        fd.write("# opportunity_potential_reduction: ???? \n")
        fd.write("# opportunity_savings: potention savings in heating Fuel(gal)\n")
        fd.write("# opportunity_total_percent_community_savings: ???\n")
        
        fd.write("# Total; Utility Gas; LP; Electricity; Fuel Oil; "+\
                "Coal; Wood; Solar; Other; No Fuel Used: % of heating fuel types\n")
        fd.write("#### #### #### #### ####\n")
        fd.write("key,value\n")
        fd.close()
        
        fuel = read_csv(fuel_file, index_col=0, comment = "#").ix[com_id]
        fuel = fuel.ix[["Total", "Utility Gas", "LP", "Electricity", "Fuel Oil",
                        "Coal", "Wood", "Solar", "Other", "No fuel used"]]
        
        data = read_csv(data_file, index_col=0, comment = "#").ix[com_id]
        
        df = concat([data,fuel])
        del df.T["energy_region"]
        df.to_csv(out_file,mode="a")
        return df.ix['year']
    
    def region (self, data_file, premium_file, out_dir, com_id):
        """
        preprocess the regional input items
        pre:
            data_file, premium_file is are files
        post:
            regional related items are in a file the model can read
        """
        region = read_csv(data_file, index_col=0,
                                            comment='#').energy_region[com_id]
        premium = read_csv(premium_file, index_col=0, 
                                            comment='#').premium[region]
    
        out_file = os.path.join(out_dir, "region.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " residential data\n")
        fd.write("# region: region used by model \n")
        fd.write("#### #### #### #### ####\n")
        fd.write("key,value \n")
        fd.write("region,"+ str(region) + "\n")
        fd.write("premium," + str(premium) + "\n")
        fd.close()
    
        
    def preprocess (self, data_dir, out_dir, com_id):
        """
        preprocess data in to data dir 
        
        pre:
            data dir: path to the data files from the AAEM-data dir
            out_dir: save location
            com_id: community id("Name")
        post:
            all of the files necessary to run the model are in out_dir, if out_dir
        dose not it exist it is created
        """
        
         # join makes it a directory not a file 
        data_dir = os.path.join(os.path.abspath(data_dir),"")
        out_dir = os.path.join(os.path.abspath(out_dir),"")
        try:
            os.makedirs(out_dir)
        except OSError:
            pass
        
        ### copy files that still need their own preprocessor function yet
        shutil.copy(os.path.join(data_dir,"diesel_fuel_prices.csv"), out_dir)
        shutil.copy(os.path.join(data_dir,"hdd.csv"), out_dir)
        shutil.copy(os.path.join(data_dir,"cpi.csv"), out_dir)
    
        ###
        
        self.region(os.path.join(data_dir,"res_model_data.csv"),
               os.path.join(data_dir,"heating_fuel_premium.csv"),out_dir,com_id)
        
        pop = self.population(os.path.join(data_dir,"population.csv"),
                                                            out_dir,com_id)
        year = self.residential(os.path.join(data_dir,"res_fuel_source.csv"), 
                         os.path.join(data_dir,"res_model_data.csv"),
                    out_dir, com_id)
        base_pop = np.float(pop.ix[year])
        self.wastewater(os.path.join(data_dir,"ww_data.csv"),
                        os.path.join(data_dir,"ww_assumptions.csv"),
                   out_dir, com_id)
        
        
        try:
            self.electricity(os.path.join(data_dir,
                                        "2013-add-power-cost-equalization-pce-data.csv"), 
                                                                        out_dir,
                                                                        com_id)
            self.electricity_prices(os.path.join(data_dir,
                                        "2013-add-power-cost-equalization-pce-data.csv"),
                                                                        out_dir,
                                                                        com_id)
            self.electricity_generation(os.path.join(data_dir,
                                        "2013-add-power-cost-equalization-pce-data.csv"), 
                                                                        out_dir,
                                                                        com_id)
        except KeyError:
            self.electricity(os.path.join(data_dir,"EIA.csv"), out_dir, com_id)
            self.diagnostics.add_note("preprocessor","no $/kWh estimates")
            self.diagnostics.add_note("preprocessor","no generation estimates")
            

        try:
            self.interties(os.path.join(data_dir,"interties.csv"),
                                                                out_dir,com_id)
        except KeyError:
            self.diagnostics.add_note("preprocessor", 
                                                    "no intertie on community")
        

        self.buildings(os.path.join(data_dir, "non_res_buildings.csv"), 
                       os.path.join(data_dir, "com_building_estimates.csv"),
                       os.path.join(data_dir,"com_num_buildings.csv"),
                       out_dir, com_id, base_pop)
        
        self.yearly_generation(os.path.join(data_dir, 
                            "2013-add-power-cost-equalization-pce-data.csv"),
                               os.path.join(data_dir, 
                            "purchased_power_lib.csv"),out_dir,com_id)
    
    def electricity_prices (self, in_file, out_dir, com_id):
        """
        pre process fuel prices
        """
        data = read_csv(in_file, index_col=1, comment = "#").ix[com_id]
        data = data[["year","month","residential_rate",
                     "pce_rate","effective_rate","residential_kwh_sold",
                                         "commercial_kwh_sold",
                                         "community_kwh_sold",
                                         "government_kwh_sold",
                                         "unbilled_kwh", "fuel_cost"]]
        
        last_year = data["year"].max()
        while len(data[data["year"] == last_year]) != 12:
            last_year -= 1 
                                    
                                    
        elec_fuel_cost = (data[data["year"] == last_year]['fuel_cost'].mean()\
                     / data[data["year"] == last_year][["residential_kwh_sold",
                                         "commercial_kwh_sold",
                                         "community_kwh_sold",
                                         "government_kwh_sold",
                                         "unbilled_kwh"]].mean().sum())
                                         
        res_nonPCE_price = data[data["year"] == \
                                last_year]["residential_rate"].mean()
        elec_nonFuel_cost = res_nonPCE_price - elec_fuel_cost
        
        self.diagnostics.add_note("preprocessor",
                                "calculated res non-PCE elec cost: " + \
                                 str(res_nonPCE_price))
        self.diagnostics.add_note("preprocessor",
                                    "calculated elec non-fuel cost: " + \
                                    str(elec_nonFuel_cost))
                                    
        out_file = os.path.join(out_dir, "prices.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " electricity consumption\n")
        fd.write("# all units are in $/kWh \n")
        fd.write("#### #### #### #### ####\n")
        fd.write("key,value \n")
        fd.write("res non-PCE elec cost,"+ str(res_nonPCE_price) + "\n")
        fd.write("elec non-fuel cost," + str(elec_nonFuel_cost) + "\n")
        fd.close()
    
    def yearly_generation (self, in_file, lib_file, out_dir, com_id):
        """
        pre process kwh generation by year 
        """
        try:
            lib = read_csv(lib_file, index_col=0, comment = '#').ix[com_id]
        except:
            pass
        data = read_csv(in_file, index_col=1, comment = "#").ix[com_id]
        data = data[["year","diesel_kwh_generated",
                     "powerhouse_consumption_kwh","hydro_kwh_generated",
                     "other_1_kwh_generated","other_1_kwh_type",
                     "other_2_kwh_generated","other_2_kwh_type",
                     'purchased_from','kwh_purchased',
                     "fuel_used_gal","residential_kwh_sold",
                                         "commercial_kwh_sold",
                                         "community_kwh_sold",
                                         "government_kwh_sold",
                                         "unbilled_kwh"]]
        #~ print data
        try:
            p_key = data[data["purchased_from"].notnull()]\
                                                ["purchased_from"].values[0]
            p_key = lib[lib['purchased_from'] == p_key]\
                                        ['Energy Source'].values[0].lower()
        except:
            p_key = None
        try:
            o1_key = data[data["other_1_kwh_type"].notnull()]\
                                        ["other_1_kwh_type"].values[0].lower()
            if o1_key not in ('diesel', 'natural gas','wind', 'solar'):                        
                o1_key = None
        except:
            o1_key = None
        
        try:
            o2_key = data[data["other_2_kwh_type"].notnull()]\
                                         ["other_2_kwh_type"].values[0].lower()
            if o2_key not in ('diesel', 'natural gas','wind', 'solar'):                        
                o2_key = None
        except:
            o2_key = None
        
        sums = []
        for year in set(data["year"].values):
            if len(data[data["year"] == year]) != 12:
                continue
            temp = data[data["year"] == year].sum()
            temp["year"] = int(year)
            temp['generation'] = temp[['diesel_kwh_generated',
                                        "powerhouse_consumption_kwh",
                                        "hydro_kwh_generated",
                                        "other_1_kwh_generated",
                                        "other_2_kwh_generated",
                                        "kwh_purchased"]].sum()
            
            temp['generation diesel'] = temp['diesel_kwh_generated']
            temp['generation hydro'] = temp['hydro_kwh_generated']
            
            
            if np.isreal(temp["other_1_kwh_generated"]) and o1_key is not None:
                val = temp["other_1_kwh_generated"]
                if o1_key == "diesel":
                    temp['generation diesel'] = temp['generation diesel'] + val
                temp['generation ' + o1_key] = val
            if np.isreal(temp["other_1_kwh_generated"]) and o2_key is not None:
                val =  temp["other_1_kwh_generated"]
                if o2_key == "diesel":
                    temp['generation diesel'] = temp['generation diesel'] + val
                temp['generation ' + o2_key] = val
            if np.isreal(temp["other_1_kwh_generated"]) and p_key is not None:
                val = temp['kwh_purchased']
                if p_key == "diesel":
                    temp['generation diesel'] = temp['generation diesel'] + val
                temp['generation ' + p_key] = val
            
            
            temp['consumption'] = temp[["residential_kwh_sold",
                                         "commercial_kwh_sold",
                                         "community_kwh_sold",
                                         "government_kwh_sold",
                                         "unbilled_kwh"]].sum().sum()
            temp['consumption residential'] = temp["residential_kwh_sold"].sum()
            temp['consumption non-residential'] = temp['consumption'] - \
                                                 temp['consumption residential']
            
            temp['net generation'] = temp['generation'] - \
                                     temp["powerhouse_consumption_kwh"]
            temp['fuel used'] = temp['fuel_used_gal']
            temp['line loss'] = 1.0 - temp['consumption']/temp['net generation']
            temp['efficiency'] = temp['generation'] / temp['fuel_used_gal']
            sums.append(temp)
        
        df_diesel = DataFrame(sums)[["year",'generation diesel']].set_index('year')
        df_hydro = DataFrame(sums)[["year",'generation hydro']].set_index('year')

        try:
            df_gas = DataFrame(sums)[["year",'generation natural gas']].set_index('year')
        except KeyError:
            df_gas = DataFrame({"year":(2003,2004),
                                "generation natural gas":(np.nan,np.nan)}).set_index('year')
        try:
            df_wind = DataFrame(sums)[["year",'generation wind']].set_index('year')
        except KeyError:
            df_wind = DataFrame({"year":(2003,2004),
                                "generation wind":(np.nan,np.nan)}).set_index('year')
        try:
            df_solar = DataFrame(sums)[["year",'generation solar']].set_index('year')
        except KeyError:
            df_solar = DataFrame({"year":(2003,2004),
                                "generation solar":(np.nan,np.nan)}).set_index('year')
        try:
            df_biomass = DataFrame(sums)[["year",'biomass']].set_index('year')
        except KeyError:
            df_biomass = DataFrame({"year":(2003,2004),
                                "generation biomass":(np.nan,np.nan)}).set_index('year')

        df = DataFrame(sums)[['year','generation','consumption','fuel used',
                              'efficiency', 'line loss', 'net generation', 
                              'consumption residential', 
                              'consumption non-residential']].set_index("year")
        
        df = concat([df,df_diesel,df_hydro,df_gas,df_wind,df_solar,df_biomass], axis = 1)
        
        out_file = os.path.join(out_dir, "yearly_generation.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " kWh Generation data\n")
        fd.write("# generation (kWh/yr) gross generation\n")
        fd.write("# consumption(kWh/yr) total kwh sold\n")
        fd.write("# fuel used(gal/yr) fuel used in generation\n")
        fd.write('# efficiency (kwh/gal) efficiency of generator/year\n')
        fd.write('# line loss (% as decimal) kwh lost from transmission\n')
        fd.write("# net generation(kWh/yr) generation without " +\
                                                    "powerhouse consumption\n")
        fd.write("# consumption residential (kWh/yr) residential kwh sold\n")
        fd.write("# consumption non-residential (kWh/yr) non-residential " + \
                                                                "kwh sold\n")
        fd.write("# generation <fuel source> (kWh/yr) generation from source\n")
        fd.write("#### #### #### #### ####\n")
        fd.close()
        df.to_csv(out_file,mode="a")
        
    def electricity_generation (self, in_file, out_dir, com_id):
        """
        pre process kwh generation 
        """
        data = read_csv(in_file, index_col=1, comment = "#").ix[com_id]
        data = data[["year","diesel_kwh_generated",
                     "powerhouse_consumption_kwh","hydro_kwh_generated",
                     "other_1_kwh_generated","other_2_kwh_generated",
                     "fuel_used_gal"]]
                     
        
        last_year = data["year"].max()
        while len(data[data["year"] == last_year]) != 12:
            last_year -= 1 
    
        generation = data[data["year"]==last_year][["diesel_kwh_generated",
                     "powerhouse_consumption_kwh","hydro_kwh_generated",
                     "other_1_kwh_generated",
                     "other_2_kwh_generated"]].sum().sum()
        
        net_generation = generation - data[data["year"]==last_year][\
                                        "powerhouse_consumption_kwh"].sum()
                                        
        fuel_used = data[data["year"]==last_year]["fuel_used_gal"].sum()

        out_file = os.path.join(out_dir, "generation.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " kWh Generation data\n")
        fd.write("# generation (kWh/yr) gross generation\n")
        fd.write("# net generation(kWh/yr) generation-powerhouse consumption\n")
        fd.write("# consumption HF(gal/yr) heating fuel used in generation\n")
        fd.write("#### #### #### #### ####\n")
        fd.write("key,value\n")
        fd.write("generation," + str(generation) + "\n")
        fd.write("net_generation," + str(net_generation) + "\n")
        fd.write("consumption HF," + str(fuel_used) + "\n")
        fd.close()
        
    def interties (self, in_file, out_dir, com_id):
        """ 
        preprocess interties
        
        pre:
            in_infile is the intertie data file
            out_dir is a directory
            com_id is a string
        post
            com_id's intertie data is saved to out_dir as interties.csv
        """
        data = read_csv(in_file, index_col=0, 
                        comment = "#").ix[com_id].fillna("''")
        out_file = os.path.join(out_dir, "interties.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " intertied communities\n")
        fd.write("#### #### #### #### ####\n")
        fd.close()
        data.to_csv(out_file, mode = 'a')
        return data

    def buildings (self, in_file, est_file, count_file, out_dir, com_id, pop):
        """ Function doc """
        data = read_csv(in_file, index_col=0, comment = "#").ix[com_id]
        
        l = ["Square Feet",
             "implementation cost", "Electric", "Electric Post", "Fuel Oil",
             "Fuel Oil Post", "HW District", "HW District Post", "Natural Gas", 
             "Natural Gas Post", "Propane", "Propane Post"]
        data[l] = data[l].replace(r'\s+', np.nan, regex=True)
        
        
        out_file = os.path.join(out_dir, "community_buildings.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " non-res buildigns\n")
        fd.close()
       
            
       
        c = ["Building Type", "Square Feet", "Audited", "Retrofits Done",
             "implementation cost", "Electric", "Electric Post", "Fuel Oil",
             "Fuel Oil Post", "HW District", "HW District Post", "Natural Gas", 
             "Natural Gas Post", "Propane", "Propane Post"]
        data.to_csv(out_file, columns = c, mode="a", index=False)
        
        
        out_file = os.path.join(out_dir, "com_num_buildings.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " estimated number of buildings\n")
        fd.write("#### #### #### #### ####\n")
        fd.write("key,value\n")
        fd.close()
        
        data = read_csv(count_file ,comment = "#", index_col = 0,
                                                 header = 0).ix[com_id]
        data.to_csv(out_file,mode="a", header = False)
        
        
        
        
        out_file = out_file = os.path.join(out_dir, 
                                                "com_building_estimates.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " community building estimates\n")
        fd.close()
        
        data = read_csv(est_file ,comment = u"#",index_col = 0, header = 0)
        units = set(data.ix["Estimate units"])
        l = []
        for itm in units:
            l.append(data.T[data.ix["Estimate units"] == itm]\
                          [(data.T[data.ix["Estimate units"] == itm]\
                          ["Lower Limit"].astype(float) <= pop)]\
                          [data.ix["Estimate units"] == itm]\
                          [(data.T[data.ix["Estimate units"] == itm]\
                          ["Upper Limit"].astype(float) > pop)])
        df = concat(l)
        del(df["Lower Limit"])
        del(df["Upper Limit"])
        #~ del(df["Estimate units"])  
        df = df.T
        
        df.to_csv(out_file,mode="a", header = False)
        
        
        


def preprocess(data_dir, out_dir, com_id):
    """
    """
    pp = Preprocessor()
    pp.preprocess(data_dir,out_dir,com_id)
    pp.diagnostics.save_messages(os.path.join(out_dir,
                                            "preprocessor_diagnostis.csv"))
    
