from glmgen import feeder

import re

def calculate_load_by_phase(load_object, power_type = 'apparent'):
    """
    Returns three-tuple of load by phase in W (power_type == 'real'), 
    var (power_type == 'reactive'), or VA (power_type == 'apparent') for 'load' 
    objects.  As you would expect, the tuple lists A, B, and C phase load in that order.
    """
    phase_load = { "A": complex(0.0, 0.0),
                   "B": complex(0.0, 0.0),
                   "C": complex(0.0, 0.0) }
    next_phase = { "A": "B", "B": "C", "C": "A" }
    
    def get_phase(m):
        phase = m.group(1)
        if not phase in phase_load:
            raise RuntimeError("Unexpected key '{}'.".format(key))
        return phase
            
    if feeder.GlmFile.object_is_type(load_object, 'load'):
        is_delta_connected = True if ('phases' in load_object) and ('D' in load_object['phases']) else False
        
        for key in load_object:
            m = re.match(r'^constant_power_(.)$', key)
            if m is not None:
                phase = get_phase(m)
                phase_load[phase] = phase_load[phase] + complex(load_object[key])
                
            m = re.match(r'^constant_impedance_(.)$', key)
            if m is not None:
                phase = get_phase(m)
                voltage_this = complex(load_object['voltage_' + phase])
                voltage_next = voltage_this
                if is_delta_connected:
                    voltage_next = complex(load_object['voltage_' + next_phase[phase]])
                phase_load[phase] = phase_load[phase] + voltage_this * voltage_next.conjugate() / complex(load_object[key]).conjugate()
               
            m = re.match(r'^constant_current_(.)$', key)
            if m is not None:
                phase = get_phase(m)
                voltage_to_use = None
                if is_delta_connected:
                    voltage_this = complex(load_object['voltage_' + phase])
                    voltage_next = complex(load_object['voltage_' + next_phase[phase]])
                    voltage_to_use = voltage_this - voltage_next
                else:
                    voltage_to_use = complex(load_object['voltage_' + phase])
                phase_load[phase] = phase_load[phase] + voltage_to_use * complex(load_object[key]).conjugate()
    else:
        raise RuntimeError("This function applies to a dict containing a GridLAB-D " + 
                           "object of type load")        

    for key in phase_load:
        phase_load[key] = complex_power_to_power_type(phase_load[key], power_type)
        
    return (phase_load["A"], phase_load["B"], phase_load["C"])

def calculate_load(triplex_node_object, power_type = 'apparent'):
    """
    Calculates load in load in W (power_type == 'real'), var (power_type == 
    'reactive'), or VA (power_type == 'apparent') for 'triplex_node' objects.
    """
    result = complex(0.0, 0.0)
    if feeder.GlmFile.object_is_type(triplex_node_object, 'triplex_node'):
          if 'power_1' in triplex_node_object:
            result = result + complex(triplex_node_object['power_1'])
          if 'power_12' in triplex_node_object:
            result = result + complex(triplex_node_object['power_12'])
    else:
        raise RuntimeError("This function applies to a dict containing a GridLAB-D " + 
                           "object of type triplex_node")           
    return complex_power_to_power_type(result, power_type)
    
def complex_power_to_power_type(complex_power, power_type):
    result = complex_power
    if power_type.lower() == 'apparent':
        result = abs(complex_power)
    elif power_type.lower() == 'real':
        result = complex_power.real
    elif power_type.lower() == 'reactive':
        result = complex_power.imag
    elif not power_type.lower() == 'complex':
        print("Unexpected power_type '{}'. Was expecting 'real', 'reactive', or 'apparent'. Returning full complex power.".format(power_type))
    return result
    