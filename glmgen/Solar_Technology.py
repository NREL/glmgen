from __future__ import division

from glmgen import helpers

import math
import random
import csv
import os
from math import cos, asin, sqrt,sin,atan2,sin,pi

def calculate_distance(lat1, lon1, lat2, lon2):
    r=6371
    dlat=deg2rad(lat2-lat1)
    dlon=deg2rad(lon2-lon1)
    a= sin(dlat/2)*sin(dlat/2)+cos(deg2rad(lat1))*cos(deg2rad(lat2))*sin(dlon/2)*sin(dlon/2)
    c=2*atan2(sqrt(a),sqrt(1-a))
    d=r*c
    return d

def deg2rad(deg):
    return deg*pi/180.0


def generate_player(parent,desoto_data,desoto_locations,dir):
    location_name_split = parent.split('_')
    location_name=''
    location_coord=[]
    sensor_coords={}
    if location_name_split[0]=='R2-25-00-1':
        location_name=location_name_split[0]+'_'+location_name_split[1]+'_'+location_name_split[2]
    else:
        location_name=location_name_split[1]+'_'+location_name_split[2]+'_'+location_name_split[3]

    with open(desoto_locations) as csvfile:
        reader=csv.reader(csvfile,delimiter=',')
        header=next(reader,None)
        for row in reader:
            if row[0][0:3]=='P2-':
                sensor_coords[row[0]]=(float(row[1]),float(row[2]))
            if row[0]==location_name: 
                #import pdb; pdb.set_trace()												  
                location_coord=[float(row[2]),float(row[1])] #they're backwards here.
                break
    distances=[]
#    min_val = 1000000000000
#    min_pos = -1
#    count = 0
#    weight=[0 for i in range(len(sensor_coords))]
    for i in sorted(sensor_coords):
        print calculate_distance(location_coord[0],location_coord[1],sensor_coords[i][0],sensor_coords[i][1])
        distances.append(calculate_distance(location_coord[0],location_coord[1],sensor_coords[i][0],sensor_coords[i][1]))
#        if distances[-1]<min_val:
#            min_val=distances[-1]
#            min_pos=count
#        count=count+1
#    weight[min_pos]=1
    #weighted averaging gives values which are too smooth.
##    min_val=min(distances)
 ##   distances=[(i-min_val+1) for i in distances] # translate so that the smallest distance is 1. (subtract min value from all and add 1 so min_value is 1)
    min_val=min(distances)
    ratios=[min_val/i for i in distances]
    total=sum(ratios)
    weight=[i/total for i in ratios]
    print weight


    data=[0 for i in range(60*60*24)] #second data
    ordered_columns=[] # The 0th element is Global Hoiz P2-01, the 1st element is Global Horiz P2-02 etc. This should have length of 15
    start_time=60*60*5
    counter=0
    with open(desoto_data) as csvfile:
        reader=csv.reader(csvfile,delimiter=',')
        header=next(reader,None) # the header
        desoto_index=1
        #import pdb; pdb.set_trace()												  
        for i in range(len(header)):
            if header[i]=='Global Horiz P2-%02d [W/m^2]'%(desoto_index):
                ordered_columns.append(i)
                desoto_index=desoto_index+1
        for row in reader:
        # for now only look at the first desoto data location.
        # later we iterate through all the ordered columns and the data variable is a matrix, not a vector
            data[start_time+counter]=0
            for sensor in range(len(ordered_columns)):
                data[start_time+counter]=data[start_time+counter]+float(row[ordered_columns[sensor]])*weight[sensor]
            counter=counter+1
    with open('%s/pv_%s.player'%(dir,parent),'wb') as outputfile:
        for i in range(len(data)):
            outputfile.write('2014-04-30 %02d:%02d:%02d, %.3f\n'%(i/3600,(i/60)%60,i%60,data[i]))
        # currently omitting the timezone and using whatever TZ is set to be.


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
    
    feeder_name=parent.split('_')[0]
    feeder_name2=parent.split('_')[1]
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
                                                  
    #import pdb; pdb.set_trace()												  
    if feeder_name=='R2-25-00-1' or feeder_name2=='R2-25-00-1':
        print config_data['directory']
        # This may fail because resources folder not built yet.
        #generate_player(parent,config_data['desoto_data'],config_data['desoto_locations'])
        generate_player(parent,'/projects/igms/inputs/ieee118_csv/desoto_20140430.csv','/projects/igms/inputs/ieee118_csv/desoto_locations.csv',config_data['directory'].split('\\')[0])

#TODO:
# use name (i.e. pv_{parent}.player as the player file
# do correct inerpoloation for the player file.
#	read in all the solar irradiance data and produce a new player file which is the weighted sum of the values accross all locations, based on their co-ordinates. Write the player files to the resource data folders.
# Check what feeder we're on and hence whether to use panel or panel2
# Check that all the entries are right.

        panel = {'object' : 'solar',
             'name' : 'pv_{:s}'.format(parent),
             'parent' : 'pv_inv_{:s}'.format(parent),
             'generator_mode' : 'SUPPLY_DRIVEN',
             'generator_status' : 'ONLINE',
             'panel_type' : 'SINGLE_CRYSTAL_SILICON',
             'efficiency' : '{:.4f}'.format(cell_efficiency),
             'area' : '{:.0f}'.format(panel_area),
         #    'orientation': 'FIXED_AXIS', #Not used in PLAYERVALUE mode
             'tilt_angle': '{:.2f}'.format(tilt_angle),
             'orientation_azimuth': '{:.2f}'.format(orientation_azimuth),
             'SOLAR_TILT_MODEL': 'PLAYERVALUE',
             'SOLAR_POWER_MODEL': 'FLATPLATE',
             'a_coeff': '-2.98',
             'b_coeff': '-0.0471',
             'dT_coeff': '1.0',
             'T_coeff': '-0.5',
			 1: {'object': 'player','property':'Insolation','file':'"pv_{:s}.player"'.format(parent)},
			 'ambient_temperature':'50',
			 'wind_speed':'1'}


    else:
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



    #CHECK FEEDER BEFORE APPLYING PANEL1 OR PANEL2
    return inverter, panel             
            
def main():
    #tests here
    pass
    #PVGLM = Append_Solar(PV_Tech_Dict,use_flags,)
    
if __name__ ==  '__main__':
    main()
