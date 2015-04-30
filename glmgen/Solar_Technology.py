from __future__ import division
import math
import random

def Append_Solar(PV_Tech_Dict, use_flags, config_data, tech_data, last_key, 
                 solar_bigbox_array=None, solar_office_array=None, 
                 solar_stripmall_array=None, solar_residential_array=None):
    # PV_Tech_Dict - the dictionary that we add solar objects to
    # use_flags - the output from TechnologyParameters.py
    # config_data - the output from Configuration.py
    # solar_bigbox_array - contains a list of commercial houses, corresponding floor areas, parents,and phases that commercial PV can be attached to
    # solar_office_array - contains a list of commercial houses, corresponding floor areas, parents,and phases that commercial PV can be attached to
    # solar_stripmall_array - contains a list of commercial houses, corresponding floor areas, parents,and phases that commercial PV can be attached to
    # solar_residential_array - contains a list of residential houses, corresponding floor areas, parents,and phases that residential PV can be attached to
    # last_key should be a numbered key that is the next key in PV_Tech_Dict
    last_key = PV_Tech_Dict.last_key()
    
    # Initialize psuedo-random seed
    random.seed(4) if config_data["fix_random_seed"] else random.seed()
            
    # Populating solar as percentage of feeder peak load
    # Add Commercial PV
    if use_flags['use_solar'] != 0 or use_flags['use_solar_com'] != 0:
        # Initialize psuedo-random seed
        random.seed(4) if config_data["fix_random_seed"] else random.seed()
        
        # solar_penetration should apply equally to all solar-eligible building types
        penetration_stripmall = config_data['solar_penetration']
        penetration_bigbox = config_data['solar_penetration']
        penetration_office = config_data['solar_penetration']
        if solar_stripmall_array is None:
            penetration_stripmall = 0
        if solar_bigbox_array is None:
            penetration_bigbox = 0
        if solar_office_array is None: 
            penetration_office = 0
            
        solar_rating = config_data['solar_rating'] * 1000 # Convert kW to W
        #Determine total number of PV we must add to office
        if penetration_office > 0:    # solar_office_array = list(number of office meters attached to com loads,list(office meter names attached to loads),list(phases of office meters attached to loads))
            # TODO: Better implementation of solar_penetration
            # 'emissions_peak' is not tied to the actual feeder, and is not an energy-based penetration.
            # penetration_* is also in % units, so should be divided by 100        
            # total_office_pv_units = math.ceil((config_data['emissions_peak'] * penetration_office) / tech_data['solar_averagepower_office'])
            total_office_pv_units = int(math.ceil(solar_office_array[0] * penetration_office / 100.0))
            total_office_number = int(solar_office_array[0])
                        
            # Create a randomized list of numbers 0 to total_office_number
            random_index = []
            random_index = random.sample(list(range(total_office_number)),
                                         total_office_number);
            
            # Determine how many units to attach to each office building
            pv_units_per_office = int(math.ceil(total_office_pv_units / total_office_number)) if total_office_number > 0 else 0
            
            # Attach PV units to dictionary
            pv_unit = 0
            floor_area = round(solar_rating / (92.902 * 0.20))
            
            for x in range(total_office_number):
                parent = solar_office_array[1][random_index[x]]
                phases = solar_office_array[2][random_index[x]]
                pv_unit = pv_unit + pv_units_per_office
                
                if pv_unit < total_office_number:
                    if pv_units_per_office > (total_office_number - pv_unit - 1):
                        pv_units_per_office = total_office_number - pv_unit - 1
                        
                    for y in range(0,pv_units_per_office):
                        # Write the PV meter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'meter',
                                                  'name' : 'pv_meter{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(parent),
                                                  'phases' : '{:s}'.format(phases),
                                                  'nominal_voltage' : '{:f}'.format(config_data['nom_volt2']),
                                                  'groupid' : 'PV_Meter'}
                        
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'inverter',
                                                  # 'name' : 'pv_inverter_{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'name' : 'pv_inverter{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'phases' : '{:s}'.format(phases),
                                                  'generator_mode' : 'CONSTANT_PF',
                                                  'generator_status' : 'ONLINE',
                                                  'inverter_type' : 'PWM',
                                                  'power_factor' : '1.0',
                                                  'inverter_efficiency' : '0.9',
                                                  'rated_power' : '{:.0f}'.format(math.ceil(solar_rating))}
                                                  
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'solar',
                                                  # 'name' : 'sol_panel_{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'name' : 'pv_panel{:d}_{:s}'.format(y, parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'generator_mode' : 'SUPPLY_DRIVEN',
                                                  'generator_status' : 'ONLINE',
                                                  'panel_type' : 'SINGLE_CRYSTAL_SILICON',
                                                  'efficiency' : '0.2',
                                                  'area' : '{:.0f}'.format(floor_area)}
        
        # Determine total number of PV we must add to bigbox commercial
        if penetration_bigbox > 0:    # solar_bigbox_array = list(number of bigbox meters attached to com loads,list(bigbox meter names attached to loads),list(phases of bigbox meters attached to loads))
            # TODO: Better implementation of solar_penetration
            # 'emissions_peak' is not tied to the actual feeder, and is not an energy-based penetration.
            # penetration_* is also in % units, so should be divided by 100
            # total_bigbox_pv_units = math.ceil((config_data['emissions_peak'] * penetration_bigbox) / tech_data['solar_averagepower_bigbox'])
            total_bigbox_pv_units = math.ceil(solar_bigbox_array[0] * penetration_bigbox / 100.0)
            total_bigbox_number = int(solar_bigbox_array[0])
                        
            # Create a randomized list of numbers 0 to total_bigbox_number
            random_index = []
            random_index = random.sample(list(range(total_bigbox_number)),
                                         total_bigbox_number);
            
            # Determine how many units to attach to each bigbox building
            pv_units_per_bigbox = int(math.ceil(total_bigbox_pv_units / total_bigbox_number)) if total_bigbox_number > 0 else 0
            
            # Attach PV units to dictionary
            pv_unit = 0
            floor_area = round(solar_rating / (92.902 * 0.20))
            
            for x in range(total_bigbox_number):
                parent = solar_bigbox_array[1][random_index[x]]
                phases = solar_bigbox_array[2][random_index[x]]
                pv_unit = pv_unit + pv_units_per_bigbox
                
                if pv_unit < total_bigbox_number:
                    if pv_units_per_bigbox > (total_bigbox_number - pv_unit - 1):
                        pv_units_per_bigbox = total_bigbox_number - pv_unit - 1
                        
                    for y in range(pv_units_per_bigbox):
                        # Write the PV meter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'meter',
                                                  'name' : 'pv_meter{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(parent),
                                                  'phases' : '{:s}'.format(phases),
                                                  'nominal_voltage' : '{:f}'.format(config_data['nom_volt2']),
                                                  'groupid' : 'PV_Meter'}
                        
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'inverter',
                                                  # 'name' : 'pv_inverter_{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'name' : 'pv_inverter{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'phases' : '{:s}'.format(phases),
                                                  'generator_mode' : 'CONSTANT_PF',
                                                  'generator_status' : 'ONLINE',
                                                  'inverter_type' : 'PWM',
                                                  'power_factor' : '1.0',
                                                  'inverter_efficiency' : '0.9',
                                                  'rated_power' : '{:.0f}'.format(math.ceil(solar_rating))}
                                                  
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'solar',
                                                  # 'name' : 'sol_panel_{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'name' : 'pv_panel{:d}_{:s}'.format(y, parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'generator_mode' : 'SUPPLY_DRIVEN',
                                                  'generator_status' : 'ONLINE',
                                                  'panel_type' : 'SINGLE_CRYSTAL_SILICON',
                                                  'efficiency' : '0.2',
                                                  'area' : '{:.0f}'.format(floor_area)}
            
        # Determine total number of PV we must add to stripmall commercial
        if penetration_stripmall > 0:    # solar_stripmall_array = list(number of stripmall meters attached to com loads,list(stripmall meter names attached to loads),list(phases of stripmall meters attached to loads))
            # TODO: Better implementation of solar_penetration
            # 'emissions_peak' is not tied to the actual feeder, and is not an energy-based penetration.
            # penetration_* is also in % units, so should be divided by 100
            # total_stripmall_pv_units = math.ceil((config_data['emissions_peak'] * penetration_stripmall) / tech_data['solar_averagepower_stripmall'])
            total_stripmall_pv_units = math.ceil(solar_stripmall_array[0] * penetration_stripmall / 100.0)
            total_stripmall_number = int(solar_stripmall_array[0])
            
            # Create a randomized list of numbers 0 to total_stripmall_number
            random_index = []
            random_index = random.sample(list(range(total_stripmall_number)),
                                         total_stripmall_number);
            
            # Determine how many units to attach to each stripmall building
            pv_units_per_stripmall = int(math.ceil(total_stripmall_pv_units / total_stripmall_number)) if total_stripmall_number > 0 else 0
            
            # Attach PV units to dictionary
            pv_unit = 0
            floor_area = round(solar_rating / (92.902 * 0.20))
            
            for x in range(total_stripmall_number):
                parent = solar_stripmall_array[1][random_index[x]] # house triplex_meter
                parent_key = PV_Tech_Dict.get_object_key_by_name(parent, 'triplex_meter')
                grandparent = PV_Tech_Dict[PV_Tech_Dict.get_parent_key(parent_key)]['name']
                phases = solar_stripmall_array[2][random_index[x]]
                pv_unit = pv_unit + pv_units_per_stripmall
                
                if pv_unit < total_stripmall_number:
                    if pv_units_per_stripmall > (total_stripmall_number - pv_unit - 1):
                        pv_units_per_stripmall = total_stripmall_number - pv_unit - 1
                        
                    for y in range(pv_units_per_stripmall):
                        # ETH: The house triplex_meter is hooked into another triplex_meter, but 
                        # GridLAB-D does not appear to allow a chain of three triplex meters. 
                        # Originally, the triplex_meter for the PV was parented by the house 
                        # triplex_meter; instead, to get a feasible model, have the PV triplex_meter
                        # parented by the house's triplex_meter's parent (the 'grandparent'). 
                        
                        # Write the PV meter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'triplex_meter',
                                                  'name' : 'pv_triplex_meter{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(grandparent),
                                                  'phases' : '{:s}'.format(phases),
                                                  'nominal_voltage' : '120',
                                                  'groupid' : 'PV_Meter'}
                        
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'inverter',
                                                  # 'name' : 'pv_inverter_{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'name' : 'pv_inverter{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'parent' : '{:s}'.format(parent),
                                                  'phases' : '{:s}'.format(phases),
                                                  'generator_mode' : 'CONSTANT_PF',
                                                  'generator_status' : 'ONLINE',
                                                  'inverter_type' : 'PWM',
                                                  'power_factor' : '1.0',
                                                  'inverter_efficiency' : '0.9',
                                                  'rated_power' : '{:.0f}'.format(math.ceil(solar_rating))}
                                                  
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'solar',
                                                  # 'name' : 'sol_panel_{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'name' : 'pv_panel{:d}_{:s}'.format(y, parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'generator_mode' : 'SUPPLY_DRIVEN',
                                                  'generator_status' : 'ONLINE',
                                                  'panel_type' : 'SINGLE_CRYSTAL_SILICON',
                                                  'efficiency' : '0.2',
                                                  'area' : '{:.0f}'.format(floor_area)}
            
    # Add Residential PV
    if use_flags['use_solar'] != 0 or use_flags['use_solar_res'] != 0:
        # Initialize psuedo-random seed
        random.seed(5) if config_data["fix_random_seed"] else random.seed()
        
        solar_rating = config_data['solar_rating']*1000 #Convert kW to W
        # Determine solar penetrations for residential
        if solar_residential_array != None:
            residential_penetration = config_data['solar_penetration']
        else:
            residential_penetration = 0
            
        # Determine total number of PV we must add to residential houses
        if residential_penetration > 0:    # solar_residential_array = list(number of residential triplex_meters attached to com loads,list(residential triplex_meter names attached to loads),list(phases of residential triplex_meters attached to loads))
            # TODO: Better implementation of solar_penetration
            # 'emissions_peak' is not tied to the actual feeder, and is not an energy-based penetration.
            # penetration_* is also in % units, so should be divided by 100
            # total_residential_pv_units = math.ceil((config_data['emissions_peak'] * residential_penetration) / tech_data['solar_averagepower_residential'])
            total_residential_pv_units = math.ceil(solar_residential_array[0] * residential_penetration / 100.0)
            total_residential_number = int(solar_residential_array[0])
            
            # Create a randomized list of numbers 0 to total_residential_number
            random_index = []
            random_index = random.sample(list(range(total_residential_number)),
                                         total_residential_number);
            
            # Determine how many units to attach to each residential house
            pv_units_per_residential = int(math.ceil(total_residential_pv_units / total_residential_number)) if total_residential_number > 0 else 0
            
            # Attach PV units to dictionary
            pv_unit = 0
            floor_area = round(solar_rating / (92.902 * 0.20))
            
            for x in range(total_residential_number):
                parent = solar_residential_array[1][random_index[x]]
                parent_key = PV_Tech_Dict.get_object_key_by_name(parent, 'triplex_meter')
                grandparent = PV_Tech_Dict[PV_Tech_Dict.get_parent_key(parent_key)]['name']
                phases = solar_residential_array[2][random_index[x]]
                pv_unit = pv_unit + pv_units_per_residential
                
                if pv_unit < total_residential_number:
                    if pv_units_per_residential > (total_residential_number - pv_unit - 1):
                        pv_units_per_residential = total_residential_number - pv_unit - 1
                        
                    for y in range(pv_units_per_residential):
                        # ETH: The house triplex_meter is hooked into another triplex_meter, but 
                        # GridLAB-D does not appear to allow a chain of three triplex meters. 
                        # Originally, the triplex_meter for the PV was parented by the house 
                        # triplex_meter; instead, to get a feasible model, have the PV triplex_meter
                        # parented by the house's triplex_meter's parent (the 'grandparent'). 
                        
                        # Write the PV meter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'triplex_meter',
                                                  'name' : 'pv_triplex_meter{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(grandparent),
                                                  'phases' : '{:s}'.format(phases),
                                                  'nominal_voltage' : '120',
                                                  'groupid' : 'PV_Meter'}
                        
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'inverter',
                        #                           'name' : 'pv_inverter_{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'name' : 'pv_inverter{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'phases' : '{:s}'.format(phases),
                                                  'generator_mode' : 'CONSTANT_PF',
                                                  'generator_status' : 'ONLINE',
                                                  'inverter_type' : 'PWM',
                                                  'power_factor' : '1.0',
                                                  'inverter_efficiency' : '0.9',
                                                  'rated_power' : '{:.0f}'.format(math.ceil(solar_rating))}
                                                  
                        # Write the PV panel
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'solar',
                                                  # 'name' : 'sol_panel_{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'name' : 'pv_panel{:d}_{:s}'.format(y, parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'generator_mode' : 'SUPPLY_DRIVEN',
                                                  'generator_status' : 'ONLINE',
                                                  'panel_type' : 'SINGLE_CRYSTAL_SILICON',
                                                  'efficiency' : '0.2',
                                                  'area' : '{:.0f}'.format(floor_area)}
            
    return PV_Tech_Dict
            
def main():
    #tests here
    pass
    #PVGLM = Append_Solar(PV_Tech_Dict,use_flags,)
    
if __name__ ==  '__main__':
    main()