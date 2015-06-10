from glmgen import feeder

import random
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
    
def get_transformer_size(load_kVA, transformer_ratings_kVA, oversize_factor):
    for i, y in enumerate(transformer_ratings_kVA):
        if y >= load_kVA * oversize_factor:
          load_rating = y
          load_rating_index = i
          break
        elif y == transformer_ratings_kVA[-1]:
          load_rating = y
          load_rating_index = i
          break          
    assert load_rating_index is not None
    return load_rating, load_rating_index
    
def get_bin_index(bins):
    selection = random.random() * sum(bins)
    cum_proportion = 0.0
    for i, proportion in enumerate(bins):
        if cum_proportion < selection <= cum_proportion + proportion:
            return i
        cum_proportion += proportion
    assert False
    return None
    
def cap_floor_area(chosen_floor_area, total_node_load, load_left_to_allocate, peak_load_intensity, tol = 0.5):
    remainder = load_left_to_allocate - chosen_floor_area * peak_load_intensity
    if remainder < 0.0:
        if abs(remainder) > tol * total_node_load:
            this_load = load_left_to_allocate + tol * total_node_load
            new_floor_area = this_load / peak_load_intensity
            # print('Cutting floor area off at {:.0f} ft^2 (was {:.0f} ft^2).'.format(new_floor_area, chosen_floor_area))
            return new_floor_area
    return chosen_floor_area
    
def get_buildings(glm_file):
    """
    Returns list of tuples with
      - (triplex_)meter_key
      - classID
      - floor_area
    """
    result = []
    # ugly hardcoding to match the ugly hardcoding below
    load_classes = ['Residential1', 'Residential2', 'Residential3', 'Residential4', 'Residential5', 'Residential6', 'Strip Mall', 'Big Box', 'Office'] 
    for key, glm_object in glm_file.items():
        if feeder.GlmFile.object_is_type(glm_object, 'meter') or feeder.GlmFile.object_is_type(glm_object, 'triplex_meter'):
            if ('groupid' in glm_object) and (glm_object['groupid'] in ['Commercial_Meter', 'Residential_Meter']):
                load_class, floor_area = extract_bldg_input_data(glm_file, key)
                result.append((key, load_classes.index(load_class), floor_area))
    return result
    
def extract_bldg_input_data(glm_file, bldg_meter_key):
    load_class = None; floor_area = 0.0
    bldg_meter = glm_file[bldg_meter_key]
    if feeder.GlmFile.object_is_type(bldg_meter, 'meter'):
        assert bldg_meter['groupid'] == 'Commercial_Meter'
        if re.search('_office_', bldg_meter['name']):
            load_class = 'Office'
        else:
            assert re.search('_bigbox_', bldg_meter['name'])
            load_class = 'Big Box'
        # to get floor_area follow meter -> transformer -> triplex_meter -> house
        for transformer_key in glm_file.get_connector_keys_by_node(bldg_meter_key, 'from', 'transformer'):
          assert 'to' in glm_file[transformer_key]
          tm_name = glm_file[transformer_key]['to']
          tm_key = glm_file.get_object_key_by_name(tm_name, 'triplex_meter')
          for house_key in glm_file.get_children_keys(tm_key, 'house'):
              assert 'floor_area' in glm_file[house_key]
              floor_area += float(glm_file[house_key]['floor_area'])
    else:
        assert feeder.GlmFile.object_is_type(bldg_meter, 'triplex_meter')
        child_house_keys = glm_file.get_children_keys(bldg_meter_key, 'house')
        assert len(child_house_keys) == 1        
        if bldg_meter['groupid'] == 'Commercial_Meter':
            load_class = 'Strip Mall'
        else:
            assert bldg_meter['groupid'] == 'Residential_Meter'
            assert 'comment' in glm_file[child_house_keys[0]]
            m = re.match(r'.*Load Classification -> (.+)', 
                         glm_file[child_house_keys[0]]['comment'])
            load_class = m.group(1)
        assert 'floor_area' in glm_file[child_house_keys[0]]
        floor_area = float(glm_file[child_house_keys[0]]['floor_area'])
    return load_class, floor_area    
        