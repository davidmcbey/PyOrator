# -------------------------------------------------------------------------------
# Name:        ora_forward_run.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     13/04/2017
# Licence:     <your licence>
#
#   The simulation starts using default SOC pools and plant inputs
#    The SOC pools can have any value as the steady state simulation will adjust the pool sizes according to the measured SOC
#    The value of the total annual plant inputs will also be determined by the steady state simulation, but the
#    distribution of the plant inputs should follow the cropping patterns observed in the field#
#
#    The simulation is continued for 100 years, after which time, the C in the DPM, RPM, BIO, HUM and IOM pools are summed and
#    compared to the measured soil C. The soil C pools are then re-initialised with the values
#    calculated after 100 years and the plant inputs, CPI, are adjusted according to the ratio of measured and simulated total soil C
#
# -------------------------------------------------------------------------------
# !/usr/bin/env python

__prog__ = 'ora_forward_run.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from time import time
from ora_water_model import get_soil_water_constants
from ora_low_level_fns import get_rate_temp, inert_organic_carbon, carbon_lost_from_pool, get_soil_vars, \
                                                                init_ss_carbon_pools, get_values_for_tstep
from ora_nitrogen_model import soil_nitrogen
from ora_water_model import get_soil_water, SoilWater


# rate constant for decomposition of the pool
# ===========================================
K_DPM = 10/12;    K_RPM = 0.3/12;   K_BIO = 0.66/12;  K_HUM = 0.02/12  # per month

def cn_forward_run(parameters, weather, management, soil_vars, steady_state):
    '''

    '''
    pettmp = weather.pettmp_fwd
    t_depth, t_bulk, t_pH_h2o, tot_soc_meas, prop_hum, prop_bio, prop_co2 = get_soil_vars(soil_vars)

    # water content at initial and first time step
    # ============================================
    wc_t0 = 0; wc_t1 = 0; imnth =1
    wc_fld_cap, wc_pwp = get_soil_water_constants(soil_vars)

    ntsteps = management.ntsteps
    carbon_change, nitrogen_change, soil_water = steady_state
    pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, tot_soc_simul, \
                                    c_input_bio, c_input_hum, c_loss_dpm, c_loss_rpm, c_loss_hum, c_loss_bio \
                                                                                = carbon_change.get_last_tstep_pools()
    for tstep in range(ntsteps):
        tair, precip, pet, irrig, c_pi_mnth, c_n_rat_ow, rat_dpm_rpm, cow, rat_dpm_hum_ow, prop_iom_ow, \
                                    max_root_dpth = get_values_for_tstep(pettmp, management, parameters, tstep)

        wat_soil, wc_t0, wc_t1 = get_soil_water(tstep, precip, pet, irrig, wc_fld_cap, wc_pwp, wc_t0, wc_t1)

        rate_mod, rate_moist = get_rate_temp(tair, t_pH_h2o, wc_fld_cap, wc_pwp, wat_soil)

        # plant inputs and losses (t ha-1) passed to the DPM pool
        # =======================================================
        pi_to_dpm = c_pi_mnth * rat_dpm_rpm/(1.0 + rat_dpm_rpm)  # (eq.2.1.10)
        cow_to_dpm = cow * rat_dpm_hum_ow * (1.0 - prop_iom_ow) / (1 + rat_dpm_hum_ow)  # (eq.2.1.12)
        pool_c_dpm += pi_to_dpm + cow_to_dpm - c_loss_dpm
        pool_c_dpm = max(0, pool_c_dpm)

        # RPM pool
        # ========
        pi_to_rpm = c_pi_mnth * 1.0 / (1.0 + rat_dpm_rpm)  # (eq.2.1.11)
        pool_c_rpm += pi_to_rpm - c_loss_rpm

        # BIO pool
        # ========
        pool_c_bio += c_input_bio - c_loss_bio

        # HUM pool
        # ========
        cow_to_hum = cow * (1 - prop_iom_ow) / (1 + rat_dpm_hum_ow)  # (eq.2.1.13)
        pool_c_hum += cow_to_hum + c_input_hum - c_loss_hum

        # IOM pool
        # ========
        ioc_to_iom = inert_organic_carbon(prop_iom_ow, cow)  # add any IOM from organic waste added to the soil
        pool_c_iom += ioc_to_iom

        # carbon losses
        # =============
        c_loss_dpm = carbon_lost_from_pool(pool_c_dpm, K_DPM, rate_mod)
        c_loss_rpm = carbon_lost_from_pool(pool_c_rpm, K_RPM, rate_mod)
        c_loss_bio = carbon_lost_from_pool(pool_c_bio, K_BIO, rate_mod)
        c_loss_hum = carbon_lost_from_pool(pool_c_hum, K_HUM, rate_mod)
        c_loss_total = c_loss_dpm + c_loss_rpm + c_loss_hum + c_loss_bio

        c_input_bio = prop_bio * c_loss_total
        c_input_hum = prop_hum * c_loss_total
        co2_release = prop_co2 * c_loss_total

        carbon_change.append_vars(imnth, rate_mod, c_pi_mnth, cow, c_n_rat_ow,
                                  pool_c_dpm, pi_to_dpm, cow_to_dpm, c_loss_dpm,
                                  pool_c_rpm, pi_to_rpm, c_loss_rpm,
                                  pool_c_bio, c_input_bio, c_loss_bio,
                                  pool_c_hum, cow_to_hum, c_input_hum, c_loss_hum,
                                  pool_c_iom, ioc_to_iom, tot_soc_simul, co2_release)

        soil_water.append_vars(t_depth, max_root_dpth, precip, pet, irrig, wc_pwp, wat_soil, wc_fld_cap)

    nitrogen_change = soil_nitrogen(carbon_change, soil_water, parameters, pettmp, management, soil_vars)

    return (carbon_change, nitrogen_change, soil_water)
