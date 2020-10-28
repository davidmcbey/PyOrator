# -------------------------------------------------------------------------------
# Name:        ora_crop_model.py
# Purpose:     functions for crop model
# Author:      Dave Mcbey
# Created:     24/09/2020
# Licence:     <your licence>
# defs:
#
#
# Description:
#
# -------------------------------------------------------------------------------
# !/usr/bin/env python


__prog__ = 'ora_crop_model.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os
import numpy as np
from pandas import DataFrame
from ora_excel_read import read_single_crop_and_soil_data, read_rotations_crop_and_soil_data, read_weather_data_crops, \
    _read_weather_sheet, _read_crop_vars, _read_location_sheet
from thornthwaite import thornthwaite
from ora_water_model import SoilWater


# from weather_inputs_get_data_new import calc_potential_evapotrans_fr, calc_potential_evapotrans_ss
# from ora_water_model import get_soil_water_constants, add_pet_to_weather
# from ora_low_level_fns import soil_water

def test_crop_algorithms(form):

    # Set flag to indicate whether single crop or rotations to be used
    crop_rotations = form.w_crop_rotations.isChecked()
    # Set npp calculation method
    npp_calc = str(form.w_npp_calc.currentText())
    xls_inp_fname = os.path.normpath(form.w_lbl13.text())
    if not os.path.isfile(xls_inp_fname):
        print('Excel input file ' + xls_inp_fname + 'must exist')

        return

    # Call function to get all weather data, then slice into rain, temp for steady state and forward runs
    # Reset index so all dataframes run from 0 to 11
    weather_dataframe = read_weather_data_crops(xls_inp_fname)
    ss_rain_data = weather_dataframe.iloc[0:12]
    ss_air_temp_data = weather_dataframe.iloc[14:26]
    ss_air_temp_data.reset_index(level=0, inplace=True, drop=True)
    fr_rain_data = weather_dataframe.iloc[29:41]
    fr_rain_data.reset_index(level=0, inplace=True, drop=True)
    fr_air_temp_data = weather_dataframe.iloc[43:55]
    fr_air_temp_data.reset_index(level=0, inplace=True, drop=True)

    # Dictionary containing data on plant growing seasons. TO DO: FOR GROWING SEASONS THAT START LATE IN YEAR AND GO INTO
    # NEXT YEAR (EG TOMATOES), DO CALCULATIONS WORK PROPERLY?
    # IS THIS DATA DOUBLED UP - HAS MIKE CODED THIS SOMEWHERE
    grow_seas = {'Grassland': {'sow_mon': 1, 'har_mon': 12, 'grow_mons': range(1, 13), },
        'Shrubland': {'sow_mon': 1, 'har_mon': 12, 'grow_mons': range(1, 13), },
        'Maize': {'sow_mon': 7, 'har_mon': 11, 'grow_mons': range(7, 12), },
        'Haricot beans': {'sow_mon': 7, 'har_mon': 10, 'grow_mons': range(7, 11), },
        'Teff': {'sow_mon': 8, 'har_mon': 11, 'grow_mons': range(8, 12), },
        'Finger Millet': {'sow_mon': 5, 'har_mon': 9, 'grow_mons': range(5, 10), },
        'Pepper': {'sow_mon': 3, 'har_mon': 10, 'grow_mons': range(3, 11), },
        'Coffee': {'sow_mon': 1, 'har_mon': 12, 'grow_mons': range(1, 13), },
        'Chat': {'sow_mon': 1, 'har_mon': 12, 'grow_mons': range(1, 13), },
        'Tomatoes': {'sow_mon': 11, 'har_mon': 2, 'grow_mons': [11, 12, 1, 2], },
        'Cabbage': {'sow_mon': 11, 'har_mon': 3, 'grow_mons': [11, 12, 1, 2, 3], },
        'Wheat': {'sow_mon': 8, 'har_mon': 11, 'grow_mons': range(8, 12), },
        'Sorghum': {'sow_mon': 5, 'har_mon': 9, 'grow_mons': range(5, 10), }, }

    # TODO Use this dictionary to replace grow_seas above
    crop_parms = _read_crop_vars(xls_inp_fname, 'Crop parms')


    class CropInfo:
        """Information on crops"""

        def __init__(self, area_name, crop_area, soil_depth, pcnt_clay, pcnt_silt, pcnt_sand, pcnt_carbon, bulk_den, ph,
                     salinity, ):

            self.area_name = area_name
            self.crop_area = crop_area
            self.soil_depth = soil_depth
            self.pcnt_clay = pcnt_clay
            self.pcnt_silt = pcnt_silt
            self.pcnt_sand = pcnt_sand
            self.pcnt_carbon = pcnt_carbon
            self.bulk_den = bulk_den
            self.ph = ph
            self.salinity = salinity

            if crop_rotations:
                self.rot_length = crop_data[column][12]
                crop_rotation_info = crop_data[column][14:134]
                crop_rotation_info = crop_rotation_info.reset_index(drop=True)
                self.crop_rotation_info = crop_rotation_info
                crop_names = crop_rotation_info.to_list()
                crop_names_list = list(set(crop_names))
                if 'None' in crop_names_list:
                    crop_names_list.remove('None')
                self.crop_names = crop_names_list

            else:
                self.crop_name = crop_data[column][11]
                self.n_fert_applied = crop_data[column][12]
                self.p_fert_applied = crop_data[column][13]
                self.typ_yield = crop_data[column][14]
                self.mon_fert_app = crop_data[column][15]
                self.typ_org_waste_app = crop_data[column][17]
                self.mon_org_waste_app = crop_data[column][18]
                self.typ_amnt_org_waste_app = crop_data[column][19]
                self.irrig_amnt = crop_data[column][21]
                self.max_wat_avail = crop_data[column][22]

        def split_into_years(self, dataframe):
            """Splits 10 year dataframes into yearly chunks. Reset index to remove timestep"""

            year_1_df = DataFrame(dataframe.loc[0:11])
            year_1_df = year_1_df.set_index(0)
            year_2_df = DataFrame(dataframe.loc[12:23])
            year_2_df = year_2_df.set_index(0)
            year_3_df = DataFrame(dataframe.loc[24:35])
            year_3_df = year_3_df.set_index(0)
            year_4_df = DataFrame(dataframe.loc[36:47])
            year_4_df = year_4_df.set_index(0)
            year_5_df = DataFrame(dataframe.loc[48:59])
            year_5_df = year_5_df.set_index(0)
            year_6_df = DataFrame(dataframe.loc[60:71])
            year_6_df = year_6_df.set_index(0)
            year_7_df = DataFrame(dataframe.loc[72:83])
            year_7_df = year_7_df.set_index(0)
            year_8_df = DataFrame(dataframe.loc[84:95])
            year_8_df = year_8_df.set_index(0)
            year_9_df = DataFrame(dataframe.loc[96:107])
            year_9_df = year_9_df.set_index(0)
            year_10_df = DataFrame(dataframe.loc[108:119])
            year_10_df = year_10_df.set_index(0)

            year_list = [year_1_df, year_2_df, year_3_df, year_4_df, year_5_df, year_6_df, year_7_df, year_8_df,
                         year_9_df, year_10_df]
            return year_list

        def calc_grow_season_by_crop(self, ls_of_dataframes):
            """Calculate the total temp/precip for each crop per year"""

            # Create dictionaries by iterating over each DF and summing temp/precip for each crop
            ls_of_dics = []
            for df in ls_of_dataframes:
                dic = {}
                for index, row in df.itertuples():
                    if index in self.crop_names:
                        if index in dic:
                            dic[index] = (dic[index] + row)
                            continue
                        elif index not in dic:
                            dic[index] = row
                            continue
                    else:
                        continue
                ls_of_dics.append(dic)

            return ls_of_dics

        def get_land_use(self):
            """Pull monthly land use data from excel sheet"""
            # TODO THIS IS A PLACEHOLDER UNTIL I WORK OUT HOW TO DO IT. NEED TO CALCULATE/PULL
            # CROP NUMBER (OR JUST USE NAMES) AND THEN HOW TO MAKE IT MONTHLY RATHER THAN YEARLY
            land_use = []
            for num in range(0, 120):
                land_use.append(self.crop_name)
            self.crop_rotation_info = land_use

        def npp_leith_1972(self):
            """Calculate steady and non-steady state npp using Leith's (1972) equations, for ten years"""

            if crop_rotations:
                # Convert crop rotations info to list
                growing_season_rotations = self.crop_rotation_info
                grow_list = growing_season_rotations.to_list()
                # Pull dictionary cotaining temp and rain data for SS and FR
                rain_temp_ss, rain_temp_fwd = _read_weather_sheet(xls_inp_fname, 'Weather', 14)
                # Split into list of temps and list of rains for SS and FR
                rain_ss = rain_temp_ss['precip']
                temp_ss = rain_temp_ss['tair']
                rain_fr = rain_temp_fwd['precip']
                temp_fr = rain_temp_fwd['tair']

                # Merge weather data lists with growing season lists to make dataframes
                rain_ss_grow = DataFrame(zip(grow_list, rain_ss))
                temp_ss_grow = DataFrame(zip(grow_list, temp_ss))
                rain_fr_grow = DataFrame(zip(grow_list, rain_fr))
                temp_fr_grow = DataFrame(zip(grow_list, temp_fr))

                # Split each dataframe into 1 year chunks and save as list
                rain_ss_grow_years = self.split_into_years(rain_ss_grow)
                temp_ss_grow_years = self.split_into_years(temp_ss_grow)
                rain_fr_grow_years = self.split_into_years(rain_fr_grow)
                temp_fr_grow_years = self.split_into_years(temp_fr_grow)

                # For each year, make a dictionary for each crop containing total growing season temp/precip
                rain_ss_total_per_crop = DataFrame(self.calc_grow_season_by_crop(rain_ss_grow_years))
                temp_ss_total_per_crop = DataFrame(self.calc_grow_season_by_crop(temp_ss_grow_years))
                rain_fr_total_per_crop = DataFrame(self.calc_grow_season_by_crop(rain_fr_grow_years))
                temp_fr_total_per_crop = DataFrame(self.calc_grow_season_by_crop(temp_fr_grow_years))

                # Calculate NPP for each crop, for each year EQ 3.1.1
                ss_npp = DataFrame(np.minimum(5 * 3 * (1 - np.exp(-0.00064 * rain_ss_total_per_crop)),
                                              5 * 3 / (1 + np.exp(1.315 - 0.119 * temp_ss_total_per_crop))))
                fr_npp = DataFrame(np.minimum(5 * 3 * (1 - np.exp(-0.00064 * rain_fr_total_per_crop)),
                                              5 * 3 / (1 + np.exp(1.315 - 0.119 * temp_fr_total_per_crop))))

                # Create dic with harv_index for each crop
                harv_index_dic = {}
                for crop in self.crop_names:
                    for key, value in crop_parms.items():
                        if crop == key:
                            harv_index = value.get('harv_indx')
                            harv_index_dic[crop] = harv_index

                # Slice dataframe and calculate npp * harvest index for each crop
                crop_prod_typ = DataFrame()
                for header, col in ss_npp.items():
                    if header in harv_index_dic.keys():
                        h_index = harv_index_dic[header]
                        plant_typ = (col * h_index)
                        crop_prod_typ = crop_prod_typ.append(plant_typ)

                crop_prod_atyp = DataFrame()
                for header, col in ss_npp.items():
                    if header in harv_index_dic.keys():
                        h_index = harv_index_dic[header]
                        plant_atyp = (col * h_index)
                        crop_prod_atyp = crop_prod_atyp.append(plant_atyp)

                # Eq 3.0.2
                p_plant_atyp = crop_prod_atyp / crop_prod_typ

                # Convert yearly p_plant_atyp into monthly values. This assumes ratio of atyp to typ is constant through
                # year, and returns a value of 1 if nothing is growing that month.
                prod_comp_ss_mon = []
                rotations = self.crop_rotation_info.to_list()
                year = 0
                mon = 0

                for rotation in rotations:
                    if rotation == 'None':
                        mon_value = 1
                        prod_comp_ss_mon.append(mon_value)
                        mon += 1
                        if mon == 12:
                            year += 1
                            mon = 0
                        else:
                            continue

                    else:
                        mon_value = p_plant_atyp.loc[rotation,year]
                        prod_comp_ss_mon.append(mon_value)
                        mon += 1
                        if mon == 12:
                            year += 1
                            mon = 0
                        else:
                            continue

                self.yield_atyp_mon = prod_comp_ss_mon

                # Eq 3.1.1
                # TODO Get typical yield info for crop rotations - how should this be input?
                self.typ_yield = 3.44
                c_yld_atyp = self.typ_yield * p_plant_atyp

            else:
                # Get the crop sowing and harvest months from the dictionary above, then add as list
                growing_season_single = grow_seas.get(self.crop_name, {}).get('grow_mons')
                self.grow_season = list(growing_season_single)

                # Use growing season list to match with months on temp and rain dictionaries to return totals
                # use month + 1 as weather data is 0 indexed so month 1 = 0
                dict_1 = ss_air_temp_data
                ss_air_temps = []
                for years, months in dict_1.items():
                    temp = []
                    for month, value in months.items():
                        if (month + 1) in self.grow_season:
                            temp.append(value)
                    sum_temp = sum(temp)
                    ss_air_temps.append(sum_temp)
                ss_air_temps = np.array(ss_air_temps)

                dict_2 = ss_rain_data
                ss_rains = []
                for years, months in dict_2.items():
                    temp = []
                    for month, value in months.items():
                        if (month + 1) in self.grow_season:
                            temp.append(value)
                    sum_temp = sum(temp)
                    ss_rains.append(sum_temp)
                ss_rains = np.array(ss_rains)
                # Equation to calculate limiting factor (rain or temp), and return npp for each year
                ss_npp = np.minimum(5 * 3 * (1 - np.exp(-0.00064 * ss_rains)),
                                    5 * 3 / (1 + np.exp(1.315 - 0.119 * ss_air_temps)))

                dict_1 = fr_air_temp_data
                fr_air_temps = []
                for years, months in dict_1.items():
                    temp = []
                    for month, value in months.items():
                        if (month + 1) in self.grow_season:
                            temp.append(value)
                    sum_temp = sum(temp)
                    fr_air_temps.append(sum_temp)
                fr_air_temps = np.array(fr_air_temps)

                dict_2 = fr_rain_data
                fr_rains = []
                for years, months in dict_2.items():
                    temp = []
                    for month, value in months.items():
                        if (month + 1) in self.grow_season:
                            temp.append(value)
                    sum_temp = sum(temp)
                    fr_rains.append(sum_temp)
                fr_rains = np.array(fr_rains)
                # Equation to calculate limiting factor (rain or temp), and return npp for each year
                fr_npp = np.minimum(5 * 3 * (1 - np.exp(-0.00064 * fr_rains)),
                                    5 * 3 / (1 + np.exp(1.315 - 0.119 * fr_air_temps)))

                # Calculate production compared to steady state
                p_plant_atyp = fr_npp / ss_npp

                # get monthly figure -  TODO right now simply have growing equally all year but need
                # to change to reflect growing months? OR can I leave it as growing months never change, so production
                # compared to steady state will always be 1 in non-growing months?
                prod_comp_ss_mon = []
                prod_comp_ss_fr_list = p_plant_atyp.tolist()
                for year in prod_comp_ss_fr_list:
                    monthly = []
                    for number in range(0, 12):
                        temp_num = year * 1
                        monthly.append(temp_num)
                    prod_comp_ss_mon.append(monthly)

                # Make this one list, rather than list of lists
                flat_list = []
                for items in prod_comp_ss_mon:
                    for item in items:
                        flat_list.append(item)

                # Calculate actual yield
                c_yield_atyp = self.typ_yield * p_plant_atyp

                self.yield_atyp_mon = flat_list
                self.p_plant_atyp = p_plant_atyp
                self.yield_atyp = c_yield_atyp

        def npp_zaks_et_al_2007(self):
            """Calculate steady and non-steady state npp using Zaks et al (2007) equations, for ten years"""
            # Get the crop sowing and harvest months from the dictionary above, then add as list
            # TODO get this working for crop rotations also
            # Dictionary with days for each month (no leap years). Zero indexed to match how weather data is stored
            month_days_dic = {0: 31, 1: 28, 2: 31, 3: 30, 4: 31, 5: 30, 6: 31, 7: 31, 8: 30, 9: 31, 10: 30, 11: 31, }

            growing_season = grow_seas.get(self.crop_name, {}).get('grow_mons')
            self.grow_season = list(growing_season)

            # Calculate cumulative temperatures on growing degree days for each month STEADY STATE
            growing_degree_days = []
            dict_1 = ss_air_temp_data
            for years, months in dict_1.items():
                temp = []
                for month, value in months.items():
                    # Use month + 1 as ss_air_temp_data is zero indexed
                    if (month + 1) in self.grow_season:
                        # EQUATION 3.2.2
                        mon_days = month_days_dic.get(month)
                        temp_list = np.maximum(0, mon_days * (value - 5))
                        temp.append(temp_list)
                growing_degree_days.append(temp)
            ten_year_growing_degree_days_ss = np.array(growing_degree_days)
            self.ten_year_growing_degree_days_ss = ten_year_growing_degree_days_ss

            # Calculate cumulative temperatures on growing degree days for each month FORWARD RUN
            growing_degree_days = []
            dict_2 = fr_air_temp_data
            for years, months in dict_2.items():
                temp = []
                for month, value in months.items():
                    if (month + 1) in self.grow_season:
                        # Multiply average temp for month by days in month - CHANGE EQUATION TO ONE IN EXCEL/EQ 3.2.2
                        mon_days = month_days_dic.get(month)
                        temp_list = np.maximum(0, mon_days * (value - 5))
                        temp.append(temp_list)
                growing_degree_days.append(temp)
            ten_year_growing_degree_days_fr = np.array(growing_degree_days)
            self.ten_year_growing_degree_days_fr = ten_year_growing_degree_days_fr

            # Calculate potential and actual evapotransportation
            farm_location = _read_location_sheet(xls_inp_fname, 'Inputs1- Farm location', 13)
            farm_lat = farm_location[1]

            def calc_potential_evapotrans_ss(self):
                """calculate potential evapotransportation for steady state and forward runs"""

                thornthwaite_ten_years_ss = []
                for column in ss_air_temp_data:
                    year_temps = ss_air_temp_data[column].to_list()
                    thornthwaite_year = thornthwaite(year_temps, farm_lat)
                    thornthwaite_ten_years_ss.append(thornthwaite_year)

                return thornthwaite_ten_years_ss

            def calc_potential_evapotrans_fr(self):
                """calculate potential evapotransportation for forward runs"""

                thornthwaite_ten_years_fr = []
                for column in fr_air_temp_data:
                    year_temps = fr_air_temp_data[column].to_list()
                    thornthwaite_year = thornthwaite(year_temps, farm_lat)
                    thornthwaite_ten_years_fr.append(thornthwaite_year)
                return thornthwaite_ten_years_fr

            self.potential_evapotrans_ss = calc_potential_evapotrans_ss(self)
            self.potential_evapotrans_fr = calc_potential_evapotrans_fr(self)

            soil_water = SoilWater()
            soil_water_calcs = soil_water.append_vars()


            # Use ora_water_model to get permenant wilt points and field capacity
            # get water content at field capacity and at permanent wilting point (mm)
            # ======================================================================
            # Hard code these for now, but Mike will send code to pull/calculate
            tot_soc_meas = 36.064
            t_depth = 20
            t_bulk = 1.12
            pcnt_c = 1.61
            t_clay = 12.8
            t_silt = 47.5
            t_sand = 39.7
            # DUMMY NUMBERS UNTIL MIKE GIVES ME THE REAL ONE
            VWat = ten_yrs_days_in_month

            pcnt_c = tot_soc_meas / (t_depth * t_bulk)  # work back from conversion in hwsd_bil.py
            wc_fld_cap, wc_pwp = get_soil_water_constants(pcnt_c, t_clay, t_silt, t_sand, t_depth)
            # DUMMY ARRAY TO MAKE EQUATION WORK 3.2.4
            wc_pwp = ten_yrs_days_in_month

            # Use equation 3.2.4 to calculate actual evapotransportation. First, add value for maximum root depth
            for crop in crop_list:
                if self.crop_name in d_max_dic:
                    self.d_max = d_max_dic.get(self.crop_name)
                else:
                    print("Please enter crop maximum rooting depth: ")

            # Need Vwat - volume of water at timestep for rooting depth (steady state and forward run)
            # Equation 3.2.4. Use 'reduce' function to consider all 3 arguments

            actual_evapotrans_ss = np.minimum.reduce(
                [self.potential_evapotrans_ss, 5 * ten_yrs_days_in_month, (VWat - wc_pwp)])
            actual_evapotrans_fr = np.minimum.reduce(
                [self.potential_evapotrans_fr, 5 * ten_yrs_days_in_month, (VWat - wc_pwp)])
            self.actual_evapotrans_ss = actual_evapotrans_ss
            self.actual_evapotrans_fr = actual_evapotrans_fr

            # Use equation 3.2.3 to calculate water stress index (steady state and forward run)

            wat_stress_ss = self.actual_evapotrans_ss / self.potential_evapotrans_ss
            wat_stress_fr = self.actual_evapotrans_fr / self.potential_evapotrans_fr

            # Convert to Dataframe to slice so that only growing months are included, then back to NumPy array for calculating
            wat_stress_ss_df = DataFrame(wat_stress_ss)
            wat_stress_fr_df = DataFrame(wat_stress_fr)
            ss_df_slice = wat_stress_ss_df.loc[:, [col for col in self.grow_season]]
            fr_df_slice = wat_stress_fr_df.loc[:, [col for col in self.grow_season]]
            wat_stress_ss_slice = ss_df_slice.to_numpy()
            wat_stress_fr_slice = fr_df_slice.to_numpy()
            self.wat_stress_ss = wat_stress_ss_slice
            self.wat_stress_fr = wat_stress_fr_slice

            # Use equation 3.2.1 to calculate net primary production of C this month, relative to this month in a year
            # with different conditions
            c_npp_mon_ss = 27.20 * np.maximum(0, (
                        0.0396 / 1 + np.exp(6.33 - 1.5 * (self.ten_year_growing_degree_days_ss / 11500)) * (
                            39.58 * self.wat_stress_ss - 14.52)))
            c_npp_mon_fr = 27.20 * np.maximum(0, (
                        0.0396 / 1 + np.exp(6.33 - 1.5 * (self.ten_year_growing_degree_days_fr / 11500)) * (
                            39.58 * self.wat_stress_fr - 14.52)))

            # Now calculate production compared to steady state, by comparing each month with a month 10 years earlier
            # Return 0 rather than Nan by using np.nan_to_num
            # Ignore divide by 0 error
            np.seterr(divide='ignore', invalid='ignore')
            prod_comp_ss_mon = np.nan_to_num(c_npp_mon_fr / c_npp_mon_ss)
            # Sum all months to give total change in production for the year
            prod_com_ss_yr = np.nan_to_num(prod_comp_ss_mon.sum(axis=1))

            self.p_plant_atyp = prod_com_ss_yr

            # Calculate actual yield
            act_yield = self.typ_yield * prod_com_ss_yr
            self.yield_atyp = act_yield

    def get_single_crop_info_sliced():
        """Read input data for single crop"""
        crop_data = read_single_crop_and_soil_data(xls_inp_fname)
        single_crop_data_sliced = crop_data.loc[:, 'Unnamed: 4':'Unnamed: 8']
        return single_crop_data_sliced

    def get_crop_rotations_sliced():
        """Read input data for crop rotations"""
        crop_data = read_rotations_crop_and_soil_data(xls_inp_fname)
        return crop_data

    # pull either single crop or rotations data, then convert to list in order to iterate over columns
    if crop_rotations:
        crop_data = get_crop_rotations_sliced()
        columns = list(crop_data)
    else:
        crop_data = get_single_crop_info_sliced()
        columns = list(crop_data)

    # Create list to store each instance of the class, then create each instance of the class and append
    crop_list = []
    for column in columns:
        if crop_rotations:
            crop = CropInfo(area_name=crop_data[column][0], crop_area=crop_data[column][1],
                            soil_depth=crop_data[column][3], pcnt_clay=crop_data[column][4],
                            pcnt_silt=crop_data[column][5], pcnt_sand=crop_data[column][6],
                            pcnt_carbon=crop_data[column][7], bulk_den=crop_data[column][8], ph=crop_data[column][9],
                            salinity=crop_data[column][10], )
            crop_list.append(crop)

        else:

            crop = CropInfo(area_name=crop_data[column][0], crop_area=crop_data[column][1],
                            soil_depth=crop_data[column][3], pcnt_clay=crop_data[column][4],
                            pcnt_silt=crop_data[column][5], pcnt_sand=crop_data[column][6],
                            pcnt_carbon=crop_data[column][7], bulk_den=crop_data[column][8], ph=crop_data[column][9],
                            salinity=crop_data[column][10], )
            crop_list.append(crop)

    for crop in crop_list:
        if crop_rotations:
            pass
        # Get list of crop growing for each month. Assumes they won't change in non-rotation system
        else:
            crop.get_land_use()

        if npp_calc == 'MIAMI Model (Leith 1972)':
            crop.npp_leith_1972()
        elif npp_calc == 'Growing degree days and water stress (Zaks et al. 2007)':
            crop.npp_zaks_et_al_2007()
        elif npp_calc == 'Nutrient limitation (Reid 2002)':
            pass
        else:
            print('Please select NPP calculation method')

    print("\nThe following crops have been simulated:\n")
    for crop in crop_list:
        if crop_rotations:
            print(f"\tSUBPLOT NAME: {crop.area_name} CROPS: {crop.crop_names}")
        else:
            print(f"\tSUBPLOT NAME: {crop.area_name} CROP: {crop.crop_name}")
    return crop_list
