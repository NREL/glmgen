#!/usr/bin/env python

import datetime, copy, os, re, warnings
# import networkx as nx
from matplotlib import pyplot as plt
import re

from collections import deque

class GlmFile(dict):
    """
    GlmFile is a dict with integer keys (for ordering the file) and dict
    values, each of which is an item in a glm file.
    """
    def __init__(self, *arg, **kw):
        super(GlmFile, self).__init__(*arg,**kw)
        
    def get_clocks(self):
        """
        Returns a list of deep copies of all clock objects in this GlmFile.
        """
        result = []
        for key, value in sorted(self.items(), key=lambda pair: pair[0]):
            if 'clock' in value:
                result.append(copy.deepcopy(value))
        return result
    
    def get_objects_by_type(self, glm_type=None):
        """
        Returns a list of deep copies of all objects ('object') of glm_type 
        in this GlmFile.
        """
        result = []
        for key, value in sorted(self.items(), key=lambda pair: pair[0]):
            if self.object_is_type(value,glm_type):
                result.append(copy.deepcopy(value))
        return result

    def object_is_type(self, obj, glm_type):
        """
        Inspects obj, a dict representing an item in a glm file, determining
        whether it is an 'object', and if so, if it is of glm_type.
        
        Parameters:
            obj (dict): item in a glm file
            glm_type (string): type of 'object' (e.g., 'house', 'load')
            
        Returns True if glm_type is None or obj is of glm_type, False otherwise.
        """
        result = True
        if glm_type is not None:
            if 'object' not in obj:
                result = False
            elif not re.match("{:s}.*".format(glm_type),obj['object']):
                result = False
        return result
        
    def get_parent_key(self,key,parent_type=None):
        """
        Looks for the key of the parent of self[key].
        
        Parameters:
            key (int): self[key] is the glm object whose parent we seek
            parent_type (string): None, or the type of object we require the 
                                  parent to be in order to return it
                                  
        Returns None if self[key] has no parent, or the parent is not of 
        parent_type. 
        
        Returns the key to the parent object, let's call it parent_key, such 
        that the parent of self[key] is self[parent_key], if self[key] has a 
        parent, and object_is_type(self[parent_key],parent_type) (which always 
        returns True if parent_type is None).
        """
        result = None
        if key in self and 'parent' in self[key]:
          parent_name = self[key]['parent']
        else:
          return result
        for obj_key, obj in self.items():
            if 'name' in obj and obj['name'] == parent_name:
                if not self.object_is_type(obj,parent_type):
                    continue
                result = obj_key
                break
        return result
      
    def get_connector_by_to_node(self,to_node_key,connector_type=None):
        """
        Looks for the first connecting object that refers to self[to_node_key] 
        in a 'to' field. Optionally restricts the returned object to be of a 
        certain connector_type.
        
        Parameters:
            to_node_key (int): self[to_node_key] is the object we expect to 
                               be in a 'to' field of another object
            connector_type (string): 
            
        Returns None if self[to_node_key] is not connected 'to', or there is
        no such connector of connector type.
        
        Returns the key to the connecting object, let's call it connector_key,
        such that self[connector_key] lists the name of self[to_node_key] in 
        its 'to' field, and object_is_type(self[connector_key],connector_type)
        (which always returns True if parent_type is None).
        """
        result = None
        if to_node_key in self and 'name' in self[to_node_key]:
            to_node_name = self[to_node_key]['name']
        else:
            return result
        for obj_key, obj in self.items():
            if 'to' in obj and obj['to'] == to_node_name:
                if not self.object_is_type(obj,connector_type):
                    continue
                result = obj_key
                break
        return result  
        
    def get_name_of_swing_bus(self):
        """
        Returns the name of the first meter with bustype SWING
        """
        for key, value in sorted(self.items(), key=lambda pair: pair[0]):
            if 'object' in value and value['object'] == 'meter':
                if 'bustype' in value and value['bustype'] == 'SWING':
                    if 'name' in value:
                        return value['name']
        return None
        
    def __setitem__(self, key, item):
        if not isinstance(key, int):
            raise KeyError("GlmFile keys must be integers.")
        if not (key >= 0 and key <= len(self)):
            raise KeyError("""GlmFile keys must be a sequential list of integers 
                starting from 0's. Yes, GlmFile should be a list. Sorry.""")
        if key in self.keys():
            # shift everyone else down
            keys_to_shift = [k for k in sorted(self.keys()) if k >= key]
            for k in reversed(keys_to_shift):
                super(GlmFile, self).__setitem__(k+1, self[k])
                super(GlmFile, self).__delitem__(k)
        super(GlmFile, self).__setitem__(key, item)
        
    def __delitem__(self, key):
        keys_to_shift = [k for k in sorted(self.keys()) if k >= key]
        assert keys_to_shift[0] == key
        for i, cur_key in enumerate(keys_to_shift):
            if i > 0:
                self[cur_key - 1] = self[cur_key]
            super(GlmFile, self).__delitem__(key)        
        
    def set_clock(self, starttime, stoptime, timezone = None):    
        set_time = False
        to_remove = []
        for key, value in sorted(self.items(), key=lambda pair: pair[0]):
            if 'clock' in value:
                if not set_time:
                    # first instance - set the time
                    value['startime'] = "'{}'".format(starttime)
                    value['stoptime'] = "'{}'".format(stoptime)
                    if timezone is not None:
                        value['timezone'] = '{}'.format(timezone)
                    set_time = True
                else:
                    to_remove.append(key)
                    
        if not set_time:
            # make clock from scratch
            self[0] = { 'clock': '',
                        'startime': "'{}'".format(starttime),
                        'stoptime': "'{}'".format(stoptime) }
            if timezone is not None:
                self[0]['timezone'] = '{}'.format(timezone)
            
        # remove in reverse order, because del changes keys
        for key in reversed(to_remove):
            del self[key]
               
    def set_transmission_voltage(self, playerfiles):
        """
        Sets the voltage on the SWING bus to the values in the playerfiles.
        
        Parameters
            - playerfiles (length 3 list of paths): Paths to player files for
                  phases A, B, and C, respectively
        """
        if not len(playerfiles) == 3:
            raise RuntimeError("""The playerfiles argument must be an 
                iterable of length 3. It is assumed that the contents are 
                paths to player files for phases A, B, and C, respectively.""")

        # get SWING bus name
        swing_bus = self.get_name_of_swing_bus()
        if swing_bus is None:
            raise RuntimeError("Cannot set the transmission voltage without a swing bus.")
        
        # replace data if possible, otherwise, make new players
        property_dict = { 'voltage_A': (playerfiles[0], False),
                          'voltage_B': (playerfiles[1], False),
                          'voltage_C': (playerfiles[2], False) }
        to_remove = []
        for key, value in sorted(self.items(), key=lambda pair: pair[0]):
            if 'object' in value and value['object'] == 'player':
                if 'property' in value and value['property'] in property_dict:
                    if 'parent' in value and value['parent'] == swing_bus:
                        if not property_dict[value['property']][1]:
                            value['file'] = property_dict[value['property']][0]
                        else:
                            # already found -- remove
                            to_remove.append(key)
                            
        for key, item in property_dict.items():
            if not item[1]:
                # make from scratch
                # TODO: Find a good insertion point higher up in the file
                self[len(self)] = {'object' : 'player',
                                   'property' : key,
                                   'parent' : swing_bus,
                                   'loop' : '10',
                                   'file' : item[0]}
                            
        for key in reversed(to_remove):
            del self[key]
        
    @staticmethod
    def load(glm_file_name):
        tokens = GlmFile.__tokenizeGlm(glm_file_name)
        return GlmFile.__parseTokenList(tokens)
        
    def __str__(self):
        """
        Write this GlmFile to string, with objects ordered by their key.
        """
        output = ''
        try:
            for key, value in sorted(self.items(), key=lambda pair: pair[0]):
                output += dictToString(value) + '\n'
        except ValueError:
            raise Exception
        return output
        
    def save(self,glm_file_name):
        glm_string = str(self)
        file = open(glm_file_name, 'w')
        file.write(glm_string)
        file.close()    
    
    @staticmethod
    def __tokenizeGlm(glmFileName):
        with open(glmFileName,'r') as glmFile:
            data = glmFile.read()
        # Get rid of http for stylesheets because we don't need it and it conflicts with comment syntax.
        data = re.sub(r'http:\/\/', '', data)  
        # Strip comments.
        data = re.sub(r'\/\/.*\n', '', data)
        # Add semicolons to # lines
        data = re.sub(re.compile(r'^#(.*)$',re.MULTILINE),r'#\1;',data)
        # Strip non-single whitespace because it's only for humans:
        data = data.replace('\n','').replace('\r','').replace('\t',' ')
        # Tokenize around semicolons, braces and whitespace.
        tokenized = re.split(r'(;|\}|\{|\s)',data)
        # Get rid of whitespace strings.
        basicList = deque([x for x in tokenized if (x != '') and (x != ' ')])
        return basicList

    @staticmethod
    def __parseTokenList(tokenList):
        
        # Tree variables.
        tree = GlmFile()
        guid = 0
        guidStack = []
        
        # Helper function to add to the current leaf we're visiting.
        def currentLeafAdd(key, value):
            current = tree
            for x in guidStack:
                current = current[x]
            current[key] = value
          
        # Helper function to turn a list of strings into one string with some decent formatting.
        # TODO: formatting could be nicer, i.e. remove the extra spaces this function puts in.
        def listToString(listIn):
            result = ''
            if len(listIn) > 0: 
                result = listIn[1]
                for x in listIn[2:-1]:
                    result = result + ' ' + x
            return result
            
        # Pop off a full token, put it on the tree, rinse, repeat.
        while len(tokenList) > 0:
            # Pop, then keep going until we have a full token (i.e. 'object house', not just 'object')
            fullToken = []
            while fullToken == [] or fullToken[-1] not in ['{',';','}']:
                fullToken.append(tokenList.popleft())
            # Work with what we've collected.
            if fullToken[-1] == ';':
                # Special case when we have zero-attribute items (like #include, #set, module).
                if guidStack == [] and fullToken != [';']:
                    tree[guid] = {'omftype':fullToken[0],'argument':listToString(fullToken)}
                    guid += 1
                # We process if it isn't the empty token (';')
                elif len(fullToken) > 1:
                    currentLeafAdd(fullToken[0],listToString(fullToken))
            elif fullToken[-1] == '}':
                if len(fullToken) > 1:
                    currentLeafAdd(fullToken[0],listToString(fullToken))
                guidStack.pop()
            elif fullToken[0] == 'schedule':
                # Special code for those ugly schedule objects:
                if fullToken[0] == 'schedule':
                    while fullToken[-1] not in ['}']:
                        fullToken.append(tokenList.popleft())
                    tree[guid] = {'object':'schedule','name':fullToken[1], 'cron':' '.join(fullToken[3:-2])}
                    guid += 1
            elif fullToken[-1] == '{':
                currentLeafAdd(guid,{})
                guidStack.append(guid)
                guid += 1
                # Wrapping this currentLeafAdd is defensive coding so we don't crash on malformed glms.
                if len(fullToken) > 1:
                    # Do we have a clock/object or else an embedded configuration object?
                    if len(fullToken) < 4:
                        currentLeafAdd(fullToken[0],fullToken[-2])
                    else:
                        currentLeafAdd('omfEmbeddedConfigObject', fullToken[0] + ' ' + listToString(fullToken))
        return tree

def parse(glmFileName):
    """
    Deprecated -- use GlmFile.load(glmFileName).
    """
    return GlmFile.load(glmFileName)

def dictToString(inDict):
  
  # Helper function: given a single dict, concatenate it into a string.
  def gatherKeyValues(inDict, keyToAvoid):
    otherKeyValues = ''
    for key in inDict:
      if type(key) is int:
        # WARNING: RECURSION HERE
        # TODO (cosmetic): know our depth, and indent the output so it's more human readable.
        otherKeyValues += dictToString(inDict[key])
      elif key != keyToAvoid:
        if key == 'comment':
          otherKeyValues += (inDict[key] + '\n')
        elif key == 'name' or key == 'parent':
          if len(inDict[key]) <= 62:
            otherKeyValues += ('\t' + key + ' ' + inDict[key] + ';\n')
          else:
            warnings.warn("{:s} argument is longer that 64 characters. Truncating.".format(key), RuntimeWarning)
            otherKeyValues += ('\t' + key + ' ' + inDict[key][0:62] + '; // truncated from {:s}\n'.format(inDict[key]))
        else:
          otherKeyValues += ('\t' + key + ' ' + str(inDict[key]) + ';\n')
    return otherKeyValues
    
  # Handle the different types of dictionaries that are leafs of the tree root:
  if 'omftype' in inDict:
    return inDict['omftype'] + ' ' + inDict['argument'] + ';'
    
  elif 'module' in inDict:
    return 'module ' + inDict['module'] + ' {\n' + gatherKeyValues(inDict, 'module') + '};\n'
    
  elif 'clock' in inDict:
    #return 'clock {\n' + gatherKeyValues(inDict, 'clock') + '};\n'
    # THis object has known property order issues writing it out explicitly
    clock_string = 'clock {\n' + '\ttimezone ' + inDict['timezone'] + ';\n' + '\tstarttime ' + inDict['starttime'] + ';\n' + '\tstoptime ' + inDict['stoptime'] + ';\n};\n'
    return clock_string
    
  elif 'object' in inDict and inDict['object'] == 'schedule':
    return 'schedule ' + inDict['name'] + ' {\n' + inDict['cron'] + '\n};\n'
    
  elif 'object' in inDict:
    return 'object ' + inDict['object'] + ' {\n' + gatherKeyValues(inDict, 'object') + '};\n'
    
  elif 'omfEmbeddedConfigObject' in inDict:
    return inDict['omfEmbeddedConfigObject'] + ' {\n' + gatherKeyValues(inDict, 'omfEmbeddedConfigObject') + '};\n'
    
  elif '#include' in inDict:
    return '#include ' + '"' + inDict['#include'] + '"' + '\n'
    
  elif '#define' in inDict:
    return '#define ' + inDict['#define'] + '\n'
    
  elif '#set' in inDict:
    return '#set ' + inDict['#set'] + '\n'
    
  elif 'class' in inDict:
    prop = ''
    if 'variable_types' in inDict.keys() and 'variable_names' in inDict.keys() and len(inDict['variable_types'])==len(inDict['variable_names']):
      for x in range(len(inDict['variable_types'])):
        prop += '\t' + inDict['variable_types'][x] + ' ' + inDict['variable_names'][x] + ';\n'
      return 'class ' + inDict['class'] + '{\n' + prop + '};\n'
    else:
      return '\n'

      
def adjustTime(tree, simLength, simLengthUnits, simStartDate):
  # translate LengthUnits to minutes.
  if simLengthUnits == 'minutes':
    lengthInSeconds = simLength * 60
    interval = 60
  elif simLengthUnits == 'hours':
    lengthInSeconds = 3600 * simLength
    interval = 3600
  elif simLengthUnits == 'days':
    lengthInSeconds = 86400 * simLength
    interval = 3600

  starttime = datetime.datetime.strptime(simStartDate, '%Y-%m-%d')
  stoptime = starttime + datetime.timedelta(seconds=lengthInSeconds)

  # alter the clocks and recorders:
  for x in tree:
    leaf = tree[x]
    if 'clock' in leaf:
      # Ick, Gridlabd wants time values wrapped in single quotes:
      leaf['starttime'] = "'" + str(starttime) + "'"
      # Apparently it needs timestamp=starttime. Gross! Bizarre!
      leaf['timestamp'] = "'" + str(starttime) + "'"
      leaf['stoptime'] = "'" + str(stoptime) + "'"
    elif 'object' in leaf and (leaf['object'] == 'recorder' or leaf['object'] == 'collector'):
      leaf['interval'] = str(interval)
      # We're trying limitless for the time being.
      # leaf['limit'] = str(simLength)
      # Also, set the file since we're already inside this data structure.
      if leaf['file'] == 'meterRecorder_XXX.csv':
        leaf['file'] = 'meterRecorder_' + leaf['name'] + '.csv'
    elif 'argument' in leaf and leaf['argument'].startswith('minimum_timestep'):
      leaf['argument'] = 'minimum_timestep=' + str(interval)

def fullyDeEmbed(glmTree):
  def deEmbedOnce(glmTree):
    iterTree = copy.deepcopy(glmTree)
    for x in iterTree:
      for y in iterTree[x]:
        if type(iterTree[x][y]) is dict and 'object' in iterTree[x][y]:
          # set the parent and name attributes:
          glmTree[x][y]['parent'] = glmTree[x]['name']
          if 'name' in glmTree[x][y]:
            pass
          else:
            glmTree[x][y]['name'] = glmTree[x]['name'] + glmTree[x][y]['object'] + str(y)
            
          # check for key collision, which should technically be impossible:
          if y in glmTree.keys():
            print('KEY COLLISION!')
            z = y
            while z in glmTree.keys():
              z += 1
            # put the embedded object back up in the glmTree:
            glmTree[z] = glmTree[x][y]
          else:
            # put the embedded object back up in the glmTree:
            glmTree[y] = glmTree[x][y]
          # delete the embedded copy:
          del glmTree[x][y]
        # TODO: take this if case and roll it into the if case above to save lots of code and make it easier to read.
        if type(iterTree[x][y]) is dict and 'omfEmbeddedConfigObject' in iterTree[x][y]:
          configList = iterTree[x][y]['omfEmbeddedConfigObject'].split()
          # set the name attribute and the parent's reference:
          if 'name' in glmTree[x][y]:
            pass
          else:
            glmTree[x][y]['name'] = glmTree[x]['name'] + configList[2] + str(y)
          glmTree[x][y]['object'] = configList[2]
          glmTree[x][configList[0]] = glmTree[x][y]['name']
          # get rid of the omfEmbeddedConfigObject string:
          del glmTree[x][y]['omfEmbeddedConfigObject']
          # check for key collision, which should technically be impossible BECAUSE Y AND X ARE DIFFERENT INTEGERS IN [1,...,numberOfDicts]:
          if y in glmTree.keys():
            print('KEY COLLISION!')
            z = y
            while z in glmTree.keys():
              z += 1
            # put the embedded object back up in the glmTree:
            glmTree[z] = glmTree[x][y]
          else:
            # put the embedded object back up in the glmTree:
            glmTree[y] = glmTree[x][y]
          # delete the embedded copy:
          del glmTree[x][y]
  lenDiff = 1
  while lenDiff != 0:
    currLen = len(glmTree)
    deEmbedOnce(glmTree)
    lenDiff = len(glmTree) - currLen

def attachRecorders(tree, recorderType, keyToJoin, valueToJoin, sample=False):
  # TODO: if sample is a percentage, only attach to that percentage of nodes chosen at random.
  # HACK: the biggestKey assumption only works for a flat tree or one that has a flat node for the last item...
  biggestKey = sorted([int(key) for key in tree.keys()])[-1] + 1
  # Types of recorders we can attach:
  recorders = { 'Regulator':{'interval':'1', 'parent':'X', 'object':'recorder', 'limit':'0', 'file':'Regulator_Y.csv', 'property':'tap_A,tap_B,tap_C,power_in_A.real,power_in_A.imag,power_in_B.real,power_in_B.imag,power_in_C.real,power_in_C.imag,power_in.real,power_in.imag'},
          'Voltage':{'interval':'1', 'parent':'X', 'object':'recorder', 'limit':'0', 'file':'Voltage_Y.csv', 'property':'voltage_1.real,voltage_1.imag,voltage_2.real,voltage_2.imag,voltage_12.real,voltage_12.imag'},
          'Capacitor':{'interval':'1', 'parent':'X', 'object':'recorder', 'limit':'0', 'file':'Capacitor_Y.csv', 'property':'switchA,switchB,switchC'},
          'Climate':{'interval':'1', 'parent':'X', 'object':'recorder', 'limit':'0', 'file':'climate.csv', 'property':'temperature,solar_direct,wind_speed,rainfall,snowdepth'},
          'Inverter':{'interval':'1', 'parent':'X', 'object':'recorder', 'limit':'0', 'file':'inverter_Y.csv', 'property':'power_A.real,power_A.imag,power_B.real,power_B.imag,power_C.real,power_C.imag'},
          'Windmill':{'interval':'1', 'parent':'X', 'object':'recorder', 'limit':'0', 'file':'windmill_Y.csv', 'property':'voltage_A.real,voltage_A.imag,voltage_B.real,voltage_B.imag,voltage_C.real,voltage_C.imag,current_A.real,current_A.imag,current_B.real,current_B.imag,current_C.real,current_C.imag'},
          'CollectorVoltage':{'interval':'1', 'object':'collector', 'limit':'0', 'file':'VoltageJiggle.csv', 'group':'class=triplex_meter', 'property':'min(voltage_12.mag),mean(voltage_12.mag),max(voltage_12.mag),std(voltage_12.mag)'},
          'OverheadLosses':{'group':'class=overhead_line', 'interval':'1', 'object':'collector', 'limit':'0', 'file':'OverheadLosses.csv', 'property':'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'},
          'UndergroundLosses':{'group':'class=underground_line', 'interval':'1', 'object':'collector', 'limit':'0', 'file':'UndergroundLosses.csv', 'property':'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'},
          'TriplexLosses':{'group':'class=triplex_line', 'interval':'1', 'object':'collector', 'limit':'0', 'file':'TriplexLosses.csv', 'property':'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'},
          'TransformerLosses':{'group':'class=transformer', 'interval':'1', 'object':'collector', 'limit':'0', 'file':'TransformerLosses.csv', 'property':'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'}
        }
  # If the recorder doesn't have a parent don't walk the tree:
  if 'parent' not in recorders[recorderType]:
    # What class of objects are we trying to attach to?
    objectSet = set([tree[x]['object'] for x in tree.keys() if 'object' in tree[x]])
    groupClass = recorders[recorderType]['group'][6:]
    # Only attach if the right objects are there: 
    if groupClass in objectSet:
      newLeaf = copy.copy(recorders[recorderType])
      tree[biggestKey] = newLeaf
      biggestKey += 1
  # Walk the tree. Don't worry about a recursive walk (yet).
  staticTree = copy.copy(tree)
  for key in staticTree:
    leaf = staticTree[key]
    if keyToJoin in leaf and 'name' in leaf:
      parentObject = leaf['name']
      if leaf[keyToJoin] == valueToJoin:
        # DEBUG:print 'just joined ' + parentObject
        newLeaf = copy.copy(recorders[recorderType])
        newLeaf['parent'] = parentObject
        newLeaf['file'] = recorderType + '_' + parentObject + '.csv'
        tree[biggestKey] = newLeaf
        biggestKey += 1

def groupSwingKids(tree):
  staticTree = copy.copy(tree)
  swingNames = []
  swingTypes = []
  # find the swing nodes:
  for key in staticTree:
    leaf = staticTree[key]
    if 'bustype' in leaf and leaf['bustype'] == 'SWING':
      swingNames += [leaf['name']]
  # set the groupid on the kids:
  for key in staticTree:
    leaf = staticTree[key]
    if 'from' in leaf and 'to' in leaf:
      if leaf['from'] in swingNames or leaf['to'] in swingNames:
        leaf['groupid'] = 'swingKids'
        swingTypes += [leaf['object']]
  # attach the collector:
  biggestKey = sorted([int(key) for key in tree.keys()])[-1] + 1
  collector = {'interval':'1', 'object':'collector', 'limit':'0', 'group':'X', 'file':'Y', 'property':'sum(power_in.real),sum(power_in.imag)'}
  for obType in swingTypes:
    insert = copy.copy(collector)
    insert['group'] = 'class=' + obType + ' AND groupid=swingKids'
    insert['file'] = 'SwingKids_' + obType + '.csv'
    tree[biggestKey] = insert
    biggestKey += 1

def phaseCount(phaseString):
  ''' Return number of phases not including neutrals. '''
  return sum([phaseString.lower().count(x) for x in ['a','b','c']])

# def treeToNxGraph(inTree):
# ''' Convert feeder tree to networkx graph. '''
# outGraph = nx.Graph()
# for key in inTree:
#   item = inTree[key]
#   if 'name' in item.keys():
#     if 'parent' in item.keys():
#       outGraph.add_edge(item['name'],item['parent'], attr_dict={'type':'parentChild','phases':1})
#       outGraph.node[item['name']]['type']=item['object']
#       outGraph.node[item['name']]['pos']=(float(item.get('latitude',0)),float(item.get('longitude',0)))
#     elif 'from' in item.keys():
#       myPhase = phaseCount(item.get('phases','AN'))
#       outGraph.add_edge(item['from'],item['to'],attr_dict={'type':item['object'],'phases':myPhase})
#     elif item['name'] in outGraph:
#       # Edge already led to node's addition, so just set the attributes:
#       outGraph.node[item['name']]['type']=item['object']
#     else:
#       outGraph.add_node(item['name'],attr_dict={'type':item['object']})
#     if 'latitude' in item.keys() and 'longitude' in item.keys():
#       outGraph.node.get(item['name'],{})['pos']=(float(item['latitude']),float(item['longitude']))
# return outGraph

def _obToCol(obStr):
  ''' Function to color by node/edge type. '''
  obToColor = {'node':'gray',
    'house':'#3366FF',
    'load':'#3366FF',
    'ZIPload':'#66CCFF',
    'waterheater':'#66CCFF',
    'triplex_meter':'#FF6600',
    'triplex_node':'#FFCC00',
    'gridNode':'#CC0000',
    'swingNode':'hotpink',
    'parentChild':'gray',
    'underground_line':'black'}
  return obToColor.get(obStr,'black')

# def latLonNxGraph(inGraph, labels=False, neatoLayout=False):
  # ''' Draw a networkx graph representing a feeder. '''
  # plt.figure(figsize=(15,15))
  # plt.axis('off')
  # plt.tight_layout()
  # # Layout the graph via GraphViz neato. Handy if there's no lat/lon data.
  # if neatoLayout:
    # # HACK: work on a new graph without attributes because graphViz tries to read attrs.
    # pos = nx.graphviz_layout(nx.Graph(inGraph.edges()),prog='neato')
  # else:
    # pos = {n:inGraph.node[n].get('pos',(0,0)) for n in inGraph}
  # # Draw all the edges.
  # for e in inGraph.edges():
    # eType = inGraph.edge[e[0]][e[1]]['type']
    # ePhases = inGraph.edge[e[0]][e[1]]['phases']
    # standArgs = {'edgelist':[e],
           # 'edge_color':_obToCol(eType),
           # 'width':2,
           # 'style':{'parentChild':'dotted','underground_line':'dashed'}.get(eType,'solid') }
    # if ePhases==3:
      # standArgs.update({'width':5})
      # nx.draw_networkx_edges(inGraph,pos,**standArgs)
      # standArgs.update({'width':3,'edge_color':'white'})
      # nx.draw_networkx_edges(inGraph,pos,**standArgs)
      # standArgs.update({'width':1,'edge_color':_obToCol(eType)})
      # nx.draw_networkx_edges(inGraph,pos,**standArgs)
    # if ePhases==2:
      # standArgs.update({'width':3})
      # nx.draw_networkx_edges(inGraph,pos,**standArgs)
      # standArgs.update({'width':1,'edge_color':'white'})
      # nx.draw_networkx_edges(inGraph,pos,**standArgs)
    # else:
      # nx.draw_networkx_edges(inGraph,pos,**standArgs)
  # # Draw nodes and optional labels.
  # nx.draw_networkx_nodes(inGraph,pos,
               # nodelist=pos.keys(),
               # node_color=[_obToCol(inGraph.node[n]['type']) for n in inGraph],
               # linewidths=0,
               # node_size=40)
  # if labels:
    # nx.draw_networkx_labels(inGraph,pos,
                # font_color='black',
                # font_weight='bold',
                # font_size=0.25)
