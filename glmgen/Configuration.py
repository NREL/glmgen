'''
Created on Apr 2, 2013
Author: D3P988

Updated on May 6, 2015
Author = Elaine Hale
'''
import re

def append_default_feeder_config_data(data, working_directory, resources_dir, dir):
  data["directory"] = dir
  data["fix_random_seed"] = True
  data["regions"] = { 1: 'Temperate, West Cost (San Francisco)',
                      2: 'North Central/Northeast, Cold (Chicago)',
                      3: 'Southwest, Hot/Arid (Phoenix)',
                      4: 'Southeast Central, Hot/Cold (Nashville)',
                      5: 'Southeast Coastal, Hot/Humid (Miami)',
                      6: 'Hawaii, Sub-Tropical (Honolulu)',
                      7: 'Other -- defaults not provided' }
  data["weather"] = '{:s}/SCADA_weather_NC_gld_shifted.csv'.format(resources_dir)
  data["timezone"] = 'PST+8PDT'
  data["region"] = 1
  # Feeder Properties
  # - Substation Rating in MVA (Additional 15% gives rated kW & pf = 0.87)
  # - Nominal Voltage of Feeder Trunk
  # - Secondary (Load Side) of Transformers
  # - Voltage Players Read Into Swing Node
  data["feeder_rating"] = 1.15*14.0
  data["nom_volt"] = 14400
  data["nom_volt2"] = 14400 #was set to 480 for taxonomy feeders
  #data["load_shape_norm"] = dir + "FRIENDSHIP_2012_normalized_loadshape.player"
  data["load_shape_norm"] = dir + 'load_shape_player.player'
  vA='{:s}/VA.player'.format(resources_dir)
  vB='{:s}/VB.player'.format(resources_dir)
  vC='{:s}/VC.player'.format(resources_dir)
  data["voltage_players"] = ['"{:s}"'.format(vA),'"{:s}"'.format(vB),'"{:s}"'.format(vC)]
  data['standard_transformer_ratings'] = [10,15,25,37.5,50,75,100,150,167,250,333.3,500,666.7] # kW
  data['tranformer_oversize_factor'] = 1.5
     
  # Voltage Regulation
  # - EOL Measurements (name of node, phases to measure (i.e. ['GC-12-47-1_node_7','ABC',1]))
  # - Voltage Regulationn ( [desired, min, max, high deadband, low deadband] )
  # - Regulators (list of names)
  # - Capacitor Outages ( [name of capacitor, outage player file])
  # - Peak Power of Feeder in kVA 
  data["EOL_points"] = []
  data["voltage_regulation"] = [14400, 12420, 15180, 60, 60]     
  data["regulators"] = []
  data["capacitor_outtage"] = []
  data["emissions_peak"] = 13910 # Peak in kVa base .85 pf of 29 (For emissions)
      
  # Time of Use (TOU)
  data["TOU_prices"] = [0.07590551, 0.15181102]
  data["TOU_hours"] = [12, 12, 6]
  data["TOU_stats"] = [0.11385826, 0.03795329]
  data["TOU_price_player"] = 'R1_1247_1_t0_TOU.player'
      
  # Critical Peak Price (CPP) 
  data["CPP_prices"] = [0.06998667, 0.13997334, 0.69986670]
  data["CPP_stats"] = [0.10999954, 0.03795329]
  data["CPP_price_player"] = 'R1_1247_1_t0_CPP.player'
  data["CPP_flag"] = 'CPP_days_R1.player' # Specifies critical day
      
  # Load Classifications
  data["load_classifications"] = ['Residential1', 'Residential2', 'Residential3', 'Residential4', 'Residential5', 'Residential6', 'Commercial1', 'Commercial2', 'Commercial3']    
  # Columns correspond to 'standard_transformer_ratings'.
  #                                [ 10,  15,  25,37.5,  50,  75, 100,150,167,250,333.3, 500,666.7]
  data['comm_load_class_dists'] = [[100, 100, 100, 100, 100, 100, 100, 15, 11,  0,    0,   0,    0], # Strip Mall - 6
                                   [  0,   0,   0,   0,   0,   0,   0, 85, 27, 22,   17,   0,    0], # Big Box - 7
                                   [  0,   0,   0,   0,   0,   0,   0,  0, 62, 78,   83, 100,  100]] # Office - 8
  data['res_load_class_dists'] =  [[ 18,  43,  22,   0,  14,  10,   8,  2, 16, 16,   16,  16,   16], # Res 1 - Older SFH < 2000 ft2
                                   [ 76,  14,  61,   0,  48,   8,   4,  1, 16, 16,   16,  16,   16], # Res 2 - Newer SFH < 2000 ft2
                                   [  0,   0,   2, 100,   3,   8,  30,  1, 16, 16,   16,  16,   16], # Res 3 - Older SFH > 2000 ft2
                                   [  0,   0,   2,   0,  21,  43,  26,  9, 16, 16,   16,  16,   16], # Res 4 - Newer SFH > 2000 ft2
                                   [  0,  10,   3,   0,   3,   8,   8, 20, 18, 18,   18,  18,   18], # Res 5 - Mobile Homes
                                   [  6,  33,  10,   0,  11,  23,  24, 67, 18, 18,   18,  18,   18]] # Res 6 - Apartments (seem sized for 1 apt., but shouldn't it be whole building?)

  # Industrial Loads
  # - For each classification, flag if you want loads populated using normalized load shape
  #   from player files rather than with houses. You may include a
  #   maximum value such that loads less than that size are populated with
  #   houses, and loads greater are populated with loadshape from player. 
  # - Note that the option exists to print any classification as constant power scaled by players.. the term "industrial" is used loosely.
  data["indust_class"] = [[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]]  #[(0 or 1), kW]
  data["loadshape_r"]='' # player file
  data["loadshape_i"]='' # player file
  data["loadshape"]=0+0j
  data["indust_scalar_com_r"]=0
  data["indust_scalar_com_i"]=0
  data["indust_scalar_com"]=0+0j    
  
  # Additional Solar Modules
  # - penetration (%)
  # - solar rating (kVA)
  # - inverter power factor (fraction)
  data["solar_penetration"] = 0.0
  data["solar_rating"] = 5  
  data["inverter_power_factor"] = 1.0
  
  # Existing Solar (modules in utility database)
  # - inverter object properties to be used
  # - solar module object properties to be used
  # if entry is blank (i.e. ''), default property value will be used in in the .glm:
  data['sol_inv_properties'] = \
      ['', #1    # inverter_type (TWO_PULSE|SIX_PULSE|TWELVE_PULSE|PWM|FOUR_QUADRANT)
       '', #2    # generator_status (ONLINE|OFFLINE)
       '', #3    # generator_mode (UNKNOWN|CONSTANT_V|CONSTANT_PQ|CONSTANT_PF|SUPPLY_DRIVEN), 
                 # -- default is CONSTANT_PF, and this property is irrelevent if 
                 # inverter type is four quadrant:
       '', #4    # V_In [V]
       '', #5    # I_In [A]
       '', #6    # four_quadrant_control_mode (NONE|CONSTANT_PQ|CONSTANT_PF)
                 # -- this property is necessary only if inverter type is four quadrant:
       '', #7    # P_Out [VA]  -- used for constant PQ mode
       '', #8    # Q_Out [VAr] -- used for constant PQ mode
       '', #9    # power_factor [pu] (used for constant pf mode)
       '', #10   # rated_power [W]
       '', #11   # use_multipoint_efficiency (TRUE|FALSE)
       '', #12   # inverter_manufacturer (NONE|FRONIUS|SMA|XANTREX)
                 #-- only used if multipoint efficiency:
       '', #13   # maximum_dc_power [W] -- used if multipoint efficiency:
       '', #14   # maximum_dc_voltage [V] -- used if multipoint effici ency:
       '', #15   # minimum_dc_power [W] -- used if multipoint efficiency:
       '', #16   # c_0 -- coefficient descibing the parabolic relationship between AC and DC power of the inverter
                 #-- only used if multipoint efficiency:
       '', #17   # c_1 -- coefficient allowing the maximum DC power to vary linearly with DC voltage
                 #-- only used if multipoint efficiency:
       '', #18   # c_2 -- coefficient allowing the minimum DC power to vary linearly with DC voltage
                 #-- only used if multipoint efficiency:
        ''] #19  # c_3 -- coefficient allowing c_0 to vary linearly with DC voltage
                 #-- only used if multipoint efficiency:

  # properties of solar modules
  data['sol_module_properties'] = \
      ['',             #1  # generator_mode (SUPPLY_DRIVEN)
       '',             #2  # generator_status (ONLINE|OFFLINE)
       'MULTI_CRYSTAL_SILICON',   #3  # panel_type (SINGLE_CRYSTAL_SILICON|MULTI_CRYSTAL_SILICON|AMORPHOUS_SILICON|THIN_FILM_GA_AS|CONCENTRATOR)
       '',             #4  # NOCT [degF] --default is 118.4 degF, used to calculate Tmodule
       '',             #5  # Tmodule [degF] -- used to calculate Voc and VA_Out  
       '',             #6  # power_factor [pu] (used for constant pf mode)
       '',             #7  # Rated_Insolation [W/sf] -- default is 92.902
       '',             #8  # Pmax_temp_coeff -- used to calculate VA_Out, set by panel type selection if not set here:
       '',             #9  # Voc_temp_coeff -- used to calculate Voc, set by panel type selection if not set here:
       '',             #10 # V_Max [V] -- default is 27.1 + 0j, used to calculate V_Out
       '',             #11 # Voc_Max [V] -- default is 34 + 0j, used to calculate Voc and V_Out
       '',             #12 # efficiency [unit] -- set by panel type selection if not set here:
       '',             #13 # area [sf] -- default is 323 #TODO: should they be allowed to change this since it's figured out according to load size?
       '',             #14 # shading_factor -- default is 1 (no shading)
       '20',           #15 # tilt_angle -- default is 45 degrees
       '',             #16 # orientation_azimuth -- default is 0 (equator facing)
       '',             #17 # latitude_angle_fix (TRUE|FALSE) -- default is false (this fixes tilt angle to regions latitude as determined by the included climate info
       'FIXED_AXIS']   #18 # orientation  (FIXED|DEFAULT) -- default is DEFAULT, which means tracking

  # what percentage breakdown of these configurations? (inverter with sol_inv_properties{n} will be parent to solar object with solar_module_properties{n})
  data["solar_inverter_config_breakdown"] = [1, #Res1
                                             1, #Res2
                                             1, #Res3
                                             1, #Res4
                                             1, #Res5
                                             1, #Res6
                                             1, #Com1
                                             1, #Com2
                                             1] #Com3
                                               
  # Commercial Buildings
  # - Designate what type of commercial building each classification represents.
  data["com_buildings"] = [[0, 0, 0, 0, 0, 0, 0, 0, 1],  # office buildings 
                           [0, 0, 0, 0, 0, 0, 0, 1, 0],  # big box 
                           [0, 0, 0, 0, 0, 0, 1, 0, 0]]  # strip mall
  data["no_cool_sch"] = 8
  data["no_heat_sch"] = 6
  data["no_water_sch"] = 6
  data["ts_penetration"] = 10 #0-100, percent of buildings utilizing thermal storage - for all regions
  
  # Determines how many houses to populate (bigger avg_house = less houses)
  data["avg_house"] = 15000 # W
  
  # Determines sizing of commercial loads (bigger avg_commercial = less houses)
  data["avg_commercial"] = 35000 # W
  
  # Scale the responsive and unresponsive loads (percentage)
  data["base_load_scalar"] = 1.0
  
  #variable to shift the residential schedule skew (seconds)
  data["residential_skew_shift"] = 0
  
  # widen schedule skew
  data["residential_skew_std"] = 2700
  
  # window wall ratio
  data["window_wall_ratio"] = 0.15
  
  # additional set point degrees
  data["addtl_heat_degrees"] = 0
  
  # normalized load shape scalar
  data["normalized_loadshape_scalar"] = 1
  
  if 'load_shape_norm' in data.keys() and data['load_shape_norm'] is not None:
    # commercial zip fractions for loadshapes
    data["c_z_pf"] = 0.97
    data["c_i_pf"] = 0.97
    data["c_p_pf"] = 0.97
    data["c_zfrac"] = 0.2
    data["c_ifrac"] = 0.4
    data["c_pfrac"] = 1 - data["c_zfrac"] - data["c_ifrac"]
    
    # residential zip fractions for loadshapes
    data["r_z_pf"] = 0.97
    data["r_i_pf"] = 0.97
    data["r_p_pf"] = 0.97
    #data["r_zfrac"] = 0.2
    #data["r_ifrac"] = 0.4
    data["r_zfrac"] = 0.0
    data["r_ifrac"] = 0.0
    data["r_pfrac"] = 1 - data["r_zfrac"] - data["r_ifrac"]  
  
  return data

def FeederConfiguration(wdir, resources_dir, config_data = None):
  data = {}; update = False  
  if config_data is not None:
    data = config_data; update = True
   
  working_directory = re.sub('\\\\','\\\\\\\\',wdir)
  dir = working_directory+'\\\\schedules\\\\'
  if not update:
    data = append_default_feeder_config_data(data, working_directory, resources_dir, dir)
  
  if update:
    region = data['region']
    default_weather_by_region = { 1:  ['CA-San_francisco.tmy2',   'PST+8PDT'],
                                  2:  ['IL-Chicago.tmy2',     'CST+6CDT'],
                                  3:  ['AZ-Phoenix.tmy2',     'MST+7MDT'],
                                  4:  ['TN-Nashville.tmy2',     'CST+6CDT'],
                                  5:  ['FL-Miami.tmy2',       'EST+5EDT'],
                                  6:  ['HI-Honolulu.tmy2',     'HST10'] }
    # keyed on region number,  the index position in the lists then represent load classifications, 
    # see data["load_classifications"], and Commercial1 = Strip Mall, Commercial2 = Big Box and 
    # Commercial 3 = Office
    # Third quartile of individual house power in W/ft^2.
    default_peak_power_intensity_by_region_and_load_class = { \
        #   Res1   Res2   Res3   Res4   Res5    Res6    StripM BigB   Office
        1: [7.023, 5.863, 5.156, 4.135, 12.151, 12.905, 6.028, 6.224, 6.050],
        2: [8.199, 6.279, 6.208, 4.570, 11.008, 12.398, 6.088, 6.362, 6.379],
        3: [8.472, 6.313, 6.373, 4.578, 13.304, 13.542, 7.444, 7.583, 7.491],
        4: [9.315, 6.431, 7.072, 4.930, 17.554, 16.810, 6.419, 6.665, 6.722],
        5: [6.967, 5.491, 5.387, 4.088, 11.450, 11.463, 5.881, 6.160, 6.298], 
        6: [6.664, 5.438, 5.084, 4.011,  8.653,  9.940, 5.624, 5.927, 6.078]
    }
    # As above, but median annual load intensity in kWh/ft^2.
    default_annual_load_intensity_by_region_an_load_class = { \
        #   Res1    Res2   Res3   Res4   Res5    Res6    StripM  BigB   Office
        1: [ 9.329, 9.312, 7.261, 7.295, 13.100, 15.209, 15.542, 19.984, 18.350],
        2: [ 9.572, 9.137, 7.746, 7.440, 12.284, 14.506, 16.532, 20.829, 18.944],
        3: [10.845, 9.546, 8.528, 7.702, 14.728, 15.691, 20.436, 25.262, 23.106],
        4: [ 9.818, 8.446, 7.992, 6.792, 14.087, 13.771, 17.723, 22.304, 20.440],
        5: [10.736, 9.388, 8.669, 7.485, 13.693, 14.593, 20.559, 25.902, 23.693],
        6: [10.549, 9.367, 8.393, 7.482, 13.027, 14.636, 20.430, 25.803, 23.588]
    }
    default_pv_capacity_factors_by_region = { \
        1: 0.1731,
        2: 0.1404,
        3: 0.2058,
        4: 0.1579,
        5: 0.1711,
        6: 0.1883
    }
    if region in default_weather_by_region:
        if 'weather' not in data or not data["weather"]:
            data["weather"] = '{:s}/'.format(resources_dir) + default_weather_by_region[region][0]
        if 'timezone' not in data.keys() or not data['timezone']:    
            data["timezone"] = default_weather_by_region[region][1]
        if 'peak_load_intensities' not in data or not data['peak_load_intensities']:
            data['peak_load_intensities'] = default_peak_power_intensity_by_region_and_load_class[region]
        if 'annual_load_intensities' not in data or not data['annual_load_intensities']:
            data['annual_load_intensities'] = default_annual_load_intensity_by_region_an_load_class[region]
        if 'pv_cf' not in data or not data['pv_cf']:
            data['pv_cf'] = default_pv_capacity_factors_by_region[region]
            
    n_trans = len(data['standard_transformer_ratings'])
    for percentages in data['comm_load_class_dists']:
        if len(percentages) != n_trans:
            raise RuntimeError("Number of distribution percentages for commercial loads ({}) "
                               "does not match the number of standard transformer sizes ({}).".format(
                                   len(percentages), n_trans))
    for percentages in data['res_load_class_dists']:
        if len(percentages) != n_trans:
            raise RuntimeError("Number of distribution percentages for residential loads ({}) "
                               "does not match the number of standard transformer sizes ({}).".format(
                                   len(percentages), n_trans))
  
  return data
  
def LoadClassConfiguration(f_config_data, classID):

    data = {}
    region = f_config_data['region']

    # Thermal Percentages by Region
    # - The "columns" represent load classifications. The "rows" represent the breakdown within that classification of building age. 
    #   1:<1940     2:1980-89   3:<1940     4:1980-89   5:<1960     6:<1960     7:<2010 8:<2010 9:<2010
    #   1:1940-49   2:>1990     3:1940-49   4:>1990     5:1960-89   6:1960-89   7:-     8:-     9:-
    #   1:1950-59   2:-         3:1950-59   4:-         5:>1990     6:>1990     7:-     8:-     9:-
    #   1:1960-69   2:-         3:1960-69   4:-         5:-         6:-         7:-     8:-     9:-
    #   1:1970-79   2:-         3:1970-79   4:-         5:-         6:-         7:-     8:-     9:-
    #   1:-         2:-         3:-       4:-         5:-         6:-         7:-     8:-     9:-
    
    ## emission dispatch order
    # Nuc Hydro Solar BioMass Wind Coal NG GeoTherm Petro
    dispatch_order = [[1,5,2,3,4,7,6,8,9],   #Res1
                      [1,7,2,3,4,5,6,8,9],   #Res2
                      [1,7,2,3,4,5,6,8,9],   #Res3
                      [1,7,2,3,4,5,6,8,9],   #Res4
                      [1,7,2,3,4,6,5,8,9],   #Res5
                      [1,7,2,3,4,5,6,8,9],   #Res6
                      [1,7,2,3,4,5,6,8,9],   #Com1
                      [1,7,2,3,4,5,6,8,9],   #Com2
                      [1,7,2,3,4,6,5,8,9]]   #Com3    
    
    # Using values from the old regionalization.m script. 
    # Retooled the old thermal percentages values into this new "matrix" form for classifications.
    if region == 1:
      thermal_percentages = [  [0.1652, 0.4935, 0.1652, 0.4935, 0.0000, 0.1940, 1, 1, 1],  #1
                               [0.1486, 0.5064, 0.1486, 0.5064, 0.7535, 0.6664, 0, 0, 0],   #2
                               [0.2238, 0.0000, 0.2238, 0.0000, 0.2462, 0.1395, 0, 0, 0],   #3
                               [0.1780, 0.0000, 0.1780, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #4
                               [0.2841, 0.0000, 0.2841, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #5
                               [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0, 0, 0]]   #6 
      data["floor_area"] = [1500, 1500, 2250, 2250, 1054, 820, 0, 0, 0]
      data["one_story"] = [0.6887] * 9
      perc_gas = [0.7051] * 9   # 'percentage' (appears to be fraction) heating with natural gas
      perc_pump = [0.0321] * 9  # 'percentage' (appears to be fraction) heating with heat pump
      perc_AC = [0.4348] * 9    # 'percentage' (appears to be fraction) with air conditioning
      wh_electric = [0.7455] * 9 # 'percentage' (appears to be fraction) with electric waterheaters
      wh_size = [[0.0000,0.3333,0.6667]] * 9 # waterheater sizing breakdown  [<30, 31-49, >50]
      AC_type = [  [1, 1, 1, 1, 1, 1, 0, 0, 0], # central
                   [0, 0, 0, 0, 0, 0, 0, 0, 0]] # window/wall unit
      over_sizing_factor = [ [ 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0, 0, 0], # central
                             [ 0, 0, 0, 0, 0, 0, 0, 0, 0] ] # window/wall unit
      perc_pool_pumps= [0.0904] * 9 # 'percentage' (appears to be fraction) of SFH (?) with pool pumps
    elif region == 2:
      thermal_percentages = [  [0.2873, 0.3268, 0.2873, 0.3268, 0.0000, 0.2878, 1, 1, 1],  #1
                               [0.1281, 0.6731, 0.1281, 0.6731, 0.6480, 0.5308, 0, 0, 0],   #2
                               [0.2354, 0.0000, 0.2354, 0.0000, 0.3519, 0.1813, 0, 0, 0],   #3
                               [0.1772, 0.0000, 0.1772, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #4
                               [0.1717, 0.0000, 0.1717, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #5
                               [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0, 0, 0]]   #6 
      data["floor_area"] = [1500, 1500, 2250, 2250, 1054, 820, 0, 0, 0]
      data["one_story"] = [0.5210] * 9
      perc_gas = [0.8927] * 9
      perc_pump = [0.0177] * 9
      perc_AC = [0.7528] * 9 
      wh_electric = [0.7485] * 9
      wh_size = [[0.1459,0.5836,0.2706]] * 9
      AC_type = [ [1, 1, 1, 1, 1, 1, 0, 0, 0],  # central
                  [0, 0, 0, 0, 0, 0, 0, 0, 0] ] # window/wall unit
      over_sizing_factor = [ [ 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0, 0, 0], # central
                             [ 0, 0, 0, 0, 0, 0, 0, 0, 0] ] # window/wall unit
      perc_pool_pumps= [0.0591] * 9
    elif region == 3:
      thermal_percentages = [  [0.1240, 0.3529, 0.1240, 0.3529, 0.0000, 0.1079, 1, 1, 1],  #1
                               [0.0697, 0.6470, 0.0697, 0.6470, 0.6343, 0.6316, 0, 0, 0],   #2
                               [0.2445, 0.0000, 0.2445, 0.0000, 0.3656, 0.2604, 0, 0, 0],   #3
                               [0.2334, 0.0000, 0.2334, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #4
                               [0.3281, 0.0000, 0.3281, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #5
                               [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0, 0, 0]]   #6 
      data["floor_area"] = [1500, 1500, 2250, 2250, 1054, 820, 0, 0, 0]
      data["one_story"] = [0.7745] * 9
      perc_gas = [0.6723] * 9
      perc_pump = [0.0559] * 9
      perc_AC = [0.5259] * 9
      wh_electric = [0.6520] * 9
      wh_size = [[0.2072,0.5135,0.2793]] * 9
      AC_type = [  [1, 1, 1, 1, 1, 1, 0, 0, 0], # central
            [0, 0, 0, 0, 0, 0, 0, 0, 0]] # window/wall unit
      over_sizing_factor = [  [ 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0, 0, 0], # central
                  [ 0, 0, 0, 0, 0, 0, 0, 0, 0]] # window/wall unit
      perc_pool_pumps= [0.0818] * 9
    elif region == 4:
      thermal_percentages = [ [0.1470, 0.3297, 0.1470, 0.3297, 0.0000, 0.1198, 1, 1, 1],  #1
                              [0.0942, 0.6702, 0.0942, 0.6702, 0.5958, 0.6027, 0, 0, 0],   #2
                              [0.2253, 0.0000, 0.2253, 0.0000, 0.4041, 0.2773, 0, 0, 0],   #3
                              [0.2311, 0.0000, 0.2311, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #4
                              [0.3022, 0.0000, 0.3022, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #5
                              [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0, 0, 0]]   #6 
      data["floor_area"] = [1500, 1500, 2250, 2250, 1054, 820, 0, 0, 0]
      data["one_story"] = [0.7043] * 9
      perc_gas = [0.4425] * 9
      perc_pump = [0.1983] * 9
      perc_AC = [0.9673] * 9
      wh_electric = [0.3572] * 9
      wh_size = [[0.2259,0.5267,0.2475]] * 9
      AC_type = [ [1, 1, 1, 1, 1, 1, 0, 0, 0],  # central
                  [0, 0, 0, 0, 0, 0, 0, 0, 0] ] # window/wall unit
      over_sizing_factor = [  [ 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0, 0, 0], # central
                              [ 0, 0, 0, 0, 0, 0, 0, 0, 0]] # window/wall unit
      perc_pool_pumps= [0.0657] * 9
    elif region == 5:
      thermal_percentages = [  [0.1470, 0.3297, 0.1470, 0.3297, 0.0000, 0.1198, 1, 1, 1],  #1
                  [0.0942, 0.6702, 0.0942, 0.6702, 0.5958, 0.6027, 0, 0, 0],   #2
                  [0.2253, 0.0000, 0.2253, 0.0000, 0.4041, 0.2773, 0, 0, 0],   #3
                  [0.2311, 0.0000, 0.2311, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #4
                  [0.3022, 0.0000, 0.3022, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #5
                  [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0, 0, 0]]   #6 
      data["floor_area"] = [1500, 1500, 2250, 2250, 1054, 820, 0, 0, 0]
      data["one_story"] = [0.7043] * 9
      perc_gas = [0.4425] * 9
      perc_pump = [0.1983] * 9
      perc_AC = [0.9673] * 9
      wh_electric = [0.3572] * 9
      wh_size = [[0.2259,0.5267,0.2475]] * 9
      AC_type = [  [1, 1, 1, 1, 1, 1, 0, 0, 0], # central
            [0, 0, 0, 0, 0, 0, 0, 0, 0]] # window/wall unit
      over_sizing_factor = [  [ 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0, 0, 0], # central
                  [ 0, 0, 0, 0, 0, 0, 0, 0, 0]] # window/wall unit
      perc_pool_pumps= [0.0657] * 9
    elif region == 6:
      thermal_percentages = [ [0.2184, 0.3545, 0.2184, 0.3545, 0.0289, 0.2919, 1, 1, 1],   #1
                              [0.0818, 0.6454, 0.0818, 0.6454, 0.6057, 0.5169, 0, 0, 0],   #2
                              [0.2390, 0.0000, 0.2390, 0.0000, 0.3652, 0.1911, 0, 0, 0],   #3
                              [0.2049, 0.0000, 0.2049, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #4
                              [0.2556, 0.0000, 0.2556, 0.0000, 0.0000, 0.0000, 0, 0, 0],   #5
                              [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0, 0, 0] ]  #6 
      data["floor_area"] = [1500, 1500, 2250, 2250, 1054, 820, 0, 0, 0]
      data["one_story"] = [0.7043] * 9
      perc_gas = [0.4425] * 9
      perc_pump = [0.1983] * 9
      perc_AC = [0.9673] * 9
      wh_electric = [0.3572] * 9
      wh_size = [[0.2259,0.5267,0.2475]] * 9
      AC_type = [  [1, 1, 1, 1, 1, 1, 0, 0, 0], # central
            [0, 0, 0, 0, 0, 0, 0, 0, 0]] # window/wall unit
      over_sizing_factor = [  [ 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0, 0, 0], # central
                  [ 0, 0, 0, 0, 0, 0, 0, 0, 0]] # window/wall unit
      perc_pool_pumps= [0.0657] * 9
      
      
    # Single-Family Homes
    # - Designate the percentage of SFH in each classification
    SFH = [[1, 1, 1, 1, 0, 0, 0, 0, 0], # Res1-Res4 are 100% SFH.
           [1, 1, 1, 1, 0, 0, 0, 0, 0],
           [1, 1, 1, 1, 0, 0, 0, 0, 0],
           [1, 1, 1, 1, 0, 0, 0, 0, 0],
           [1, 1, 1, 1, 0, 0, 0, 0, 0],
           [1, 1, 1, 1, 0, 0, 0, 0, 0]] 

    # COP High/Low Values
    # - "columns" represent load classifications. The "rows" represent the sub-classifications (See thermal_percentages).
    cop_high = [[2.8, 3.8, 2.8, 3.8, 0.0, 2.8, 0, 0, 0], 
                [3.0, 4.0, 3.0, 4.0, 2.8, 3.0, 0, 0, 0], 
                [3.2, 0.0, 3.2, 0.0, 3.5, 3.2, 0, 0, 0], 
                [3.4, 0.0, 3.4, 0.0, 0.0, 0.0, 0, 0, 0], 
                [3.6, 0.0, 3.6, 0.0, 0.0, 0.0, 0, 0, 0], 
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0]]
    
    cop_low = [[2.4, 3.0, 2.4, 3.0, 0.0, 1.9, 0, 0, 0], 
               [2.5, 3.0, 2.5, 3.0, 1.9, 2.0, 0, 0, 0], 
               [2.6, 0.0, 2.6, 0.0, 2.2, 2.1, 0, 0, 0], 
               [2.8, 0.0, 2.8, 0.0, 0.0, 0.0, 0, 0, 0], 
               [3.0, 0.0, 3.0, 0.0, 0.0, 0.0, 0, 0, 0], 
               [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0]]

    # Thermal Properties
    # - There should be a list of properties for each entry in thermal_percentages. (Each sub-classification in each classification)
    # - thermal_properties[i][j] = [ R-ceil,R-wall,R-floor,window layers,window glass, glazing treatment, window frame, R-door, Air infiltrationS ]
    # - for i = subclassficaiton, j = classification
    thermal_properties = [None] * 6 
    for i in range(6):
      thermal_properties[i] = [None] * 9  
      # Now we have a list of 6 lists of "None"

    # For each non-zero entry for a classification ("column") in thermal_percentages, fill in thermal properties. 
    # Res 1 (sfh pre-1980, <2000sf)
    thermal_properties[0][0] = [16, 10, 10, 1, 1, 1, 1, 3, 0.75]  # <1940
    thermal_properties[1][0] = [19, 11, 12, 2, 1, 1, 1, 3, 0.75]  # 1940-49
    thermal_properties[2][0] = [19, 14, 16, 2, 1, 1, 1, 3, 0.50]  # 1950-59
    thermal_properties[3][0] = [30, 17, 19, 2, 1, 1, 2, 3, 0.50]  # 1960-69
    thermal_properties[4][0] = [34, 19, 20, 2, 1, 1, 2, 3, 0.50]  # 1970-79
    thermal_properties[5][0] = [0, 0, 0, 0, 0, 0, 0, 0, 0]        # n/a
    
    # Res2 (sfh post-1980, <2000sf)
    thermal_properties[0][1] = [36, 22, 22, 2, 2, 1, 2, 5, 0.25]  # 1980-89
    thermal_properties[1][1] = [48, 28, 30, 3, 2, 2, 4, 11, 0.25] # >1990
    thermal_properties[2][1] = [0, 0, 0, 0, 0, 0, 0, 0, 0]        # n/a
    thermal_properties[3][1] = [0, 0, 0, 0, 0, 0, 0, 0, 0]        # n/a
    thermal_properties[4][1] = [0, 0, 0, 0, 0, 0, 0, 0, 0]        # n/a
    thermal_properties[5][1] = [0, 0, 0, 0, 0, 0, 0, 0, 0]        # n/a
    
    # Res3 (sfh pre-1980, >2000sf, val's identical to Res1)
    thermal_properties[0][2] = [16, 10, 10, 1, 1, 1, 1, 3, 0.75]  # <1940
    thermal_properties[1][2] = [19, 11, 12, 2, 1, 1, 1, 3, 0.75]  # 1940-49
    thermal_properties[2][2] = [19, 14, 16, 2, 1, 1, 1, 3, 0.50]  # 1950-59
    thermal_properties[3][2] = [30, 17, 19, 2, 1, 1, 2, 3, 0.50]  # 1960-69
    thermal_properties[4][2] = [34, 19, 20, 2, 1, 1, 2, 3, 0.50]  # 1970-79
    thermal_properties[5][2] = [0, 0, 0, 0, 0, 0, 0, 0, 0]        # n/a
    
    # Res4 (sfh post-1980, >2000sf, val's identical to Res2)
    thermal_properties[0][3] = [36, 22, 22, 2, 2, 1, 2, 5, 0.25]  # 1980-89
    thermal_properties[1][3] = [48, 28, 30, 3, 2, 2, 4, 11, 0.25] # >1990
    thermal_properties[2][3] = [0, 0, 0, 0, 0, 0, 0, 0, 0]        # n/a
    thermal_properties[3][3] = [0, 0, 0, 0, 0, 0, 0, 0, 0]        # n/a
    thermal_properties[4][3] = [0, 0, 0, 0, 0, 0, 0, 0, 0]        # n/a
    thermal_properties[5][3] = [0, 0, 0, 0, 0, 0, 0, 0, 0]        # n/a
    
    # Res5 (mobile homes)
    thermal_properties[0][4] = [0, 0, 0, 0, 0, 0, 0, 0, 0]               # <1960
    thermal_properties[1][4] = [13.4, 9.2,  11.7, 1, 1, 1, 1, 2.2, .75]  # 1960-1989
    thermal_properties[2][4] = [24.1, 11.7, 18.1, 2, 2, 1, 2, 3.0, .75]  # >1990
    thermal_properties[3][4] = [0, 0, 0, 0, 0, 0, 0, 0, 0]               # n/a
    thermal_properties[4][4] = [0, 0, 0, 0, 0, 0, 0, 0, 0]               # n/a
    thermal_properties[5][4] = [0, 0, 0, 0, 0, 0, 0, 0, 0]               # n/a
    
    # Res6 (apartments)
    thermal_properties[0][5] = [13.4, 11.7,  9.4, 1, 1, 1, 1, 2.2, .75]    # <1960
    thermal_properties[1][5] = [20.3, 11.7, 12.7, 2, 1, 2, 2, 2.7, 0.25]   # 1960-1989
    thermal_properties[2][5] = [28.7, 14.3, 12.7, 2, 2, 3, 4, 6.3, 0.125]  # >1990 
    thermal_properties[3][5] = [0, 0, 0, 0, 0, 0, 0, 0, 0]                 # n/a
    thermal_properties[4][5] = [0, 0, 0, 0, 0, 0, 0, 0, 0]                 # n/a
    thermal_properties[5][5] = [0, 0, 0, 0, 0, 0, 0, 0, 0]                 # n/a
    
    # Com3
    thermal_properties[0][6] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[1][6] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[2][6] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[3][6] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[4][6] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[5][6] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    
    # Com2
    thermal_properties[0][7] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[1][7] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[2][7] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[3][7] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[4][7] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[5][7] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    
    # Com1
    thermal_properties[0][8] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[1][8] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[2][8] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[3][8] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[4][8] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    thermal_properties[5][8] = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # n/a
    
    # Cooling Setpoint Bins by Classification
    # [nighttime percentage, high bin value, low bin value]
    cooling_setpoint = [None] * 9
    
    cooling_setpoint[0] =  [[0.098, 69, 65], #Res1
                                [0.140, 70, 70],
                                [0.166, 73, 71],
                                [0.306, 76, 74],
                                [0.206, 79, 77],
                                [0.084, 85, 80]]                                
    
    cooling_setpoint[1] =  [[0.098, 69, 65], #Res2
                                [0.140, 70, 70],
                                [0.166, 73, 71],
                                [0.306, 76, 74],
                                [0.206, 79, 77],
                                [0.084, 85, 80]]
    
    cooling_setpoint[2] =  [[0.098, 69, 65], #Res3
                                [0.140, 70, 70],
                                [0.166, 73, 71],
                                [0.306, 76, 74],
                                [0.206, 79, 77],
                                [0.084, 85, 80]]
    
    cooling_setpoint[3] =  [[0.098, 69, 65], #Res4
                                [0.140, 70, 70],
                                [0.166, 73, 71],
                                [0.306, 76, 74],
                                [0.206, 79, 77],
                                [0.084, 85, 80]]
    
    cooling_setpoint[4] =  [[0.138, 69, 65], #Res5
                                [0.172, 70, 70],
                                [0.172, 73, 71],
                                [0.276, 76, 74],
                                [0.138, 79, 77],
                                [0.103, 85, 80]]
    
    cooling_setpoint[5] =  [[0.155, 69, 65], #Res6
                                [0.207, 70, 70],
                                [0.103, 73, 71],
                                [0.310, 76, 74],
                                [0.155, 79, 77],
                                [0.069, 85, 80]]
    
    cooling_setpoint[6] =  [[0.098, 69, 65], #Com1
                                [0.140, 70, 70],
                                [0.166, 73, 71],
                                [0.306, 76, 74],
                                [0.206, 79, 77],
                                [0.084, 85, 80]]
    
    cooling_setpoint[7] =  [[0.098, 69, 65], #Com2
                                [0.140, 70, 70],
                                [0.166, 73, 71],
                                [0.306, 76, 74],
                                [0.206, 79, 77],
                                [0.084, 85, 80]]
    
    cooling_setpoint[8] =  [[0.098, 69, 65], #Com3
                                [0.140, 70, 70],
                                [0.166, 73, 71],
                                [0.306, 76, 74],
                                [0.206, 79, 77],
                                [0.084, 85, 80]]

    # Heating Setpoint Bins by Classification
    heating_setpoint = [None] * 9
    
    heating_setpoint[0] =  [[0.141, 63, 59], #Res1
                                [0.204, 66, 64],
                                [0.231, 69, 67],
                                [0.163, 70, 70],
                                [0.120, 73, 71],
                                [0.141, 79, 74]]
    
    heating_setpoint[1] =  [[0.141, 63, 59], #Res2
                                [0.204, 66, 64],
                                [0.231, 69, 67],
                                [0.163, 70, 70],
                                [0.120, 73, 71],
                                [0.141, 79, 74]]
    
    heating_setpoint[2] =  [[0.141, 63, 59], #Res3
                                [0.204, 66, 64],
                                [0.231, 69, 67],
                                [0.163, 70, 70],
                                [0.120, 73, 71],
                                [0.141, 79, 74]]
    
    heating_setpoint[3] =  [[0.141, 63, 59], #Res4
                                [0.204, 66, 64],
                                [0.231, 69, 67],
                                [0.163, 70, 70],
                                [0.120, 73, 71],
                                [0.141, 79, 74]]
    
    heating_setpoint[4] =  [[0.129, 63, 59], #Res5
                                [0.177, 66, 64],
                                [0.161, 69, 67],
                                [0.274, 70, 70],
                                [0.081, 73, 71],
                                [0.177, 79, 74]]
    
    heating_setpoint[5] =  [[0.085, 63, 59], #Res6
                                [0.132, 66, 64],
                                [0.147, 69, 67],
                                [0.279, 70, 70],
                                [0.109, 73, 71],
                                [0.248, 79, 74]]
    
    heating_setpoint[6] =  [[0.141, 63, 59], #Com1
                                [0.204, 66, 64],
                                [0.231, 69, 67],
                                [0.163, 70, 70],
                                [0.120, 73, 71],
                                [0.141, 79, 74]]
    
    heating_setpoint[7] =  [[0.141, 63, 59], #Com2
                                [0.204, 66, 64],
                                [0.231, 69, 67],
                                [0.163, 70, 70],
                                [0.120, 73, 71],
                                [0.141, 79, 74]]
    
    heating_setpoint[8] =  [[0.141, 63, 59], #Com3
                                [0.204, 66, 64],
                                [0.231, 69, 67],
                                [0.163, 70, 70],
                                [0.120, 73, 71],
                                [0.141, 79, 74]]
    
    perc_res = list(map(lambda x, y:1-x-y, perc_pump, perc_gas))
    
    # heating offset
    allsame_c = 2
    
    # cooling offset
    allsame_h = 2
    
    # COP high scalar
    COP_high = 1
    
    # COP low scalar
    COP_low = 1    
                   
    # decrease gas heating percentage
    decrease_gas = 1                   
                   
    # Apply calibration scalars
    for x in cooling_setpoint:
      if x is None:
        pass
      else:
        for j in range(len(x)):
          x[j].insert(1,allsame_c)
          
    for x in heating_setpoint:
      if x is None:
        pass
      else:
        for j in range(len(x)):
          x[j].insert(1,allsame_h)
          
    cop_high_new = []
    
    for x in cop_high:
      cop_high_new.append([round(COP_high*y,2) for y in x])
      
    cop_low_new = []
    
    for x in cop_low:
      cop_low_new.append([round(COP_low*y,2) for y in x])
      
    for i in range(len(thermal_properties)):
      if thermal_properties[i] is None:
        pass
      else:
        for j in range(len(thermal_properties[i])):
          if thermal_properties[i][j] is None:
            pass
          else:
            thermal_properties[i][j].extend([cop_high_new[i][j],cop_low_new[i][j]])
            
      perc_pump = list(map(lambda x, y: x + (1-decrease_gas)*y,perc_pump,perc_gas))
      perc_gas = list(map(lambda x:x*decrease_gas,perc_gas))
                       
      data["thermal_percentages"] = [None]*len(thermal_percentages)
      for x in range(len(thermal_percentages)):
        data["thermal_percentages"][x] = thermal_percentages[x][classID]

      data["thermal_properties"] = [None]*len(thermal_properties)
      for x in range(len(thermal_properties)):
        data["thermal_properties"][x] = thermal_properties[x][classID]

      data["cooling_setpoint"] = cooling_setpoint[classID] 
      data["heating_setpoint"] = heating_setpoint[classID]
      data["perc_gas"] = perc_gas[classID]
      data["perc_pump"] = perc_pump[classID]
      data["perc_res"] = perc_res[classID]
      data["perc_AC"] = perc_AC[classID]
      data["perc_poolpumps"] = perc_pool_pumps[classID]
      data["wh_electric"] = wh_electric[classID]
      data["wh_size"] = wh_size[classID]
      
      data["over_sizing_factor"] = [None]*len(over_sizing_factor)
      for x in range(len(over_sizing_factor)):
        data["over_sizing_factor"][x] = over_sizing_factor[x][classID]
        
      data["AC_type"] = [None]*len(AC_type)
      for x in range(len(AC_type)):
        data["AC_type"][x] = AC_type[x][classID]
        
      data["dispatch_order"] = dispatch_order[classID]

      data["SFH"] = [None]*len(SFH)
      for x in range(len(SFH)):
        data["SFH"][x] = SFH[x][classID]
        
    return data

def main():
  #tests here
  config_data = ConfigurationFunc(None,None,4)
  #print(config_data['cooling_setpoint'][0])
if __name__ ==  '__main__':
  main()
