#-------------------------------------------------------------------------------
# Name:        ora_nitrogen_fns.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     26/12/2019
# Licence:     <your licence>
#
# Description:
#    Based on content in "Report on modelling work done for BREAD 101218v2_print.pdf"
#    Nitrogen is assumed to be held in 6 pools in the soil:
#            mineral N (nitrate and ammonium) and organic N (DPM, RPM, BIO and HUM-N)
#    loss by each process is adjusted using a loss adjustment ratio to account for
#    the losses by the other processes so that all processes are assumed to occur simultaneously
#    there is a critical minimum level of minimum N, below which, the mineral N cannot fall
#    The nitrate and ammonium pools are initialised at the minimum level, and the model run for 10 years
#    to establish the amount of nitrate or ammonium at the start of the forward run.
#    NO2 = nitrite; NO3 = nitrate; NH4 = ammonium; N2O = nitrous oxide; NO = nitric oxide
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_nitrogen_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os
from openpyxl import load_workbook
from math import exp, atan
from thornthwaite import thornthwaite

def get_n_parameters(n_parms):
    '''
    atmospheric deposition of N to the soil (eq.2.4.2)
    assume atmospheric deposition is composed of equal proportions of nitrate and ammonium-N
    This assumption may differ according to region
    '''
    atmos_n_depos = n_parms['atmos_n_depos']
    prop_atmos_dep_no3 = n_parms['prop_atmos_dep_no3']

    no3_atmos = prop_atmos_dep_no3 * atmos_n_depos/12  # (eq.2.4.2)
    nh4_atmos = (1 - prop_atmos_dep_no3) * atmos_n_depos/12  # (eq.2.4.19)
    k_nitrif = n_parms['k_nitrif']
    min_no3_nh4 = n_parms['no3_min']
    n_d50 = n_parms['n_d50']
    n_denit_max = n_parms['n_denit_max']
    
    return no3_atmos, nh4_atmos, k_nitrif, min_no3_nh4, n_d50, n_denit_max
    
def loss_adjustment_ratio(n_start, n_sum_inputs, n_sum_losses):
    '''
    for nitrate and ammonium (eq.2.4.1)
    '''
    if n_sum_losses <= n_start + n_sum_inputs:
        loss_adjust_ratio = 1
    else:
        loss_adjust_ratio = (n_start + n_sum_inputs)/n_sum_losses

    return loss_adjust_ratio

def _fertiliser_inputs(fert_amount):
    '''
    Urea fertiliser (the main form of fertiliser used in Africa and India, decomposes on application
    to the soil to produce ammonium, therefore, the proportion of nitrate added in the fertiliser is zero (eq.2.3.5)
    '''
    prop_no3_to_fert = 0
    fert_to_no3_pool = prop_no3_to_fert * fert_amount

    return fert_to_no3_pool

def _nitrified_ammonium(n_nh4):
    '''
    Nitrification is a process of nitrogen compound oxidation, i.e. the biological oxidation of ammonia to nitrite
    followed by the oxidation of the nitrite to nitrate (eq.2.3.6)
    '''
    n_no3 = n_nh4

    return n_no3

'''
     =====================================
                Losses of nitrate
     =====================================
'''
def no3_immobilisation(soil_n_supply, nh4_immob, min_no3_nh4):
    '''
    A negative soil N supply represents immobilised N. Immobilisation is assumed to occur first from the ammonium pool.
    '''
    no3_immob = min( - min(soil_n_supply - nh4_immob, 0), min_no3_nh4) #  (eq.2.4.5)

    return no3_immob

def no3_leaching(precip, wc_start, pet, wc_fld_cap, no3_start, no3_inputs, no3_min):
    '''
    Nitrate-N lost by leaching is calculated from the concentration of available nitrate in the soil at the start of
    the time step plus any inputs of nitrate after dilution with rainwater and the water drained from the soil
        precip_t1       rainfall during the time step (mm)
        water_start     amount of water (mm) in the soil at the start of the time step
        water_t0        the soil water at time t0 (mm)
        pet_t1          potential evapotranspiration during the time step (mm)
        wc_fld_cap      field capacity (mm)
    no3_start, no3_inputs, no3_min
    '''

    # volume of water drained (mm) during the time step
    # =================================================
    wat_drain = max((precip - pet) - (wc_fld_cap - wc_start), 0)  # (eq.2.4.7)

    no3_leach_tstep \
        = ((no3_start + no3_inputs - no3_min)/(wc_start + precip - pet))*wat_drain  # (eq.2.4.6)

    return  no3_leach_tstep, wat_drain

def no3_denitrific(imnth, t_depth, wat_soil, wc_pwp, wc_fld_cap, co2_aerobic_decomp, no3_avail, n_denit_max, n_d50):
    '''
    Denitrification is a microbially facilitated process where nitrate is reduced and ultimately produces molecular
    nitrogen through a series of intermediate gaseous nitrogen oxide products. The process is performed primarily by
    heterotrophic bacteria although autotrophic denitrifiers have also been identified
    based on the simple approach used in ECOSSE
    '''
    ndays_mnth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]       # TODO - leap year
    no3_d50 = n_d50 * t_depth     # soil nitrate-N content at which denitrification is 50% of its full potential (kg ha-1)
    n_denit_max = min(no3_avail, n_denit_max * t_depth * ndays_mnth[imnth - 1])    # (eq.2.4.9) maximum potential rate of denitrification (kg ha-1 month-1)

    rate_denit_no3 = no3_avail/(no3_d50 + no3_avail)    # (eq.2.4.10) nitrate rate modifier

    sigma_c = wat_soil   - wc_pwp       # calculated water content
    sigma_f = wc_fld_cap - wc_pwp       # field capacity maximum water content of the soil

    # Proportion of N2 produced by denitrification according to soil water and soil nitrate-N
    # =======================================================================================
    prop_n2_wat = 0.5*(sigma_c/sigma_f)                   # (eq.2.4.14)
    prop_n2_no3 = 1 - no3_avail/(40*t_depth + no3_avail)  # (eq.2.4.15)

    rate_denit_moist =  ((abs((sigma_c/sigma_f) - 0.62))/0.38)**1.74     # Grundmann and Rolston (1987)
    rate_denit_moist = min(1, rate_denit_moist)                     # (eq.2.4.11)

    # use the amount of CO2 produced by aerobic decomposition as a surrogate for biological activity
    # ==============================================================================================
    rate_denit_bio =  min(1, co2_aerobic_decomp * 0.1)    # (eq.2.4.12)

    n_denit = n_denit_max * rate_denit_no3 * rate_denit_moist * rate_denit_bio   # (eq.2.4.8)

    return n_denit, n_denit_max, rate_denit_no3, rate_denit_moist, rate_denit_bio, prop_n2_wat, prop_n2_no3

def no3_crop_uptake(prop_n_opt, n_respns_coef, nut_n_opt, t_grow, no3_avail, nh4_avail):
    '''
    crop N demand is calculated from the proportion of the optimum yield estimated assuming no other losses of mineral N
    0 <= prop_n_opt <= 1
    nut_n_opt  is N supply required for the optimum yield
    t_grow   is number of months in the growing season
    '''
    cn = n_respns_coef      # N response coefficient

    # prop. of the optimum yield achieved for given prop. of the optimum supply of N, prop_n_opt
    # ====================================================================================================
    prop_yld_opt = (1 + cn)*prop_n_opt**cn - cn*(prop_n_opt)**(1 + cn) # (eq.2.4.16)

    n_crop = prop_n_opt*nut_n_opt/t_grow    # (eq.2.4.17) N demand in each month
    no3_crop = n_crop*(no3_avail/(no3_avail + nh4_avail))  # (eq.2.4.18) crop N demand from the nitrate pool

    return n_crop, no3_crop, prop_yld_opt
