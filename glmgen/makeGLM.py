'''Writes the necessary .glm files for a calibration round. Define recording interval and MySQL schema name here.'''
from __future__ import division

from glmgen import feeder
from glmgen import Milsoft_GridLAB_D_Feeder_Generation

import datetime 
import os
import re
import math

def makeGLM(baseGLM, io_opts, time_opts, location_opts = {}, model_opts = {}):
  '''
  Create populated feeder.GlmFile and write it to disk.
  
  Parameters:
      - baseGLM (GlmFile):    Base GLM file loaded using feeder.GlmFile. Often a 
                              taxonomy feeder.
                              
      - io_opts (dict):       Dictionary of input-output related options.
            Required:
                - 'dir':          string path to folder to which glm file will be 
                                  written
                - 'filename':     glm file name (not the full path, just name and 
                                  optional extension)
            Defaulted:
                - 'output_type':  'csv' or 'mysql', default is 'csv'
                - 'git_csv_dir':   if true, adds a .keep file to csv_output, default is False
                - 'resources_dir': path to resources directory, default is 'schedules'
                - 'schema_name':   schema name for mysql, default is 'GridlabDB'
            Optional:
                - 'config_file':  Path to model configuration file, perhaps from 
                                  calibration process.
                                 
      - time_opts (dict):     Dictionary of time-releated options, namely, simulation 
                              duration and interval.
            Required:
                - 'start_time':   datetime.datetime object indicating the start 
                                  of the simulation
                - 'warmup_duration' or 'rec_start_time':   
                    - 'warmup_duration': datatime.timedelta object indicating 
                          the length of the warm-up period, that is, the time 
                          between when the simulation starts and when recording
                          starts.
                    - 'rec_start_time':  datetime.datetime object indicating when 
                          recorders should start recording
                - 'stop_time' OR 'sim_duration'
                    - 'stop_time':       datetime.datetime object indicating when 
                          the simulation is to stop
                    - 'sim_duration':    datetime.timedelta object indicating how 
                          long the simulation is to run (not including the warm-up 
                          time)
            Defaulted:
                - 'sim_interval': datetime.timedelta object indicating delta-t 
                                  (time step size) for the simulation, default is 60s
                - 'rec_interval': datetime.timedelta object indicating how often 
                                  data should be recorded, default is 300s
            Calculated:
                - 'warmup_duration' or 'rec_start_time'
                - 'stop_time' or 'sim_duration'
                - 'rec_limit':    maximum number of data points to be recorded
                
      - location_opts (dict): Dictionary of location options such as region and 
                              weather file.
                              
      - model_opts (dict):    Dictionary of options related to the meat of the model. 
                              Generally used to overwrite configuration or technology 
                              parameters.
                              
            Defaulted:
                - 'tech_flag': Technology flag, which is an integer [-1,13], defaults 
                               to 0.
            Optional:
                - 'config_data': dict of key, value pairs with which to overwrite config_data
                                 (defaults from the Configuration module).
                - 'tech_data':   dict of key, value pairs with which to overwrite tech_data 
                                 (defaults from the TechnologyParameters module).
                - 'use_flags':   dict of key, value pairs with which to overwrite use_flags
                                 (defaults from the TechnologyParameters module).
  '''
  
  # input helpers
  def assert_required(d, d_name, key):
      assert key in d, "Required parameter '{}' is not in {}.".format(key, d_name)
      
  def assert_compound_required(d, d_name, key_list, num_found_test):
      num_found = 0
      for key in key_list:
          if key in d:
               num_found += 1 
      assert num_found_test(num_found), \
             "Expected {} arguments from {} in {}, but found {}.".format(
                 num_found_test.expected_num, 
                 key_list, 
                 d_name, 
                 num_found)
                 
  def test_num_equals(num, expected):
      test_num_equals.expected_num = expected
      return num == expected
      
  def set_default(d, key, default):
      if not key in d:
          d[key] = default 
      assert key in d
          
  def assert_choice(d, d_name, key, choices):
      if key in d:
          assert d[key] in choices, "Unexpected value '{}' for {}['{}'].".format(d[key], d_name, key)
  
  # io_opts
  assert_required(io_opts, 'io_opts', 'dir')
  assert_required(io_opts, 'io_opts', 'filename')
  set_default(io_opts, 'output_type', 'csv')
  set_default(io_opts, 'git_csv_dir', False)
  assert_choice(io_opts, 'io_opts', 'output_type', ['csv', 'mysql'])
  set_default(io_opts, 'resources_dir', 'schedules')
  set_default(io_opts, 'schema_name', 'GridlabDB')
  
  # time_opts
  assert_required(time_opts, 'time_opts', 'start_time')
  test_num_is_one = lambda num: test_num_equals(num, 1) 
  assert_compound_required(time_opts, 'time_opts', ['warmup_duration', 'rec_start_time'], test_num_is_one)
  assert_compound_required(time_opts, 'time_opts', ['stop_time', 'sim_duration'], test_num_is_one)
  set_default(time_opts, 'sim_interval', datetime.timedelta(seconds=60))
  set_default(time_opts, 'rec_interval', datetime.timedelta(seconds=300))
  
  if 'warmup_duration' not in time_opts:
      assert 'rec_start_time' in time_opts
      time_opts['warmup_duration'] = time_opts['rec_start_time'] - time_opts['start_time']
  else:
      assert 'rec_start_time' not in time_opts
      time_opts['rec_start_time'] = time_opts['start_time'] + time_opts['warmup_duration']
      
  if 'stop_time' not in time_opts:
      assert 'sim_duration' in time_opts
      time_opts['stop_time'] = time_opts['rec_start_time'] + time_opts['sim_duration']
  else:
      assert 'sim_duration' not in time_opts
      time_opts['sim_duration'] = time_opts['stop_time'] - time_opts['rec_start_time']
      
  time_opts['rec_limit'] = int(math.ceil( time_opts['sim_duration'].total_seconds() / 
                                          time_opts['rec_interval'].total_seconds() ))
                                          
  # model_opts
  set_default(model_opts, 'tech_flag', 0)
  set_default(model_opts, 'config_data', {})
  set_default(model_opts, 'tech_data', {})
  set_default(model_opts, 'use_flags', {})
 
  # Create populated dictionary.
  glm_file, last_key = Milsoft_GridLAB_D_Feeder_Generation.GLD_Feeder(
      baseGLM,
      io_opts,
      time_opts,
      location_opts,
      model_opts) 
    
  # Get into clock object and set start and stop timestamp.
  for i in glm_file.keys():
    if 'clock' in glm_file[i].keys():
      glm_file[i]['starttime'] = "'{}'".format(time_opts['start_time'])
      glm_file[i]['stoptime'] = "'{}'".format(time_opts['stop_time'])

  # Turn dictionary into a *.glm string and print it to a file in the given directory.
  glm_file.save(os.path.join(io_opts['dir'],io_opts['filename']))
  if io_opts['output_type'] == 'csv':
    os.mkdir(os.path.join(io_opts['dir'],'csv_output'))
    if io_opts['git_csv_dir']:
        f = open(os.path.join(io_opts['dir'],'csv_output','.keep'),'w')
        f.close()
    
  return io_opts['filename']

def main():
  print (__doc__)
  print (makeGLM.__doc__)
if __name__ ==  '__main__':
   main();
