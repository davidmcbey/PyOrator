#-------------------------------------------------------------------------------
# Name:        ora_nutriment_supply.py
# Purpose:     functions for ora nutriment supply
# Author:      Dave Mcbey
# Created:     03/08/2020
# Licence:     <your licence>
# defs:
#   test_livestock_algorithms
#
# Description:
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_nutriment_supply.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os

def c_n_ratios(dpm_prev, rpm_prev, hum_prev, c_n_rat_dpm_prev, c_n_rat_pi, cow_to_dpm, c_n_rat_ow, pi_to_dpm):
    '''
    stub

    dpm_inpt = pi_to_dpm + cow_to_dpm
    denom = (dpm_prev / c_n_rat_dpm_prev) + (dpm_inpt / c_n_rat_pi) + (cow_to_dpm / c_n_rat_ow)
    c_n_rat_dpm = (dpm_prev + dpm_inpt) / denom  # (eq.3.3.10)
    c_n_rat_rpm = (rpm_prev + pi_to_rpm) / ((rpm_prev / c_n_rat_rpm_prev) + (pi_to_rpm / c_n_rat_pi))  # (eq.3.3.11)
    c_n_rat_hum = (hum_prev + cow_to_hum) / ((hum_prev / c_n_rat_hum_prev) + (cow_to_hum / c_n_rat_ow))  # (eq.3.3.12)

    return c_n_rat_dpm, c_n_rat_rpm,  c_n_rat_hum
    '''
    return
