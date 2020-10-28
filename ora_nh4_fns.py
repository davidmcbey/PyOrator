#-------------------------------------------------------------------------------
# Name:        ora_nh4_fns.py
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
# Functions:
#    Inputs of ammonium:
#       _nh4_atmos_deposition
#       _nh4_fert_inputs
#       _nh4_mineralisation
#
#    Losses of ammonium
#       nh4_immobilisation
#       nh4_volatilisation
#       _nh4_nitrification
#       nh4_crop_uptake
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_nh4_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os
from openpyxl import load_workbook
from math import exp, atan
from thornthwaite import thornthwaite

def _nh4_atmos_deposition(n_atmos_depos, proportion = 0.5):
    '''
    atmospheric deposition of N to the soil (24)
    assume atmospheric deposition is composed of equal proportions of nitrate and ammonium-N
    This assumption may differ according to region.
    '''
    n_to_soil = n_atmos_depos*proportion

    return n_to_soil

def _nh4_fert_inputs(fert_amount):
    '''
    Urea fertiliser (the main form of fertiliser used in Africa and India, decomposes on application
    to the soil to produce ammonium, therefore, the proportion of nitrate added in the fertiliser is zero (25)
    '''
    prop_no3_to_fert = 0
    fert_to_no3_pool = prop_no3_to_fert * fert_amount

    return fert_to_no3_pool

def nh4_mineralisation(soil_n_supply):
    '''
    Mineralisation - Mineralisation of organic N is assumed to release N in the form of ammonium.
    Therefore, a positive net soil N supply, Nsoil (kg ha-1) (see section 3.3), is equivalent to the input
    of ammonium-N due to mineralisation, Nnh4,miner (kg ha-1),
    '''
    nh4_miner = max(soil_n_supply, 0)  # eq.2.4.21

    return nh4_miner

'''
     =====================================
                Losses of nitrate
     =====================================
'''
def nh4_immobilisation(n_soil_supply, nh4_min):
    '''
    Immobilisation – A negative soil N supply represents immobilised N and is assumed
    to occur first from the ammonium pool before drawing on nitrate.
    n_soil_supply:  soil N supply
    nh4_min:        minimum possible amount of ammonium-N,
    '''
    nh4_immob = min( - min(n_soil_supply, 0), nh4_min)    # (eq.2.4.22)

    return nh4_immob

def nh4_nitrification(nh4, nh4_min, rate_mod, k_nitrif):
    '''
    nitrified ammonium is assumed to occur by a first order reaction, using the same environmental
    rate modifiers as in soil organic matter decomposition
    k_nitrif - rate constant for nitrification, per month
    '''
    rate_inhibit = 1     # inhibition rate modifier TODO - see manual

    tmp_var = nh4 * (1 - exp(-k_nitrif*rate_mod*rate_inhibit))

    nh4_nitrif = min(tmp_var, nh4_min)  # (eq.2.4.23)

    return nh4_nitrif

def nh4_volatilisation(precip, nh4_manure, nh4_fert):
    '''
    Ammonia volatilisation: a chemical process that occurs at the soil surface when ammonium from urea or
    ammonium-containing fertilisers (e.g. urea) is converted to ammonia gas at high pH. Losses are minimal when
    fertiliser is incorporated, but can be high when fertiliser is surface-applied.

    a fixed proportion of the ammonium-N or urea-N in applied manure and fertilisers is assumed to be lost in the
    month of application only if the rainfall in that month is less than a critical level (< 21 mm)
    '''
    prop_volat = 0.15              # proportion of ammonium-N or urea-N that can be volatilised
    precip_critic = 21          # critical level of rainfall below which losses due to volatilisation take place
    if precip < precip_critic:
        nh4_volatil = prop_volat*(nh4_manure + nh4_fert)   # (eq.2.4.25)
    else:
        nh4_volatil = 0.0

    return  nh4_volatil

def nh4_crop_uptake(n_crop, no3_avail, nh4_avail):
    '''
    as for nitrate, it is assumed that the crop N demand from the ammonium pool is shared equally between
    available nitrate and ammonium
    n_crop: N demand of the crop in each month
    '''
    nh4_crop = n_crop * (nh4_avail/(no3_avail + nh4_avail))  # (eq.2.4.26)

    return nh4_crop


