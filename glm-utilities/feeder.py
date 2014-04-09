#!/usr/bin/env python

import datetime, copy, os, re, warnings
# import networkx as nx
from matplotlib import pyplot as plt

def tokenizeGlm(glmFileName):
	with open(glmFileName,'r') as glmFile:
		data = glmFile.read()
	# Get rid of http for stylesheets because we don't need it and it conflicts with comment syntax.
	data = re.sub(r'http:\/\/', '', data)  
	# Strip comments.
	data = re.sub(r'\/\/.*\n', '', data)
	# TODO: If the .glm creator has been lax with semicolons, add them back.
	# Also strip non-single whitespace because it's only for humans:
	data = data.replace('\n','').replace('\r','').replace('\t',' ')
	# Tokenize around semicolons, braces and whitespace.
	tokenized = re.split(r'(;|\}|\{|\s)',data)
	# Get rid of whitespace strings.
	basicList = filter(lambda x:x!='' and x!=' ', tokenized)
	return basicList

def parseTokenList(tokenList):
	# Tree variables.
	tree = {}
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
		if len(listIn) == 0:
			return ''
		else:
			return reduce(lambda x,y:str(x)+' '+str(y),listIn[1:-1])
	# Pop off a full token, put it on the tree, rinse, repeat.
	while tokenList != []:
		# Pop, then keep going until we have a full token (i.e. 'object house', not just 'object')
		fullToken = []
		while fullToken == [] or fullToken[-1] not in ['{',';','}']:
			fullToken.append(tokenList.pop(0))
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
					fullToken.append(tokenList.pop(0))
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
	tokens = tokenizeGlm(glmFileName)
	return parseTokenList(tokens)

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
			for x in xrange(len(inDict['variable_types'])):
				prop += '\t' + inDict['variable_types'][x] + ' ' + inDict['variable_names'][x] + ';\n'
			return 'class ' + inDict['class'] + '{\n' + prop + '};\n'
		else:
			return '\n'

def write(inTree):
	'''write(inTreeDict)->stringGlm'''
	output = ''
	for key in inTree:
		output += dictToString(inTree[key]) + '\n'
	return output

def sortedWrite(inTree):
	'''write(inTreeDict)->stringGlm, with all tree objects ordered by their key. '''
	sortedKeys = sorted(inTree.keys(), key=int)
	output = ''
	try:
		for key in sortedKeys:
			output += dictToString(inTree[key]) + '\n'
	except ValueError:
		raise Exception
	return output

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
	recorders = {	'Regulator':{'interval':'1', 'parent':'X', 'object':'recorder', 'limit':'0', 'file':'Regulator_Y.csv', 'property':'tap_A,tap_B,tap_C,power_in_A.real,power_in_A.imag,power_in_B.real,power_in_B.imag,power_in_C.real,power_in_C.imag,power_in.real,power_in.imag'},
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
# 	''' Convert feeder tree to networkx graph. '''
# 	outGraph = nx.Graph()
# 	for key in inTree:
# 		item = inTree[key]
# 		if 'name' in item.keys():
# 			if 'parent' in item.keys():
# 				outGraph.add_edge(item['name'],item['parent'], attr_dict={'type':'parentChild','phases':1})
# 				outGraph.node[item['name']]['type']=item['object']
# 				outGraph.node[item['name']]['pos']=(float(item.get('latitude',0)),float(item.get('longitude',0)))
# 			elif 'from' in item.keys():
# 				myPhase = phaseCount(item.get('phases','AN'))
# 				outGraph.add_edge(item['from'],item['to'],attr_dict={'type':item['object'],'phases':myPhase})
# 			elif item['name'] in outGraph:
# 				# Edge already led to node's addition, so just set the attributes:
# 				outGraph.node[item['name']]['type']=item['object']
# 			else:
# 				outGraph.add_node(item['name'],attr_dict={'type':item['object']})
# 			if 'latitude' in item.keys() and 'longitude' in item.keys():
# 				outGraph.node.get(item['name'],{})['pos']=(float(item['latitude']),float(item['longitude']))
# 	return outGraph

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

if __name__ == '__main__':
	''' Here we do the tests. '''

	# # Graph Test
	# import json
	# with open('data/Feeder/public_Olin Barre Geo.json','r') as inJ:
	# 	tree = json.load(inJ)['tree']
	# nxG = treeToNxGraph(tree)
	# x = latLonNxGraph(nxG)
	# plt.show()

	# # Parser Test
	# tokens = ['clock','{','clockey','valley','}','object','house','{','name','myhouse',';','object','ZIPload','{','inductance','bigind',';','power','newpower','}','size','234sqft','}']
	# simpleTokens = tokenizeGlm('./feeders/13 Node Ref Feeder Flat/main.glm')
	# print parseTokenList(simpleTokens)

	# # Recorder Attachment Test
	# with open('data/Feeder/public_Olin Barre Geo.json','r') as inJ:
	# 	tree = json.load(inJ)['tree']
	# attachRecorders(tree, 'Regulator', 'object', 'regulator')
	# attachRecorders(tree, 'Voltage', 'object', 'node')
	# print 'All the objects: ' + str([tree[x]['object'] for x in tree.keys() if 'object' in tree[x]])

	# # Testing The De-Embedding
	# from pprint import pprint
	# tree = parse('./feeders/13 Node Reference Feeder/main.glm')
	# fullyDeEmbed(tree)
	# #pprint(tree)
	# print sortedWrite(tree)

	# # groupSwingKids test
	# from pprint import pprint
	# tree = parse('./feeders/13 Node Ref Feeder Flat/main.glm')
	# groupSwingKids(tree)
	# pprint(tree)

	# # Time Adjustment Test
	# tree = parse('./feeders/Simple Market System/main.glm')
	# adjustTime(tree, 100, 'hours', '2000-09-01')
	# from pprint import pprint
	# pprint(tree)
	pass