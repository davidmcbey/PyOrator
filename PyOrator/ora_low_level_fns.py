#-------------------------------------------------------------------------------
# Name:        ora_low_level_fns.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     26/12/2019
# Licence:     <your licence>
# Definitions:
#   spin_up
#
# Description:#
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_low_level_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import sys
from time import time
from math import exp, atan,ceil
from thornthwaite import thornthwaite

MNTH_NAMES_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
KEYS = ['Intiation', 'Plant inputs', 'DPM carbon', 'RPM carbon', 'BIO carbon', 'HUM carbon', 'IOM carbon', 'TOTAL SOC']

def _dump_summary(sum_tbl):

    wdth25 = 25
    wdth14 = 14
    line = KEYS[0].center(wdth25)
    for key in KEYS[1:]:
        line += key.rjust(wdth14)
    print(line)

    for iline in range(2):
        line = sum_tbl[KEYS[0]][iline].rjust(wdth25)
        for key in KEYS[1:]:
            line += '{:14.3f}'.format(sum_tbl[key][iline])
        print(line)

def summary_table_add(pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, pi_tonnes,
                      summary_table = None):
    '''
    create or add to summary table
    =============================
    '''
    totsoc = sum([pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom])
    pi_tonnes_sum = sum(pi_tonnes)
    data_list = list([pi_tonnes_sum, pool_c_dpm, pool_c_rpm,pool_c_bio,pool_c_hum,pool_c_iom, totsoc])

    if summary_table is None:
        val_list = ['Starting conditions'] + data_list
        summary_table = {}
        for key, val in zip(KEYS, val_list):
            summary_table[key] = [val]

        return summary_table
    else:
        val_list = ['Ending conditions'] + data_list
        for key, val in zip(KEYS, val_list):
            summary_table[key].append(val)

        _dump_summary(summary_table)

def populate_org_fert(org_fert):
    '''
    TODO: clumsy attempt to ensure org_fert is populated as required for calculation of C and N pools
    '''

    indx_frst = 0
    frst_applic_filler = None
    applic_filler = None
    for indx, val in enumerate(org_fert):
        if val is not None:
            ow_type = val['ow_type']
            amount = 0
            applic_filler = {'ow_type': ow_type, 'amount': 0}

            # save first ow type
            # ==================
            if frst_applic_filler is None:
                indx_frst = indx
                frst_applic_filler = applic_filler
        else:
            org_fert[indx] = applic_filler

    org_fert[:indx_frst] = indx_frst * [frst_applic_filler]

    return org_fert

def get_soil_vars(soil_vars):
    '''

    '''
    t_bulk = soil_vars.t_bulk
    t_clay = soil_vars.t_clay
    t_depth = soil_vars.t_depth
    t_pH_h2o = soil_vars.t_pH_h2o
    tot_soc_meas = soil_vars.tot_soc_meas

    # C lost from each pool due to aerobic decomposition is partitioned into HUM, BIO and CO2
    # =======================================================================================
    denom = 1 + 1.67 * (1.85 + 1.6 * exp(-0.0786 * t_clay))
    prop_hum = (1 / denom) / (1 + 0.85)     # (eq.2.1.7)
    prop_bio = (1 / denom) - prop_hum       # (eq.2.1.8)
    prop_co2 = 1 - prop_bio - prop_hum      # (eq.2.1.9)

    return t_depth, t_bulk, t_pH_h2o, tot_soc_meas, prop_hum, prop_bio, prop_co2

def init_ss_carbon_pools(tot_soc_meas):
    '''
    initialise carbon pools in tonnes
    use Falloon equation for amount of C in the IOM pool (eq.2.1.15)
    '''

    # initialise carbon pools
    # =======================
    pool_c_iom = 0.049 * (tot_soc_meas ** 1.139)    # Falloon
    pool_c_dpm = 1
    pool_c_rpm = 1
    pool_c_bio = 1
    pool_c_hum = 1
    tot_soc_simul = pool_c_dpm + pool_c_rpm + pool_c_bio + pool_c_hum + pool_c_iom

    return pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, tot_soc_simul

def get_values_for_tstep(pettmp, management, parameters, tstep):

    tair = pettmp['tair'][tstep];
    precip = pettmp['precip'][tstep];
    pet = pettmp['pet'][tstep]

    irrig = management.irrig[tstep]
    c_pi_mnth = management.pi_tonnes[tstep]
    crop_name = management.crop_currs[tstep]
    rat_dpm_rpm = parameters.crop_vars[crop_name]['rat_dpm_rpm']
    max_root_dpth = parameters.crop_vars[crop_name]['max_root_dpth']

    org_fert = management.org_fert[tstep]
    ow_type = org_fert['ow_type']

    ow_parms = parameters.ow_parms
    c_n_rat_ow = ow_parms[ow_type]['c_n_rat']
    prop_iom_ow = ow_parms[ow_type]['prop_iom_ow']       # proportion of inert organic matter in added organic waste
    rat_dpm_hum_ow = ow_parms[ow_type]['rat_dpm_hum_ow'] # ratio of DPM:HUM in the active organic waste added
    cow = org_fert['amount']*ow_parms[ow_type]['pcnt_c']     # proportion of plant input is carbon (t ha-1)

    return tair, precip, pet, irrig, c_pi_mnth, c_n_rat_ow, rat_dpm_rpm, cow, rat_dpm_hum_ow, prop_iom_ow, max_root_dpth

def compare_pools(pool_prev, pool_current):
    '''
    compare previous and current pools
    NB not used
    '''
    for pool in pool_current:
        for imnth in range(12):
            if pool_prev[pool][imnth] - pool_current[pool][imnth] > 0.001:
                break
    return

def get_rate_temp(air_temp, pH, wc_fld_cap, wc_pwp, wc_tstep):
    '''
    wc_tstep: water content in this timestep
    '''
    rate_temp = 47.91/(1.0 + exp(106.06/(air_temp + 18.27)))    # (eq.2.1.3)

    rate_moisture = min(1.0, 1.0 - (0.8 * (wc_fld_cap - wc_tstep))/(wc_fld_cap - wc_pwp))   # (eq.2.1.4)

    rate_ph = 0.56+(atan(3.14*0.45*(pH - 5.0)))/3.14    # (eq.2.1.5)

    salinity = 0.01
    rate_salinity = exp(-0.09 * salinity)    # (eq.2.1.6)

    # rmod is the product of rate modifiers that account for changes
    # in temperature, soil moisture, acidity and salinity
    # ===================================================
    rate_mod = rate_temp*rate_moisture*rate_ph*rate_salinity

    return rate_mod, rate_moisture

def carbon_lost_from_pool(c_in_pool, k_rate_constant, rate_mod):

    c_loss = c_in_pool*(1.0 - exp(-k_rate_constant*rate_mod))    # (eq.2.1.2)

    return c_loss

def plant_inputs_crops_distribution(c_pi_yr, t_sow, t_harv, annual_flag = True):
    '''
    plant inputs for annual crops are distributed over the growing season between sowing and harvest using
    the equation for C inputs provided by Bradbury et al. (1993);
    '''
    k_pi_c = 0.6    # constant describing the shape of the exponential curve for C input

    if annual_flag:
        # annual crops - (14)
        # ==================
        c_pi_mnths = [0]*12     # initiate

        for t_mnth in range(t_sow, t_harv + 1):
            numer = exp(-k_pi_c*(t_harv - t_mnth))      # (eq.2.1.14)
            denom = 0
            for imnth in range(t_sow, t_harv + 1):
                denom += numer

            c_pi_mnths[t_mnth - 1] = c_pi_yr*(numer/denom)
    else:
        # perennial crops
        # ===============
        c_pi_mnth = c_pi_yr/12
        c_pi_mnths = [c_pi_mnth]*12

    return c_pi_mnths

def inert_organic_carbon(prop_iom_in_ow, c_ow ):
    '''
    calculates the amount of organic waste passed to the IOM pool in this time-step (t ha-1)

    carbon in the IOM is assumed to be inert, and does not change unless organic waste containing IOM is added to the
    soil
    '''
    c_ow_to_iom = prop_iom_in_ow*c_ow   # (eq.2.1.16)

    return c_ow_to_iom

def average_weather(latitude, precip, tair):
    '''
    return average weather
    '''
    func_name =  __prog__ + '\taverage_weather'

    indx_start = 0
    indx_end   = len(precip)

    # use dict-comprehension to initialise precip. and tair dictionaries
    # =========================================================================
    hist_precip = {mnth: 0.0 for mnth in MNTH_NAMES_SHORT}
    hist_tmean  = {mnth: 0.0 for mnth in MNTH_NAMES_SHORT}

    for indx in range(indx_start, indx_end, 12):

        for imnth, month in enumerate(MNTH_NAMES_SHORT):
            hist_precip[month] += precip[indx + imnth]
            hist_tmean[month]  += tair[indx + imnth]

    # write stanza for input.txt file consisting of long term average climate
    # =======================================================================
    ave_precip = []
    ave_tmean = []
    num_years = len(precip)/12
    for month in MNTH_NAMES_SHORT:
        ave_precip.append(hist_precip[month]/num_years)
        ave_tmean.append(hist_tmean[month]/num_years)

    year = 2001 # not a leap year
    pet = thornthwaite(ave_tmean, latitude, year)

    return  ave_precip, ave_tmean, pet

def miami_dyce(land_cover_type, tair, precip):
    '''
    tair     mean annual temperature
    precip   mean total annual precipitation

    modification of the miami model by altering coefficients (no need to reparameterise exponent terms since model
    is effectively linear in climate range of the UK)

    multiply npp values according to land cover type:

    forest (3): 7/8
    semi-natural (4), grassland (2), arable (1): forest/2
    Miscanthus (5): multiply by 1.6 (from comparison of unadjusted Miami results with Miscanfor peak yield results)
    SRC (6): as forest  - peak yield is just over half that of Miscanthus)

    for plant inputs to soil, multiply npp values by different fractions according to land cover - sum of net biome productivities divided by npp
    forest: 0.15
    semi-natural, grassland: 0.08
    arable: 0.02
    Miscanthus: 0.3 (widely reported as losing around 1/3 of peak mass before harvest; small amount returns to rhizome)
    SRC: 0.15 (assumed as forest)
    '''

    # arable, grassland, forest, semi-natural, miscanthus, SRC
    resc = {'ara': 0.44, 'gra': 0.44, 'for':0.8, 'nat': 0.44, 'mis': 1.6, 'src': 0.88}
    frac = {'ara': 0.53, 'gra': 0.71, 'for':0.8, 'nat': 0.8,  'mis': 0.3, 'src': 0.23}

    nppt = 3000/(1 + exp(1.315 - 0.119*tair))    # temperature-limited npp
    nppp = 3000*(1 - exp(-0.000664*precip))      # precipitation-limited npp
    npp = 0.5*10*resc[land_cover_type]*min(nppt, nppp)   # Times 10 for unit conversion (g/m^2 to Kg/ha) and .5 for C
    soil_input = frac[land_cover_type]*npp                  # soil input of vegetation

    return soil_input

def update_progress(last_time, iteration, tot_soc_meas, tot_soc_simul,
                                    pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom):

    """Update progress bar."""
    new_time = time()
    if new_time - last_time > 5:
        # used to be: Estimated remaining
        mess = '\rIterations completed: {:=6d} SOC meas: {:=8.3f} simul: {:=8.3f}'\
                                                        .format(iteration, tot_soc_meas, tot_soc_simul)

        mess += ' pools dpm: {:=8.3f} rpm: {:=8.3f} bio: {:=8.3f} hum: {:=8.3f} iom: {:=8.3f}'\
                                    .format(pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom)
        sys.stdout.flush()
        sys.stdout.write(mess)
        last_time = new_time

    return last_time


