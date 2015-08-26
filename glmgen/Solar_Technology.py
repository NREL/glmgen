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
        
    # set per-building sizing factor to 100.0%, unless solar_penetration is > 100.0%, and then use that
    percent_bldg_annual_load = 100.0 if config_data['solar_penetration'] < 100.0 else config_data['solar_penetration']
                
    if (use_flags['use_solar'] != 0 or use_flags['use_solar_com'] != 0) and config_data['solar_penetration'] > 0.0:
        # ADD COMMERCIAL PV
        assert bldgs is not None
        comm_bldgs = [x for x in bldgs if x[1] > 5]
                
        for i in get_solar_indices(comm_bldgs, config_data['solar_penetration'], percent_bldg_annual_load, config_data):
            bldg = comm_bldgs[i]   
            meter_key = bldg[0]
            classID = bldg[1]            
            
            # Attach PV unit to dictionary            
            parent = PV_Tech_Dict[meter_key]['name']
            phases = PV_Tech_Dict[meter_key]['phases']
            pv_meter_name = None
            if classID > 6:
                # big box or office
                # write the PV meter
                last_key += 1
                pv_meter_name = 'pv_m_{:s}'.format(parent)
                PV_Tech_Dict[last_key] = {'object' : 'meter',
                                          'name' : pv_meter_name,
                                          'parent' : '{:s}'.format(parent),
                                          'phases' : '{:s}'.format(phases),
                                          'groupid' : 'PV_Meter'}
            else:
                # strip mall
                parent_key = PV_Tech_Dict.get_object_key_by_name(parent, 'triplex_meter')
                grandparent = PV_Tech_Dict[PV_Tech_Dict.get_parent_key(parent_key)]['name']
                
                # write the PV meter
                last_key += 1
                pv_meter_name = 'pv_tm_{:s}'.format(parent)
                PV_Tech_Dict[last_key] = {'object' : 'triplex_meter',
                                          'name' : pv_meter_name,
                                          'parent' : '{:s}'.format(grandparent),
                                          'phases' : '{:s}'.format(phases),
                                          'nominal_voltage' : '120',
                                          'groupid' : 'PV_Meter'}
                                          
            # write the PV inverter and panel
            inverter, panel = get_inverter_panel_dicts(bldg, percent_bldg_annual_load, parent, phases, pv_meter_name, config_data)
            last_key += 1
            PV_Tech_Dict[last_key] = inverter
            last_key += 1
            PV_Tech_Dict[last_key] = panel
                                                                                                    
    if (use_flags['use_solar'] != 0 or use_flags['use_solar_res'] != 0) and config_data['solar_penetration'] > 0.0:
        # ADD RESIDENTIAL PV
        assert bldgs is not None
        res_bldgs = [x for x in bldgs if x[1] < 6]
                
        for i in get_solar_indices(res_bldgs, config_data['solar_penetration'], percent_bldg_annual_load, config_data):
            bldg = res_bldgs[i]   
            meter_key = bldg[0]
            classID = bldg[1]            
            
            # Attach PV unit to dictionary            
            parent = PV_Tech_Dict[meter_key]['name']
            phases = PV_Tech_Dict[meter_key]['phases']
            parent_key = PV_Tech_Dict.get_object_key_by_name(parent, 'triplex_meter')
            grandparent = PV_Tech_Dict[PV_Tech_Dict.get_parent_key(parent_key)]['name']
                
            # write the PV meter
            last_key += 1
            pv_meter_name = 'pv_tm_{:s}'.format(parent)
            PV_Tech_Dict[last_key] = {'object' : 'triplex_meter',
                                      'name' : pv_meter_name,
                                      'parent' : '{:s}'.format(grandparent),
                                      'phases' : '{:s}'.format(phases),
                                      'nominal_voltage' : '120',
                                      'groupid' : 'PV_Meter'}
                                          
            # write the PV inverter and panel
            inverter, panel = get_inverter_panel_dicts(bldg, percent_bldg_annual_load, parent, phases, pv_meter_name, config_data)
            last_key += 1
            PV_Tech_Dict[last_key] = inverter
            last_key += 1
            PV_Tech_Dict[last_key] = panel
            
    return PV_Tech_Dict
    
def get_solar_indices(bldgs, solar_penetration, percent_bldg_annual_load, config_data):
    # randomize list of indices
    random_index = random.sample(list(range(len(bldgs))), len(bldgs))
        
    # determine how many buildings should have systems
    annual_loads = []
    solar_gen = []
    cum_solar_gen = []
    for i in random_index:
        annual_loads.append(config_data['annual_load_intensities'][bldgs[i][1]] * bldgs[i][2])
        solar_gen.append(annual_loads[-1] * percent_bldg_annual_load / 100.0)
        if len(cum_solar_gen) == 0:
            cum_solar_gen.append(solar_gen[-1])
        else:
            cum_solar_gen.append(cum_solar_gen[-1] + solar_gen[-1])
    target = sum(annual_loads) * solar_penetration / 100.0
    abs_err = [abs(x - target) for x in cum_solar_gen]
    i = -1; val = None
    if len(abs_err) > 0:
        i, val = min(enumerate(abs_err), key = lambda p: p[1])
    num_solar = i + 1
    inds = random_index[:num_solar]
    #print('Total load: {:.0f} MWh'.format(sum(annual_loads) / 1000.0))
    #print('Solar penetration: {}%'.format(config_data['solar_penetration']))
    #print('Single building penetration: {}%'.format(percent_bldg_annual_load))
    #print('Target solar generation: {:.0f} MWh'.format(target / 1000.0))
    #print('Cumulative solar: {}'.format(cum_solar_gen))
    #print('Absolute errors compared to target: {}'.format(abs_err))
    #print('Num solar systems to make: {}'.format(num_solar))
    #print('Keeping indices: {}'.format(inds))
    assert len(inds) == num_solar
    return inds
    
def get_inverter_panel_dicts(bldg, percent_bldg_annual_load, parent, phases, pv_meter_name, config_data):
    classID = bldg[1]
    floor_area = bldg[2]

    cell_efficiency = 0.2
    orientation_azimuth = 90.0 + random.random() * 180.0
    tilt_angle = random.random() * 50.0
    capacity_factor = config_data['pv_cf']
    desired_solar_gen = config_data['annual_load_intensities'][classID] * floor_area * percent_bldg_annual_load / 100.0 # kWh
    solar_rating = desired_solar_gen * 1000.0 / (capacity_factor * 8760.0) # W
    panel_area = round(solar_rating / (92.902 * cell_efficiency)) # standard conditions are 92.902 W/ft^2
    power_factor = config_data['inverter_power_factor']
    
    inverter = {'object' : 'inverter',
                'name' : 'pv_inv_{:s}'.format(parent),
                'parent' : pv_meter_name,
                'phases' : '{:s}'.format(phases),
                'generator_mode' : 'CONSTANT_PF',
                'generator_status' : 'ONLINE',
                'inverter_type' : 'PWM',
                'power_factor' : '{:.4f}'.format(power_factor),
                'inverter_efficiency' : '0.95',
                'rated_power' : '{:.0f}'.format(math.ceil(solar_rating))}
                                                  
    panel = {'object' : 'solar',
             'name' : 'pv_{:s}'.format(parent),
             'parent' : 'pv_inv_{:s}'.format(parent),
             'generator_mode' : 'SUPPLY_DRIVEN',
             'generator_status' : 'ONLINE',
             'panel_type' : 'SINGLE_CRYSTAL_SILICON',
             'efficiency' : '{:.4f}'.format(cell_efficiency),
             'area' : '{:.0f}'.format(panel_area),
             'orientation': 'FIXED_AXIS',
             'tilt_angle': '{:.2f}'.format(tilt_angle),
             'orientation_azimuth': '{:.2f}'.format(orientation_azimuth)}

    return inverter, panel             
            
def main():
    #tests here
    pass
    #PVGLM = Append_Solar(PV_Tech_Dict,use_flags,)
    
if __name__ ==  '__main__':
    main()