'''
Created on Jun 7, 2013

@author: fish334
'''

def add_recorders(recorder_dict, io_opts, time_opts, last_key=0):

    # check if last_key is already in glm dictionary
    def unused_key(last_key):
        if last_key in recorder_dict.keys():
            while last_key in recorder_dict.keys():
                last_key += 1
        return last_key
    
    # determine what needs to be recorded
    have_resp_zips = 0
    have_unresp_zips = 0
    have_waterheaters = 0
    have_lights = 0
    have_plugs = 0
    have_gas_waterheaters = 0
    have_occupancy = 0
    have_solar_meter = 0
    have_solar_triplex_meter = 0
    swing_node = None
    climate_name = None
    for x in recorder_dict.keys():
        if 'object' in recorder_dict[x].keys():
            if recorder_dict[x]['object'] == 'transformer' and recorder_dict[x]['name'] == 'substation_transformer':
                swing_node = recorder_dict[x]['to']
                
            if recorder_dict[x]['object'] == 'climate':
                climate_name = recorder_dict[x]['name']
                
            if recorder_dict[x]['object'] == 'ZIPload':
                if 'groupid' in recorder_dict[x].keys():
                    if recorder_dict[x]['groupid'] == 'Responsive_load':
                        have_resp_zips = 1
                        
                    if recorder_dict[x]['groupid'] == 'Unresponsive_load':
                        have_unresp_zips = 1
                        
                    if recorder_dict[x]['groupid'] == 'Gas_waterheater':
                        have_gas_waterheaters = 1
                    
                    if recorder_dict[x]['groupid'] == 'Occupancy':
                        have_occupancy = 1
                
            if recorder_dict[x]['object'] == 'waterheater':
                have_waterheaters = 1
                
            if recorder_dict[x]['object'] == 'meter':
                if 'groupid' in recorder_dict[x]:
                    if recorder_dict[x]['groupid'] == 'PV_Meter':
                        have_solar_meter = 1
                        
            if recorder_dict[x]['object'] == 'triplex_meter':
                if 'groupid' in recorder_dict[x]:
                    if recorder_dict[x]['groupid'] == 'PV_Meter':
                        have_solar_triplex_meter = 1
                        
    def add_recorder(name,rec_type,common_data,last_key):
        common_data.update( { 'interval' : time_opts['rec_interval'].total_seconds(),
                              'limit' :    time_opts['rec_limit'] } )
        if io_opts['output_type'] == 'csv':
            recorder_dict[last_key] = { 'object': 'tape.{}'.format(rec_type),
                                        'file': 'csv_output/{}.csv'.format(name) }
            recorder_dict[last_key].update(common_data)
        else:
            assert io_opts['output_type'] == 'mysql', \
                   "Unexpected output_type {}".format(io_opts['output_type'])
            recorder_dict[last_key] = { 'object': 'mysql.{}'.format(rec_type),
                                        'table': name }
            recorder_dict[last_key].update(common_data)
            recorder_dict[last_key]['connection'] = io_opts['schema_name']
            recorder_dict[last_key]['mode'] = 'a'
        return unused_key(last_key)
                                       
    last_key = unused_key(last_key)            
    # set up sql modules if needed
    if io_opts['output_type'] == 'mysql':
        recorder_dict[last_key] = {'module' : 'mysql'}
        last_key = unused_key(last_key)
    
        recorder_dict[last_key] = { 'object' : 'database',
                                    'name': io_opts['schema_name'],
                                    'schema': io_opts['schema_name'] }
        last_key = unused_key(last_key)   
        
    # Add recorder to swing bus for calibration
    last_key = add_recorder('network_node',
                            'recorder',
                            { 'parent' :   'network_node',
                              'property' : 'measured_real_power, measured_real_energy, voltage_A, voltage_B, voltage_C' },
                            last_key)
                 
    last_key = add_recorder('substation_transformer_power',
                            'recorder',
                            { 'parent' :   'substation_transformer',
                              'property' :  'power_out_A.real, power_out_A.imag, power_out_B.real, power_out_B.imag, power_out_C.real, power_out_C.imag, power_out.real, power_out.imag, power_losses_A.real, power_losses_A.imag, power_losses_B.real, power_losses_B.imag, power_losses_C.real, power_losses_C.imag' },
                            last_key)
        
    if swing_node != None:
        last_key = add_recorder('swing_bus',
                                'recorder',
                                {'parent' : '{:s}'.format(swing_node),
                                 'property' : 'measured_current_A.real, measured_current_A.imag, measured_current_B.real, measured_current_B.imag, measured_current_C.real, measured_current_C.imag, measured_voltage_A.real, measured_voltage_A.imag, measured_voltage_B.real, measured_voltage_B.imag, measured_voltage_C.real, measured_voltage_C.imag, measured_real_power, measured_reactive_power' },
                                last_key)
        
    # Measure outside temperature
    if climate_name != None:
        last_key = add_recorder('outside_temp',
                                'recorder',
                                { 'parent' : '{:s}'.format(climate_name),
                                  'property' : 'temperature' },
                                last_key)
    
    # Measure residential data
    if have_resp_zips == 1:
        last_key = add_recorder('res_responsive_load',
                                'collector',
                                { 'group' : '"class=ZIPload AND groupid=Responsive_load"',
                                  'property' : 'sum(base_power)' },
                                last_key)
        
    if have_unresp_zips == 1:
        last_key = add_recorder('res_unresponsive_load',
                                'collector',
                                { 'group' : '"class=ZIPload AND groupid=Unresponsive_load"',
                                  'property' : 'sum(base_power)' },
                                last_key)
        
    if have_waterheaters == 1:
        last_key = add_recorder('waterheater',
                                'collector',
                                { 'group' : '"class=waterheater"',
                                  'property' : 'sum(actual_load)' },
                                last_key)
        
    if have_lights == 1:
        last_key = add_recorder('lights',
                                'collector',
                                { 'group' : '"class=ZIPload AND groupid=Lights"',
                                  'property' : 'sum(base_power)' },
                                last_key)
        
    if have_plugs == 1:
        last_key = add_recorder('plugs',
                                'collector',
                                { 'group' : '"class=ZIPload AND groupid=Plugs"',
                                  'property' : 'sum(base_power)' },
                                last_key)
        
    if have_gas_waterheaters == 1:
        last_key = add_recorder('gas_waterheater',
                                'collector',
                                { 'group' : '"class=ZIPload AND groupid=Gas_waterheater"',
                                  'property' : 'sum(base_power)' },
                                last_key)
        
    if have_occupancy == 1:
        last_key = add_recorder('occupancy',
                                'collector',
                                { 'group' : '"class=ZIPload AND groupid=Occupancy"',
                                  'property' : 'sum(base_power)' },
                                last_key)
                                
    if have_solar_meter == 1:
        last_key = add_recorder('pv_meter_summed_real_power',
                                'collector',
                                { 'group': '"class=meter AND groupid=PV_Meter"',
                                  'property': 'sum(measured_real_power)' },
                                last_key)
        last_key = add_recorder('pv_meter_real_power',
                                'group_recorder',
                                { 'group': '"class=meter AND groupid=PV_Meter"',
                                  'property': 'measured_real_power' },
                                last_key)
                                
    if have_solar_triplex_meter == 1:
        last_key = add_recorder('pv_triplex_meter_summed_real_power',
                                'collector',
                                { 'group': '"class=triplex_meter AND groupid=PV_Meter"',
                                  'property': 'sum(measured_real_power)' },
                                last_key)
        last_key = add_recorder('pv_triplex_meter_real_power',
                                'group_recorder',
                                { 'group': '"class=triplex_meter AND groupid=PV_Meter"',
                                  'property': 'measured_real_power' },
                                last_key)
    
    last_key = add_recorder('all_meters_real_power',
                            'group_recorder',
                            { 'group' : '"class=meter"',
                              'property': 'measured_real_power' },
                            last_key)
                            
    last_key = add_recorder('voltA',
                            'group_recorder',
                            { 'group': '"class=node"',
                              'property': 'voltage_A',
                              'complex_part': 'MAG' },
                            last_key)
                            
    last_key = add_recorder('voltB',
                            'group_recorder',
                            { 'group': '"class=node"',
                              'property': 'voltage_B',
                              'complex_part': 'MAG' },
                            last_key)
            
    last_key = add_recorder('voltC',
                            'group_recorder',
                            { 'group': '"class=node"',
                              'property': 'voltage_C',
                              'complex_part': 'MAG' },
                            last_key)
                            
    last_key = add_recorder('all_triplex_nodes_voltage',
                            'group_recorder',
                            { 'group': '"class=triplex_node"',
                              'property': 'voltage_12',
                              'complex_part': 'MAG' },
                            last_key)                            
                            
    last_key = add_recorder('all_triplex_meters_real_power',
                            'group_recorder',
                            { 'group': '"class=triplex_meter"',
                              'property': 'measured_real_power' },
                            last_key)
                            
    return (recorder_dict, last_key)
                            
if __name__ == '__main__':
    pass