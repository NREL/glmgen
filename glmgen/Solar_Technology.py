from __future__ import division

from glmgen import helpers

import math
import random

def Append_Solar(PV_Tech_Dict, use_flags, config_data, tech_data, last_key):
    # PV_Tech_Dict - the dictionary that we add solar objects to
    # use_flags - the output from TechnologyParameters.py
    # config_data - the output from Configuration.py
    # last_key should be a numbered key that is the next key in PV_Tech_Dict
    last_key = PV_Tech_Dict.last_key()
    
    # Initialize psuedo-random seed
    random.seed(4) if config_data["fix_random_seed"] else random.seed()
    
    bldgs = None
    if (use_flags['use_solar'] != 0 or use_flags['use_solar_com'] != 0 or use_flags['use_solar_res'] != 0) \
       and config_data['solar_penetration'] > 0.0:
        # list of tuples, ((triplex_)meter_key, classID, floor_area)
        bldgs = helpers.get_buildings(PV_Tech_Dict)
                
    if (use_flags['use_solar'] != 0 or use_flags['use_solar_com'] != 0) and config_data['solar_penetration'] > 0.0:
        # ADD COMMERCIAL PV
        assert bldgs is not None
        comm_bldgs = [x for x in bldgs where x[1] > 5]
        
        # randomize list of indices
        random_index = random.sample(list(range(len(comm_bldgs))), len(comm_bldgs))
        
        # set per-building sizing factor to 100.0%, unless solar_penetration is > 100.0%, and then use that
        percent_bldg_annual_load = 100.0 if config_data['solar_penetration'] < 100.0 else config_data['solar_penetration']
        
        # determine how many buildings should have systems
        annual_loads = []
        solar_gen = []
        cum_solar_gen = []
        for i in random_index:
            annual_loads.append(config_data['annual_load_intensities'][comm_bldgs[i][1]] * comm_bldgs[i][2])
            solar_gen.append(annual_loads[-1] * percent_bldg_annual_load / 100.0)
            if cum_solar_gen.empty:
                cum_solar_gen.append(solar_gen[-1])
            else:
                cum_solar_gen.append(cum_solar_gen[-1] + solar_gen[-1])
        target = sum(annual_loads) * config_data['solar_penetration'] / 100.0
        abs_err = [abs(x - target) for x in cum_solar_gen]
        i, val = min(enumerate(abs_err), key = lambda p: p[1])
        num_solar = i + 1
        print('Total commercial load: {:.0f} MWh'.format(sum(annual_loads) / 1000.0))
        print('Solar penetration: {}%'.format(config_data['solar_penetration']))
        print('Single building penetration: {}%'.format(percent_bldg_annual_load))
        print('Target solar generation: {:.0f} MWh'.format(target / 1000.0))
        print('Cumulative solar: {}'.format(cum_solar_gen))
        print('Absolute errors compared to target: {}'.format(abs_err))
        print('Num solar systems to make: {}'.format(num_solar))
                
        for i in range(num_solar):
            bldg = comm_bldgs[random_index[i]]        
            
        solar_rating = config_data['solar_rating'] * 1000 # Convert kW to W
        #Determine total number of PV we must add to office
        if penetration_office > 0:    # solar_office_array = list(number of office meters attached to com loads,list(office meter names attached to loads),list(phases of office meters attached to loads))
            # TODO: Better implementation of solar_penetration
            # 'emissions_peak' is not tied to the actual feeder, and is not an energy-based penetration.
            # penetration_* is also in % units, so should be divided by 100        
            # total_office_pv_units = math.ceil((config_data['emissions_peak'] * penetration_office) / tech_data['solar_averagepower_office'])
            total_office_pv_units = int(math.ceil(float(solar_office_array[0]) * penetration_office / 100.0))
            total_office_number = int(solar_office_array[0])
            
            # print("Num offices: {}, solar penetration: {}, num expected PV units: {}".format(
            #     total_office_number, penetration_office, total_office_pv_units))
            
            # Create a randomized list of numbers 0 to total_office_number
            random_index = []
            random_index = random.sample(list(range(total_office_number)),
                                         total_office_number);
            
            # Determine how many units to attach to each office building
            pv_units_per_office = int(math.ceil(total_office_pv_units / total_office_number)) if total_office_number > 0 else 0
            
            # print("Units per = {}".format(pv_units_per_office))
            
            # Attach PV units to dictionary
            pv_unit = 0
            floor_area = round(solar_rating / (92.902 * 0.20))
            # randomize
            #   - cell efficiency
            #   - orientation_azimuth [deg]
            #   - tilt_angle [deg]
            # size based on avg. CF, and avg. kWh/ft^2 by building class
            
            
            for x in range(total_office_number):
                parent = solar_office_array[1][random_index[x]]
                phases = solar_office_array[2][random_index[x]]
                
                if pv_unit < total_office_pv_units:
                        
                    for y in range(0,pv_units_per_office):
                        # Write the PV meter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'meter',
                                                  'name' : 'pv_m{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(parent),
                                                  'phases' : '{:s}'.format(phases),
                                                  # 'nominal_voltage' : '{:f}'.format(config_data['nom_volt2']),
                                                  'groupid' : 'PV_Meter'}
                        
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'inverter',
                                                  'name' : 'pv_inv{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'phases' : '{:s}'.format(phases),
                                                  'generator_mode' : 'CONSTANT_PF',
                                                  'generator_status' : 'ONLINE',
                                                  'inverter_type' : 'PWM',
                                                  'power_factor' : '1.0',
                                                  'inverter_efficiency' : '0.95',
                                                  'rated_power' : '{:.0f}'.format(math.ceil(solar_rating))}
                                                  
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'solar',
                                                  'name' : 'pv{:d}_{:s}'.format(y, parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'generator_mode' : 'SUPPLY_DRIVEN',
                                                  'generator_status' : 'ONLINE',
                                                  'panel_type' : 'SINGLE_CRYSTAL_SILICON',
                                                  'efficiency' : '0.2',
                                                  'area' : '{:.0f}'.format(floor_area)}
                                                  
                        pv_unit += 1
                        if pv_unit >= total_office_pv_units:
                            break
                              
                    if pv_unit >= total_office_pv_units:
                        break
                              
            # print('Added {} PV units.'.format(pv_unit))  
        
        # Determine total number of PV we must add to bigbox commercial
        if penetration_bigbox > 0:    # solar_bigbox_array = list(number of bigbox meters attached to com loads,list(bigbox meter names attached to loads),list(phases of bigbox meters attached to loads))
            # TODO: Better implementation of solar_penetration
            # 'emissions_peak' is not tied to the actual feeder, and is not an energy-based penetration.
            # penetration_* is also in % units, so should be divided by 100
            # total_bigbox_pv_units = math.ceil((config_data['emissions_peak'] * penetration_bigbox) / tech_data['solar_averagepower_bigbox'])
            total_bigbox_pv_units = math.ceil(solar_bigbox_array[0] * penetration_bigbox / 100.0)
            total_bigbox_number = int(solar_bigbox_array[0])
            
            # print("Num big boxes: {}, solar penetration: {}, num expected PV units: {}".format(
            #     total_bigbox_number, penetration_bigbox, total_bigbox_pv_units))
            
            # Create a randomized list of numbers 0 to total_bigbox_number
            random_index = []
            random_index = random.sample(list(range(total_bigbox_number)),
                                         total_bigbox_number);
            
            # Determine how many units to attach to each bigbox building
            pv_units_per_bigbox = int(math.ceil(total_bigbox_pv_units / total_bigbox_number)) if total_bigbox_number > 0 else 0
            
            # print("Units per = {}".format(pv_units_per_bigbox))
            
            # Attach PV units to dictionary
            pv_unit = 0
            floor_area = round(solar_rating / (92.902 * 0.20))
            
            for x in range(total_bigbox_number):
                parent = solar_bigbox_array[1][random_index[x]]
                phases = solar_bigbox_array[2][random_index[x]]
                
                if pv_unit < total_bigbox_pv_units:
                        
                    for y in range(pv_units_per_bigbox):
                        # Write the PV meter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'meter',
                                                  'name' : 'pv_m{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(parent),
                                                  'phases' : '{:s}'.format(phases),
                                                  # 'nominal_voltage' : '{:f}'.format(config_data['nom_volt2']),
                                                  'groupid' : 'PV_Meter'}
                        
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'inverter',
                                                  'name' : 'pv_inv{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'phases' : '{:s}'.format(phases),
                                                  'generator_mode' : 'CONSTANT_PF',
                                                  'generator_status' : 'ONLINE',
                                                  'inverter_type' : 'PWM',
                                                  'power_factor' : '1.0',
                                                  'inverter_efficiency' : '0.95',
                                                  'rated_power' : '{:.0f}'.format(math.ceil(solar_rating))}
                                                  
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'solar',
                                                  'name' : 'pv{:d}_{:s}'.format(y, parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'generator_mode' : 'SUPPLY_DRIVEN',
                                                  'generator_status' : 'ONLINE',
                                                  'panel_type' : 'SINGLE_CRYSTAL_SILICON',
                                                  'efficiency' : '0.2',
                                                  'area' : '{:.0f}'.format(floor_area)}
                                                  
                        pv_unit += 1
                        if pv_unit >= total_bigbox_pv_units:
                            break
                              
                    if pv_unit >= total_bigbox_pv_units:
                        break
                              
            # print('Added {} PV units.'.format(pv_unit))  
                                                  
        # Determine total number of PV we must add to stripmall commercial
        if penetration_stripmall > 0:    # solar_stripmall_array = list(number of stripmall meters attached to com loads,list(stripmall meter names attached to loads),list(phases of stripmall meters attached to loads))
            # TODO: Better implementation of solar_penetration
            # 'emissions_peak' is not tied to the actual feeder, and is not an energy-based penetration.
            # penetration_* is also in % units, so should be divided by 100
            # total_stripmall_pv_units = math.ceil((config_data['emissions_peak'] * penetration_stripmall) / tech_data['solar_averagepower_stripmall'])
            total_stripmall_pv_units = math.ceil(solar_stripmall_array[0] * penetration_stripmall / 100.0)
            total_stripmall_number = int(solar_stripmall_array[0])
            
            # print("Num strip malls: {}, solar penetration: {}, num expected PV units: {}".format(
            #     total_stripmall_number, penetration_stripmall, total_stripmall_pv_units))
            
            # Create a randomized list of numbers 0 to total_stripmall_number
            random_index = []
            random_index = random.sample(list(range(total_stripmall_number)),
                                         total_stripmall_number);
            
            # Determine how many units to attach to each stripmall building
            pv_units_per_stripmall = int(math.ceil(total_stripmall_pv_units / total_stripmall_number)) if total_stripmall_number > 0 else 0
            
            # print("Units per = {}".format(pv_units_per_stripmall))
            
            # Attach PV units to dictionary
            pv_unit = 0
            floor_area = round(solar_rating / (92.902 * 0.20))
            
            for x in range(total_stripmall_number):
                parent = solar_stripmall_array[1][random_index[x]] # house triplex_meter
                parent_key = PV_Tech_Dict.get_object_key_by_name(parent, 'triplex_meter')
                grandparent = PV_Tech_Dict[PV_Tech_Dict.get_parent_key(parent_key)]['name']
                phases = solar_stripmall_array[2][random_index[x]]
                
                if pv_unit < total_stripmall_pv_units:
                        
                    for y in range(pv_units_per_stripmall):
                        # ETH: The house triplex_meter is hooked into another triplex_meter, but 
                        # GridLAB-D does not appear to allow a chain of three triplex meters. 
                        # Originally, the triplex_meter for the PV was parented by the house 
                        # triplex_meter; instead, to get a feasible model, have the PV triplex_meter
                        # parented by the house's triplex_meter's parent (the 'grandparent'). 
                        
                        # Write the PV meter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'triplex_meter',
                                                  'name' : 'pv_tm{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(grandparent),
                                                  'phases' : '{:s}'.format(phases),
                                                  'nominal_voltage' : '120',
                                                  'groupid' : 'PV_Meter'}
                        
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'inverter',
                                                  # 'name' : 'pv_inverter_{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'name' : 'pv_inv{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'phases' : '{:s}'.format(phases),
                                                  'generator_mode' : 'CONSTANT_PF',
                                                  'generator_status' : 'ONLINE',
                                                  'inverter_type' : 'PWM',
                                                  'power_factor' : '1.0',
                                                  'inverter_efficiency' : '0.95',
                                                  'rated_power' : '{:.0f}'.format(math.ceil(solar_rating))}
                                                  
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'solar',
                                                  'name' : 'pv{:d}_{:s}'.format(y, parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'generator_mode' : 'SUPPLY_DRIVEN',
                                                  'generator_status' : 'ONLINE',
                                                  'panel_type' : 'SINGLE_CRYSTAL_SILICON',
                                                  'efficiency' : '0.2',
                                                  'area' : '{:.0f}'.format(floor_area)}
                                                  
                        pv_unit += 1
                        if pv_unit >= total_stripmall_pv_units:
                            break
                              
                    if pv_unit >= total_stripmall_pv_units:
                        break
                              
            # print('Added {} PV units.'.format(pv_unit))  
                                                  
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
            
            # print("Num residences: {}, solar penetration: {}, num expected PV units: {}".format(
            #     total_residential_number, residential_penetration, total_residential_pv_units))
            
            # Create a randomized list of numbers 0 to total_residential_number
            random_index = []
            random_index = random.sample(list(range(total_residential_number)),
                                         total_residential_number);
            
            # Determine how many units to attach to each residential house
            pv_units_per_residential = int(math.ceil(total_residential_pv_units / total_residential_number)) if total_residential_number > 0 else 0
            
            # print("Units per = {}".format(pv_units_per_residential))
            
            # Attach PV units to dictionary
            pv_unit = 0
            floor_area = round(solar_rating / (92.902 * 0.20))
            
            for x in range(total_residential_number):
                parent = solar_residential_array[1][random_index[x]]
                parent_key = PV_Tech_Dict.get_object_key_by_name(parent, 'triplex_meter')
                grandparent = PV_Tech_Dict[PV_Tech_Dict.get_parent_key(parent_key)]['name']
                phases = solar_residential_array[2][random_index[x]]
                
                if pv_unit < total_residential_pv_units:
                        
                    for y in range(pv_units_per_residential):
                        # ETH: The house triplex_meter is hooked into another triplex_meter, but 
                        # GridLAB-D does not appear to allow a chain of three triplex meters. 
                        # Originally, the triplex_meter for the PV was parented by the house 
                        # triplex_meter; instead, to get a feasible model, have the PV triplex_meter
                        # parented by the house's triplex_meter's parent (the 'grandparent'). 
                        
                        # Write the PV meter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'triplex_meter',
                                                  'name' : 'pv_tm{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(grandparent),
                                                  'phases' : '{:s}'.format(phases),
                                                  'nominal_voltage' : '120',
                                                  'groupid' : 'PV_Meter'}
                        
                        # Write the PV inverter
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'inverter',
                                                  'name' : 'pv_inv{:d}_{:s}'.format(y,parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'phases' : '{:s}'.format(phases),
                                                  'generator_mode' : 'CONSTANT_PF',
                                                  'generator_status' : 'ONLINE',
                                                  'inverter_type' : 'PWM',
                                                  'power_factor' : '1.0',
                                                  'inverter_efficiency' : '0.95',
                                                  'rated_power' : '{:.0f}'.format(math.ceil(solar_rating))}
                                                  
                        # Write the PV panel
                        last_key += 1
                        PV_Tech_Dict[last_key] = {'object' : 'solar',
                                                  'name' : 'pv{:d}_{:s}'.format(y, parent),
                                                  'parent' : '{:s}'.format(PV_Tech_Dict[last_key-1]['name']),
                                                  'generator_mode' : 'SUPPLY_DRIVEN',
                                                  'generator_status' : 'ONLINE',
                                                  'panel_type' : 'SINGLE_CRYSTAL_SILICON',
                                                  'efficiency' : '0.2',
                                                  'area' : '{:.0f}'.format(floor_area)}
                                                  
                        pv_unit += 1
                        if pv_unit >= total_residential_pv_units:
                            break
                              
                    if pv_unit >= total_residential_pv_units:
                        break
                              
            # print('Added {} PV units.'.format(pv_unit))
            
    return PV_Tech_Dict
            
def main():
    #tests here
    pass
    #PVGLM = Append_Solar(PV_Tech_Dict,use_flags,)
    
if __name__ ==  '__main__':
    main()