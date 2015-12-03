"""
preprocessor.py
ross spicer

process data into a format for the model to use 
"""
from pandas import DataFrame,read_csv, concat
import shutil
import os.path
from diagnostics import diagnostics

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
                                         "unbilled_kwh"]]
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
                              "commercial","industrial"]).set_index("year")
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
                   "non-residential":non_res.values}).set_index("year")

            
            
        out_file = os.path.join(out_dir,"electricity.csv")
        fd = open(out_file,'w')
        fd.write("# " + com_id + " electricity consumption\n")
        fd.write("# all units are in kWh/year for a given year and category\n")
        fd.write("#### #### #### #### ####\n")
        fd.close()    
        
        data.to_csv(out_dir+"electricity.csv", mode="a")
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
    
    def region (self, data_file, premium_file, out_dir, com_id):
        """
        preprocess the regional input items
        pre:
            data_file, premium_file is are files
        post:
            regional related items are in a file the model can read
        """
        region = read_csv(data_file, index_col=0, comment='#').energy_region[com_id]
        premium = read_csv(premium_file, index_col=0, comment='#').premium[region]
    
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
        shutil.copy(os.path.join(data_dir,"com_benchmark_data.csv"), out_dir)
        shutil.copy(os.path.join(data_dir,"com_building_estimates.csv"),out_dir)
        shutil.copy(os.path.join(data_dir,"com_num_buildings.csv"), out_dir)
        shutil.copy(os.path.join(data_dir,"diesel_fuel_prices.csv"), out_dir)
        shutil.copy(os.path.join(data_dir,"hdd.csv"), out_dir)
        shutil.copy(os.path.join(data_dir,"cpi.csv"), out_dir)
    
        ###
        
        self.region(os.path.join(data_dir,"res_model_data.csv"),
               os.path.join(data_dir,"heating_fuel_premium.csv"),out_dir,com_id)
        
        self.population(os.path.join(data_dir,"population.csv"),out_dir,com_id)
        self.residential(os.path.join(data_dir,"res_fuel_source.csv"), 
                         os.path.join(data_dir,"res_model_data.csv"),
                    out_dir, com_id)
        self.wastewater(os.path.join(data_dir,"ww_data.csv"),
                        os.path.join(data_dir,"ww_assumptions.csv"),
                   out_dir, com_id)
        
        
        try:
            self.electricity(os.path.join(data_dir,
                                        "power-cost-equalization-pce-data.csv"), 
                                                                        out_dir,
                                                                        com_id)
            self.electricity_prices(os.path.join(data_dir,
                                        "power-cost-equalization-pce-data.csv"),
                                                                        out_dir,
                                                                        com_id)
            self.electricity_genneration(os.path.join(data_dir,
                                        "power-cost-equalization-pce-data.csv"), 
                                                                        out_dir,
                                                                        com_id)
        except KeyError:
            self.electricity(os.path.join(data_dir,"EIA.csv"), out_dir, com_id)
            self.diagnostics.add_note("preprocessor","no $/kWh estimates")
            self.diagnostics.add_note("preprocessor","no generation estimates")
            
        
    
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
                                         "unbilled_kwh", "fuel_cost"]].tail(1)
        elec_fuel_cost = (data['fuel_cost']/data[["residential_kwh_sold",
                                         "commercial_kwh_sold",
                                         "community_kwh_sold",
                                         "government_kwh_sold",
                                         "unbilled_kwh"]].T.sum()).max()
                                         
        res_nonPCE_price = data["residential_rate"].max()
        elec_nonFuel_cost = res_nonPCE_price - elec_fuel_cost
        
        self.diagnostics.add_note("preprocessor",
                                "suggestion: add (res non-PCE elec cost: " + \
                                 str(res_nonPCE_price) +\
                                 ") to the community section of your "+\
                                 "community_data.yaml file for this community ")
        self.diagnostics.add_note("preprocessor",
                                    "suggestion: add (elec non-fuel cost: " + \
                                    str(elec_nonFuel_cost) +\
                                    ") to the community section of your"+\
                                " community_data.yaml file for this community ")
                                
    def electricity_genneration (self, in_file, out_dir, com_id):
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
        

def preprocess(data_dir, out_dir, com_id):
    """
    """
    pp = Preprocessor()
    pp.preprocess(data_dir,out_dir,com_id)
    pp.diagnostics.save_messages(os.path.join(out_dir,
                                            "preprocessor_diagnostis.csv"))
    
