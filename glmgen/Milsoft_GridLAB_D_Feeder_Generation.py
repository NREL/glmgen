#Python Extraction and Calibration Version of MATLAB Scripts
#Note: This assumes that dictionary being passed in already contains split-phase center-tapped transformers with spot loads ( triplex_nodes ) on the secondary side.
#Note: All triplex_node dictionaries must contain a load classification key which tells what type of houses are located at this spot load.
#Note: All swing node objects must have a Dictionary key
from __future__ import division

import math
import random
import copy
import re

from glmgen import Configuration
from glmgen import TechnologyParameters
from glmgen import Solar_Technology
from glmgen import feeder
from glmgen import helpers
from glmgen import AddTapeObjects
from glmgen import AddLoadShapes
from glmgen import ResidentialLoads
from glmgen import CommercialLoads

def get_parameters(io_opts, model_opts):
  # Check to make sure we have a valid case flag
  if model_opts['tech_flag'] < -1:
    model_opts['tech_flag'] = 0

  if model_opts['tech_flag'] > 13:
    model_opts['tech_flag'] = 13
  
  # Get information about each feeder from Configuration() and  TechnologyParameters()
  config_data = Configuration.FeederConfiguration(io_opts['dir'], io_opts['resources_dir'])
  
  for key, value in model_opts['config_data'].items():
      config_data[key] = value
      
  # Update regional data not filled in by the user. Specifically:
  #   - weather file
  #   - time zone
  #   - average peak load by load classification
  config_data = Configuration.FeederConfiguration(io_opts['dir'], io_opts['resources_dir'], config_data)
      
  random.seed(1) if config_data["fix_random_seed"] else random.seed()
  
  # HERE -- feeder_rating to 20 MVA since there is a 17 MVA (bigger than the current default of 16 MVA) feeder
  
  #set up default flags
  use_flags = {}
  tech_data, use_flags = TechnologyParameters.TechnologyParametersFunc(use_flags,model_opts['tech_flag'])
  
  for key, value in model_opts['tech_data'].items():
      tech_data[key] = value
      
  for key, value in model_opts['use_flags'].items():
      use_flags[key] = value
  
  return model_opts, config_data, tech_data, use_flags

def Append_Solar(glmDict, io_opts, time_opts, location_opts, model_opts):
  """
  glmDict is a feeder already processed by GLD_Feeder, but with no solar yet appended.
  """
  
  model_opts, config_data, tech_data, use_flags = get_parameters(io_opts, model_opts)
  
  glmDict.set_no_reindexing()
  last_key = len(glmDict)
  
  # Append Solar: Call append_solar(feeder_dict, use_flags, config_file, solar_bigbox_array, solar_office_array, solar_stripmall_array, solar_residential_array, last_key)
  if use_flags['use_solar'] != 0 or use_flags['use_solar_res'] != 0 or use_flags['use_solar_com'] != 0:
    glmDict = Solar_Technology.Append_Solar(glmDict, use_flags, config_data, tech_data, last_key)
    
  # Append recorders
  glmDict, last_key = AddTapeObjects.add_recorders(glmDict, io_opts, time_opts, last_key, solar_only = True)

  return (glmDict, last_key)  
  

def GLD_Feeder(glmDict, io_opts, time_opts, location_opts, model_opts):
  """
  glmDict is a dictionary containing all the objects in WindMIL model represented as equivalent GridLAB-D objects

  model_opts['tech_flag'] is an integer indicating which technology case to tack on to the GridLAB-D model
    -1 : Loadshape Case
     0 : Base Case
     1 : CVR
     2 : Automation
     3 : FDIR
     4 : TOU/CPP w/ tech
     5 : TOU/CPP w/o tech
     6 : TOU w/ tech
     7 : TOU w/o tech
     8 : DLC
     9 : Thermal Storage
    10 : PHEV
    11 : Solar Residential
    12 : Solar Commercial
    13 : Solar Combined

  io_opts['config_file'] is the name of the file to use for getting feeder information

  GLD_Feeder returns a dictionary, glmCaseDict, similar to glmDict with additional object dictionaries added according to the model_opts['tech_flag'] selected.
  """

  model_opts, config_data, tech_data, use_flags = get_parameters(io_opts, model_opts)
  
  #tmy = 'schedules\\\\SCADA_weather_ISW_gld.csv'
  tmy = config_data['weather']

  #find name of swingbus of static model dictionary
  swing_bus_name = None
  nom_volt = None
  for x in glmDict:
    if ('bustype' in glmDict[x]) and (glmDict[x]['bustype'] == 'SWING'):
      swing_bus_name = glmDict[x]['name']
      nom_volt = glmDict[x]['nominal_voltage'] # Nominal voltage in V
      break
  assert(swing_bus_name is not None)
  assert(nom_volt is not None)

  # Create new case dictionary
  glmCaseDict = feeder.GlmFile()
  glmCaseDict.set_no_reindexing()
  last_key = len(glmCaseDict)

  # Create clock dictionary
  glmCaseDict[last_key] = {'clock' : '',
               'timezone' : '{:s}'.format(config_data['timezone']),
               'starttime' : "'{:s}'".format(tech_data['start_date']),
               'stoptime' : "'{:s}'".format(tech_data['end_date'])}
  last_key += 1

  # Create dictionaries of preprocessor directives
  if use_flags['use_homes'] != 0:
    glmCaseDict[last_key] = {'#include' : '{:s}/appliance_schedules.glm'.format(io_opts['resources_dir'])}
    last_key += 1
    glmCaseDict[last_key] = {'#include' : '{:s}/water_and_setpoint_schedule_v5.glm'.format(io_opts['resources_dir'])}
    last_key += 1

  if use_flags['use_battery'] == 1 or use_flags['use_battery'] == 2:
    glmCaseDict[last_key] = {'#include' : '{:s}/battery_schedule.glm'.format(io_opts['resources_dir'])}
    last_key += 1

  if use_flags['use_commercial'] == 1:
    glmCaseDict[last_key] = {'#include' : '{:s}/commercial_schedules.glm'.format(io_opts['resources_dir'])}
    last_key += 1

  if use_flags['use_market'] == 1 or use_flags['use_market'] == 2:
    glmCaseDict[last_key] = {'#include' : '{:s}/daily_elasticity_schedules.glm'.format(io_opts['resources_dir'])}
    last_key += 1

  if use_flags['use_ts'] == 2 or use_flags['use_ts'] == 4:
    glmCaseDict[last_key] = {'#include' : '{:s}/thermal_storage_schedule_R{:d}.glm'.format(io_opts['resources_dir'],config_data['region'])}
    last_key += 1

  glmCaseDict[last_key] = {'#define' : 'stylesheet=http://gridlab-d.svn.sourceforge.net/viewvc/gridlab-d/trunk/core/gridlabd-2_0'}
  last_key += 1

  glmCaseDict[last_key] = { '#set' : 'minimum_timestep={}'.format(time_opts['sim_interval'].total_seconds()) }
  last_key += 1

  glmCaseDict[last_key] = {'#set' : 'profiler=1'}
  last_key += 1

  glmCaseDict[last_key] = {'#set' : 'relax_naming_rules=1'}
  last_key += 1

  # Create dictionaries of modules to be used from the model_opts['tech_flag']
  glmCaseDict[last_key] = {'module' : 'tape'}
  last_key += 1

  glmCaseDict[last_key] = {'module' : 'climate'}
  last_key += 1

  glmCaseDict[last_key] = {'module' : 'residential',
                           'implicit_enduses' : 'NONE'}
  last_key += 1

  glmCaseDict[last_key] = {'module' : 'powerflow',
                           'solver_method' : 'NR',
                           'NR_iteration_limit' : '50'}
  last_key += 1

  if use_flags['use_solar'] != 0 or use_flags['use_solar_res'] != 0 or use_flags['use_solar_com'] != 0 or use_flags['use_battery'] == 1 or use_flags['use_battery'] == 2:
    glmCaseDict[last_key] = {'module' : 'generators'}
    last_key += 1

  if use_flags['use_market'] != 0:
    glmCaseDict[last_key] = {'module' : 'market'}
    last_key += 1

  # Add the class player dictionary to glmCaseDict
  glmCaseDict[last_key] = {'class' : 'player',
               'variable_types' : ['double'],
               'variable_names' : ['value']}
  last_key += 1
  
  if use_flags['use_normalized_loadshapes'] == 1:
    glmCaseDict[last_key] = {'object' : 'player',
                 'name' : 'norm_feeder_loadshape',
                 'property' : 'value',
                 'file' : '{:s}'.format(config_data['load_shape_norm']),
                 'loop' : '14600',
                 'comment' : '// Will loop file for 40 years assuming the file has data for a 24 hour period'}
    last_key += 1
    
  # Include the objects for the TOU case flags
  if use_flags['use_market'] != 0:
    # Add class auction dictionary to glmCaseDict
    glmCaseDict[last_key] = {'class' : 'auction',
                 'variable_types' : ['double','double'],
                 'variable_names' : ['my_avg','my_std']}
    last_key += 1

    # Add CPP player dictionary to glmCaseDict
    CPP_flag_name = config_data['CPP_flag'] # Strip '.player' from config_data['CPP_flag']
    CPP_flag_name.replace('.player','')
    glmCaseDict[last_key] = {'object' : 'player',
                 'name' : CPP_flag_name,
                 'file' : config_data['CPP_flag']}
    last_key += 1

    # Add auction object dictionary to glmCaseDict
    # Determine which stat to use for my_avg and my_std
    if use_flags['use_market'] == 1: #TOU
      temp_avg = config_data['TOU_stats'][0]
      temp_std = config_data['TOU_stats'][1]
    elif use_flags['use_market'] == 2 or use_flags['use_market'] == 3: #TOU/CPP
      temp_avg = config_data['CPP_stats'][0]
      temp_std = config_data['CPP_stats'][1]

    glmCaseDict[last_key] = {'object' : 'auction',
                 'name' : tech_data['market_info'][0],
                 'period' : "{:.0f}".format(tech_data['market_info'][1]),
                 'special_mode' : 'BUYERS_ONLY',
                 'unit' : 'kW',
                 'my_avg' : temp_avg,
                 'my_std' : temp_std}
    parent_key = last_key
    last_key += 1

    # Add player object dictionary for the auction object's clearing price
    # Determine which file to use for the clear_price
    if use_flags['use_market'] == 1: #TOU
      auction_price_file = config_data['TOU_price_player']
    elif use_flags['use_market'] == 2 or use_flags['use_market'] == 3: #TOU/CPP
      auction_price_file = config_data['CPP_price_player']

    glmCaseDict[last_key] = {'object' : 'player',
                 'parent' : glmCaseDict[parent_key]['name'],
                 'file' : auction_price_file,
                 'loop' : '10',
                 'property' : 'current_market.clearing_price'}
    last_key += 1
  else:
    CPP_flag_name = None;

  # Add climate dictionaries
  if '.csv' in tmy:
    # Climate file is a cvs file. Need to add csv_reader object
    glmCaseDict[last_key] = {'object' : 'csv_reader',
                             'name' : 'CsvReader',
                             'filename' : '"{:s}"'.format(tmy)}
    last_key += 1
    climate_name = tmy.replace('.csv','')
  elif '.tmy2' in tmy:
    climate_name = tmy.replace('.tmy2','')

  glmCaseDict[last_key] = {'object' : 'climate',
                           'name' : '"{:s}"'.format(climate_name),
                           'tmyfile' : '"{:s}"'.format(tmy)}
  if '.tmy2' in tmy:
    glmCaseDict[last_key]['interpolate'] = 'QUADRATIC'
  elif '.csv' in tmy:
    glmCaseDict[last_key]['reader'] = 'CsvReader'
  last_key += 1

  # Add substation transformer transformer_configuration
  glmCaseDict[last_key] = {'object' : 'transformer_configuration',
               'name' : 'trans_config_to_feeder',
               'connect_type' : 'WYE_WYE',
               'install_type' : 'PADMOUNT',
               'primary_voltage' : '{}'.format(config_data['nom_volt']),
               'secondary_voltage' : '{:s}'.format(nom_volt),
               'power_rating' : '{:.1f} MVA'.format(config_data['feeder_rating']),
               'impedance' : '0.00033+0.0022j'}
  last_key += 1

  # Add CVR controller
  if use_flags['use_vvc'] == 1:
    # TODO: pull all of these out and put into TechnologyParameters()
    glmCaseDict[last_key] = {'object' : 'volt_var_control',
                 'name' : 'volt_var_control',
                 'control_method' : 'ACTIVE',
                 'capacitor_delay' : '60.0',
                 'regulator_delay' : '60.0',
                 'desired_pf' : '0.99',
                 'd_max' : '0.8',
                 'd_min' : '0.1',
                 'substation_link' : 'substation_transfromer',
                 'regulator_list' : '"{:s}"'.format(','.join(config_data['regulators'])), # config_data['regulators'] should contain a list of the names of the regulators that use CVR
                 'maximum_voltage' : '{:.2f}'.format(config_data['voltage_regulation'][2]),
                 'minimum_voltage' : '{:.2f}'.format(config_data['voltage_regulation'][1]),
                 'max_vdrop' : '50',
                 'high_load_deadband' :'{:.2f}'.format(config_data['voltage_regulation'][4]),
                 'desired_voltages' : '{:.2f}'.format(config_data['voltage_regulation'][0]),
                 'low_load_deadband' : '{:.2f}'.format(config_data['voltage_regulation'][3])}

    num_caps = len(config_data['capacitor_outage']) if 'capacitor_outage' in config_data else 0
    if num_caps > 0:
      glmCaseDict[last_key]['capacitor_list'] = '"'

      for x in range(num_caps):
        if x < (num_caps - 1):
          glmCaseDict[last_key]['capacitor_list'] = glmCaseDict[last_key]['capacitor_list'] + '{:s},'.format(config_data['capacitor_outage'][x][0])
        else:
          glmCaseDict[last_key]['capacitor_list'] = glmCaseDict[last_key]['capacitor_list'] + '{:s}"'.format(config_data['capacitor_outage'][x][0])
    else:
      glmCaseDict[last_key]['capacitor_list'] = '""'

    num_eol = len(config_data['EOL_points'])
    glmCaseDict[last_key]['voltage_measurements'] = '"'

    for x in range(num_eol):
      if x < (num_eol - 1):
        glmCaseDict[last_key]['voltage_measurements'] = glmCaseDict[last_key]['voltage_measurements'] + '{:s},{:d},'.format(config_data['EOL_points'][x][0],config_data['EOL_points'][x][2])
      else:
        glmCaseDict[last_key]['voltage_measurements'] = glmCaseDict[last_key]['voltage_measurements'] + '{:s},{:d}"'.format(config_data['EOL_points'][x][0],config_data['EOL_points'][x][2])
    last_key += 1

  # Add substation swing bus and substation transformer dictionaries
  #TMH - any values that we want to bus.py to measure from the swing bus need to be added here (e.g., 'measured_power' : '0',
  glmCaseDict[last_key] = {'object' : 'meter',
               'name' : 'network_node',
               'bustype' : 'SWING',
               'nominal_voltage' : '{}'.format(config_data['nom_volt']),
               'phases' : 'ABCN',
			   'measured_power' : '0',
			   'measured_current_A' : '0',
			   'measured_current_B' : '0',
			   'measured_current_C' : '0'}
  # Add transmission voltage players
  parent_key = last_key
  last_key += 1

  if config_data["voltage_players"][0] is not None:
    glmCaseDict[last_key] = {'object' : 'player',
                             'property' : 'voltage_A',
                             'parent' : '{:s}'.format(glmCaseDict[parent_key]['name']),
                             'loop' : '10',
                             'file' : '{:s}'.format(config_data["voltage_players"][0])}
    last_key += 1

  if config_data["voltage_players"][1] is not None:
    glmCaseDict[last_key] = {'object' : 'player',
                             'property' : 'voltage_B',
                             'parent' : '{:s}'.format(glmCaseDict[parent_key]['name']),
                             'loop' : '10',
                             'file' : '{:s}'.format(config_data["voltage_players"][1])}
    last_key += 1

  if config_data["voltage_players"][2] is not None:
    glmCaseDict[last_key] = {'object' : 'player',
                             'property' : 'voltage_C',
                             'parent' : '{:s}'.format(glmCaseDict[parent_key]['name']),
                             'loop' : '10',
                             'file' : '{:s}'.format(config_data["voltage_players"][2])}
    last_key += 1

  glmCaseDict[last_key] = {'object' : 'transformer',
               'name' : 'substation_transformer',
               'from' : 'network_node',
               'to' : '{:s}'.format(swing_bus_name),
               'phases' : 'ABCN',
               'configuration' : 'trans_config_to_feeder'}
  last_key += 1

  # Copy static powerflow model glm dictionary into case dictionary
  for x in glmDict:
      # skip clocks, since already added one
      if 'clock' in glmDict[x]:
          continue
  
      glmCaseDict[last_key] = copy.deepcopy(glmDict[x])

      # Remove original swing bus from static model
      if 'bustype' in glmCaseDict[last_key] and glmCaseDict[last_key]['bustype'] == 'SWING':
          swing_node = glmCaseDict[last_key]['name']
          del glmCaseDict[last_key]['bustype']
          glmCaseDict[last_key]['object'] = 'meter'
      last_key += 1


  # Add groupid's to lines and transformers
  for x in glmCaseDict:
    if 'object' in glmCaseDict[x]:
      if re.match("triplex_line.*",glmCaseDict[x]['object']):
        glmCaseDict[x]['groupid'] = 'Triplex_Line'
      elif re.match("transformer.*",glmCaseDict[x]['object']):
        glmCaseDict[x]['groupid'] = 'Distribution_Trans'
      elif re.match("overhead_line.*",glmCaseDict[x]['object']) or re.match("underground_line.*",glmCaseDict[x]['object']):
        glmCaseDict[x]['groupid'] = 'Distribution_Line'
  
  # Create dictionary that houses the number of commercial 'load' objects where commercial house objects will be tacked on.
  commercial_dict = {}
  if use_flags['use_commercial'] == 1:
    commercial_key = 0

    to_remove = []
    for x in glmCaseDict:
      if 'object' in glmCaseDict[x] and re.match("load.*",glmCaseDict[x]['object']):
        commercial_dict[commercial_key] = {'name' : glmCaseDict[x]['name'],
                                           'parent' : 'None',
                                           'load_classification' : 'None',
                                           'load' : [0,0,0],
                                           'number_of_houses' : [0,0,0], #[phase A, phase B, phase C]
                                           'nom_volt' : glmCaseDict[x]['nominal_voltage'],
                                           'phases' : glmCaseDict[x]['phases']}
        
        if 'parent' in glmCaseDict[x]:
          commercial_dict[commercial_key]['parent'] = glmCaseDict[x]['parent']

        if 'load_class' in glmCaseDict[x]:
          commercial_dict[commercial_key]['load_classification'] = glmCaseDict[x]['load_class']

        # Figure out how many houses should be attached to this load object
        # First determine the total ZIP load for each phase
        load_A, load_B, load_C = helpers.calculate_load_by_phase(glmCaseDict[x], 'real')

        commercial_dict[commercial_key]['load'][0] = load_A
        commercial_dict[commercial_key]['load'][1] = load_B
        commercial_dict[commercial_key]['load'][2] = load_C

        # TODO: Bypass this if load rating is known
        # Determine load_rating
        total_load = (load_A + load_B + load_C)/1000.0
        load_rating, load_rating_index = helpers.get_transformer_size(
                                             total_load, 
                                             config_data['standard_transformer_ratings'], 
                                             config_data['tranformer_oversize_factor'])
        commercial_dict[commercial_key]['load_rating'] = load_rating

        # Deterimine load classification
        load_class = None
        if commercial_dict[commercial_key]['load_classification'].isdigit():
          load_class = int(commercial_dict[commercial_key]['load_classification'])
        else: 
          # load_classification is unknown determine from no_houses and transformer size
          random_class_number = random.random()*100
          cum_perc = 0
          for i, perc in enumerate([one_load_class[load_rating_index] for one_load_class in config_data['comm_load_class_dists']]):
            if cum_perc < random_class_number <= cum_perc + perc:
                 load_class = 6 + i
                 break
            cum_perc += perc
            
        assert load_class is not None
        commercial_dict[commercial_key]['load_classification'] = load_class
          
        # print('Replacing {:.0f} kW with buildings of type {}, on a transformer rated at {} kW.'.format(
        #       total_load,
        #       config_data["load_classifications"][load_class],
        #       load_rating))

        # Remove load (used to be changed into a node, but then the node was dangling)
        to_remove.append(x)
          
        # if load parented by meter ...
        meter_key = glmCaseDict.get_parent_key(x,'meter')
        if meter_key is not None:
          transformer_key = glmCaseDict.get_connector_by_to_node(meter_key,'transformer')
          if transformer_key is not None and 'phases' in glmCaseDict[transformer_key]:
            phases = glmCaseDict[transformer_key]['phases']
            m = re.match("(A|B|C|AB|AC|BC|ABC)N",phases)
            if m is not None:
              phase = m.group(1)
              # ... and the structure is what we expect, swap out the transformer for an overhead_line
              glmCaseDict[transformer_key]['object'] = 'overhead_line'
              glmCaseDict[transformer_key]['length'] = '50ft'
              glmCaseDict[transformer_key]['configuration'] = 'line_configuration_comm{:s}'.format(phase)
              glmCaseDict[transformer_key]['groupid'] = 'Distribution_Line'

        commercial_key += 1
        
    for x in to_remove:
      del glmCaseDict[x]
        
  # Create dictionary that houses the number of residential 'load' objects where residential house objects will be tacked on.
  residential_dict = {}
  if use_flags['use_homes'] == 1:
    residential_key = 0
    to_remove = []
    for x in glmCaseDict:
      if 'object' in glmCaseDict[x] and re.match("triplex_node.*",glmCaseDict[x]['object']):
        if 'power_1' in glmCaseDict[x] or 'power_12' in glmCaseDict[x]:
          residential_dict[residential_key] = {'name' : glmCaseDict[x]['name'],
                             'parent' : 'None',
                             'load_classification' : 'None',
                             'number_of_houses' : 0,
                             'load' : 0,
                             'large_vs_small' : 0.0,
                             'phases' : glmCaseDict[x]['phases']}
          
          if 'parent' in glmCaseDict[x]:
            residential_dict[residential_key]['parent'] = glmCaseDict[x]['parent']

          if 'load_class' in glmCaseDict[x]:
            residential_dict[residential_key]['load_classification'] = glmCaseDict[x]['load_class']

          # Figure out how many houses should be attached to this load object          
          # First determine the total ZIP load
          load = helpers.calculate_load(glmCaseDict[x], 'real')
          c_load = helpers.calculate_load(glmCaseDict[x], 'complex')
          
          residential_dict[residential_key]['load'] = load  
          residential_dict[residential_key]['complex_load'] = c_load  

          # Determine load_rating
          total_load = load/1000 # kW
          load_rating, load_rating_index = helpers.get_transformer_size(
                                               total_load, 
                                               config_data['standard_transformer_ratings'], 
                                               config_data['tranformer_oversize_factor'])
          residential_dict[residential_key]['load_rating'] = load_rating

          # Deterimine load classification
          load_class = None
          if residential_dict[residential_key]['load_classification'].isdigit():
            load_class = int(residential_dict[residential_key]['load_classification'])
          else: 
            # load_classification is unknown. determine from no_houses and transformer size
            residential_dict[residential_key]['load_classification'] = None
            random_class_number = random.random()*100
            load_class = None
            cum_perc = 0
            for i, perc in enumerate([one_load_class[load_rating_index] for one_load_class in config_data['res_load_class_dists']]):
               if cum_perc < random_class_number <= cum_perc + perc:
                 load_class = i
                 break
               cum_perc += perc
            
          assert load_class is not None
          residential_dict[residential_key]['load_classification'] = load_class
          # print('Replacing {:.0f} kW with houses of type {}, on a transformer rated at {} kW.'.format(
          #     total_load,
          #     config_data["load_classifications"][load_class],
          #     load_rating))

          # Remove constant load keys
          if 'load_class' in glmCaseDict[x]:
            del glmCaseDict[x]['load_class'] # Must remove load_class as it isn't a published property

          if 'power_12' in glmCaseDict[x]:
            del glmCaseDict[x]['power_12']

          if 'power_1' in glmCaseDict[x]:
            del glmCaseDict[x]['power_1']

          residential_key += 1
    
  # Calculate some random numbers needed for TOU/CPP and DLC technologies
  if use_flags['use_market'] != 0:
    # Initialize psuedo-random seed
    random.seed(2) if config_data["fix_random_seed"] else random.seed()

    if len(residential_dict) > 0:
      # Initialize random number arrays
      market_penetration_random = []
      dlc_rand = []
      pool_pump_recovery_random = []
      slider_random = []
      comm_slider_random = []
      dlc_c_rand = []
      dlc_c_rand2 = []

      # Make a large array so we don't run out
      if len(residential_dict) > 0:
        aa = len(residential_dict)*100 # was total_house_number -- just guessing at a big enough maximum number
        for x in range(aa):
          market_penetration_random.append(random.random())
          dlc_rand.append(random.random()) # Used for dlc randomization

          # 10 - 25% increase over normal cycle
          pool_pump_recovery_random.append(0.1 + 0.15*random.random())

          # Limit slider randomization to Olypen style
          slider_random.append(random.normalvariate(0.45,0.2))
          if slider_random[x] > tech_data['market_info'][4]:
            slider_random[x] = tech_data['market_info'][4]
          if slider_random[x] < 0:
            slider_random[x] = 0

        # Random elasticity values for responsive loads - this is a multiplier
        # used to randomized individual building responsiveness - very similar
        # to a lognormal, so we'll use one that has a mean of ~1, max of
        # ~1.2, and median of ~1.12
        sigma = 1.2
        mu = 0.7
        multiplier = 3.6
        xval = []
        elasticity_random = []
        for x in range(aa):
          xval.append(random.random())
          elasticity_random.append(multiplier * math.exp(-1 / (2 * pow(sigma,2))) * pow((math.log(xval[x]) - mu),2) / (xval[x] * sigma * math.sqrt(2 * math.pi)))

      if len(commercial_dict) > 0:
        aa = len(commercial_dict)*15*100
        for x in range(aa):
          # Limit slider randomization to Olypen style
          comm_slider_random.append(random.normalvariate(0.45,0.2))
          if comm_slider_random[x] > tech_data['market_info'][4]:
            comm_slider_random[x] = tech_data['market_info'][4]
          if comm_slider_random[x] < 0:
            comm_slider_random[x] = 0

          dlc_c_rand.append(random.random())
          dlc_c_rand2.append(random.random())
      
    else:
      market_penetration_random = None
      dlc_rand = None
      pool_pump_recovery_random = None
      slider_random = None
      comm_slider_random = None
      dlc_c_rand = None
      dlc_c_rand2 = None
      xval = None
      elasticity_random = None
  else:
    market_penetration_random = None
    dlc_rand = None
    pool_pump_recovery_random = None
    slider_random = None
    comm_slider_random = None
    dlc_c_rand = None
    dlc_c_rand2 = None
    xval = None
    elasticity_random = None

  # Tack on residential loads
  solar_residential_array = [0,[],[]]
  if use_flags['use_homes'] != 0:
    if use_flags['use_normalized_loadshapes'] == 1:
      glmCaseDict, last_key = AddLoadShapes.add_normalized_residential_ziploads(glmCaseDict, residential_dict, config_data, last_key)
    else:
      glmCaseDict, solar_residential_array, ts_residential_array, last_key = ResidentialLoads.append_residential(
          glmCaseDict, use_flags, config_data, tech_data, residential_dict, last_key, CPP_flag_name,
          market_penetration_random, dlc_rand, pool_pump_recovery_random, slider_random, xval, elasticity_random, 
          io_opts['dir'], io_opts['resources_dir'])
    
  # End addition of residential loads ########################################################################################################################

  solar_office_array = [0,[],[]]
  solar_bigbox_array = [0,[],[]]
  solar_stripmall_array = [0,[],[]]
  if use_flags['use_commercial'] != 0:
    if use_flags['use_normalized_loadshapes'] == 1:
      glmCaseDict, last_key = AddLoadShapes.add_normalized_commercial_ziploads(glmCaseDict, commercial_dict, config_data, last_key)
    else:
      glmCaseDict, solar_office_array, solar_bigbox_array, solar_stripmall_array, ts_office_array, \
      ts_bigbox_array, ts_stripmall_array, last_key = CommercialLoads.append_commercial(
          glmCaseDict, use_flags, config_data, tech_data, last_key, commercial_dict, comm_slider_random, 
          dlc_c_rand, dlc_c_rand2, io_opts['dir'], io_opts['resources_dir'])
      
  # Append Solar: Call append_solar(feeder_dict, use_flags, config_file, solar_bigbox_array, solar_office_array, solar_stripmall_array, solar_residential_array, last_key)
  if use_flags['use_solar'] != 0 or use_flags['use_solar_res'] != 0 or use_flags['use_solar_com'] != 0:
    glmCaseDict = Solar_Technology.Append_Solar(glmCaseDict, use_flags, config_data, tech_data, last_key)
    
  # Append recorders
  glmCaseDict, last_key = AddTapeObjects.add_recorders(glmCaseDict, io_opts, time_opts, last_key)

  return (glmCaseDict, last_key)

