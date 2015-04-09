from glmgen import feeder

import re

def calculate_load_by_phase(load_object, nom_volt = None):
    """
    Returns three-tuple of load by phase in VA (abs(complex_power)) for 'load' objects.
    As you would expect, the tuple lists A, B, and C phase load in that order.
    """
    load_A = 0.0; load_B = 0.0; load_C = 0.0
    
    if nom_volt is None:
        if 'nominal_voltage' in load_object:
            nom_volt = load_object['nominal_voltage']
            
    if feeder.GlmFile.object_is_type(load_object, 'load'):
        
        if 'constant_power_A' in load_object:
          c_num = complex(load_object['constant_power_A'])
          load_A += abs(c_num)
    
        if 'constant_power_B' in load_object:
          c_num = complex(load_object['constant_power_B'])
          load_B += abs(c_num)

        if 'constant_power_C' in load_object:
          c_num = complex(load_object['constant_power_C'])
          load_C += abs(c_num)

        if 'constant_impedance_A' in load_object:
          if nom_volt is None:
            raise RuntimeError("Need nominal voltage to calculate power from impedance, but don't have it.")
          c_num = complex(load_object['constant_impedance_A'])
          load_A += pow(nom_volt,2)/(3*abs(c_num))

        if 'constant_impedance_B' in load_object:
          if nom_volt is None:
            raise RuntimeError("Need nominal voltage to calculate power from impedance, but don't have it.")
          c_num = complex(load_object['constant_impedance_B'])
          load_B += pow(nom_volt,2)/(3*abs(c_num))

        if 'constant_impedance_C' in load_object:
          if nom_volt is None:
            raise RuntimeError("Need nominal voltage to calculate power from impedance, but don't have it.")
          c_num = complex(load_object['constant_impedance_C'])
          load_C += pow(nom_volt,2)/(3*abs(c_num))

        if 'constant_current_A' in load_object:
          if nom_volt is None:
            raise RuntimeError("Need nominal voltage to calculate power from current, but don't have it.")
          c_num = complex(load_object['constant_current_A'])
          load_A += nom_volt*(abs(c_num))

        if 'constant_current_B' in load_object:
          if nom_volt is None:
            raise RuntimeError("Need nominal voltage to calculate power from current, but don't have it.")
          c_num = complex(load_object['constant_current_B'])
          load_B += nom_volt*(abs(c_num))

        if 'constant_current_C' in load_object:
          if nom_volt is None:
            raise RuntimeError("Need nominal voltage to calculate power from current, but don't have it.")
          c_num = complex(load_object['constant_current_C'])
          load_C += nom_volt*(abs(c_num))
    else:
        raise RuntimeError("This function applies to a dict containing a GridLAB-D " + 
                           "object of type load")
                           
    return (load_A, load_B, load_C)

def calculate_load(triplex_node_object):
    """
    Calculates load in VA (abs(complex_power)) for 'triplex_node' objects.
    """
    result = 0.0
    if feeder.GlmFile.object_is_type(triplex_node_object, 'triplex_node'):
          if 'power_1' in triplex_node_object:
            c_num = complex(triplex_node_object['power_1'])
            result += abs(c_num)
          if 'power_12' in triplex_node_object:
            c_num = complex(triplex_node_object['power_12'])
            result += abs(c_num)
    else:
        raise RuntimeError("This function applies to a dict containing a GridLAB-D " + 
                           "object of type triplex_node")
    return result
    
    