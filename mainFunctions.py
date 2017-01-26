import csv
import numpy as np
from scipy.signal import butter, lfilter, filtfilt
import matplotlib as mpl
import matplotlib.pyplot as plt

import time

# function for reading in CSV file, return array of data from CSV file
def readCsvFile(fileName, maxRows=-1):
	csvFilePointer = open(fileName, 'rb')
	start = time.time()
	dataStream = csv.reader(csvFilePointer)
	end = time.time()
	print('csv.reader time: '+str(end-start)+'\n')
	dataValues = []
	faultyValueLocations=[]
	prevRowFloat=0.0
	counter=0
	start = time.time()
	for row in dataStream:
		try:
			rowFloat=float(row[0])
			prevRowFloat = rowFloat
		except: break
			# rowFloat=prevRowFloat
			# faultyValueLocations.append(counter)
		# finally:
		dataValues.append(rowFloat)
		counter+=1
		if counter==maxRows: break
	end = time.time()
	print('for row in dataStream time: '+str(end-start)+'\n')
	return dataValues

# function to load artifact cancellation data to current data array
# dataFs = sampling in samples per second: currently set to 50e3 in one second
# if readTime = -1 all data will be plotted, invert = true with current data set
def loadArtifactData(fileStamp, maxReadTime, dataFs, invert):
	filePath = './dataSource/'
	data1fileName = filePath+fileStamp+'_cancelled.csv'
	trigger1fileName = filePath+fileStamp+'_source2.csv'
	inv1 = -1.0 if invert==True else 1.0
	data1Values = [inv1*x for x in readCsvFile(fileName=data1fileName, maxRows=maxReadTime*dataFs)]
	trigger1Values = readCsvFile(fileName=trigger1fileName, maxRows=maxReadTime*dataFs)

	#set time scale
	data1Time = np.arange(len(data1Values)*1.0)/dataFs

	return data1Values, data1Time, trigger1Values

# saves the CSV file of specific dataArr, can be used to store windows
def saveCSV(dataArr, fileName):
	filePath = './dataOutput/'
	csvfile = filePath+fileName+'.csv'
	with open(csvfile, "w") as output:
		writer = csv.writer(output, lineterminator='\n')
		for data in dataArr:
			writer.writerow([data])

# filtering methods
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_lowpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, high, btype='low')
    return b, a

def filterData(dataIn, f_low, f_high, fs, order):
	(b,a)=butter_lowpass(lowcut=f_low, highcut=f_high, fs=fs, order=order)
	dataOut = lfilter(b, a, dataIn)
	return dataOut

# added 160919 60 hz filter
def filt_notch(dataIn, freq, bandwidth, fs, order):
	nyq  = 0.5*fs
	low  = (freq - bandwidth/2.0)/nyq
	high = (freq + bandwidth/2.0)/nyq
	b, a = butter(order, [low, high], btype='bandstop', analog=False, output='ba')
	dataOut = filtfilt(b, a, dataIn)
	return dataOut

# create new int array to get idx of trigger
# returns array of trigger locations in data array (indexes)
def findTriggerIdx(triggerArr, thres_up, thres_down):
	triggerIdxArr = []
	i = 0
	n = 0
	while i < len(triggerArr):
		while triggerArr[i] < thres_up:
			i+=1
			if i >= len(triggerArr): break		
		if i >= len(triggerArr): break		
		triggerIdxArr.append(i)		
		while triggerArr[i] > thres_down:
			i+=1
	return triggerIdxArr

# find the location of the stimulation using the location of the trigger (indexes in array)
# returns array of stimulation locations in data array (indexes)
def findStimIdx(triggerArr, thres_up, thres_down, timeDelay, fs):
	addIdx = int(timeDelay*fs)
	resultArr = [i+addIdx for i in findTriggerIdx(triggerArr, thres_up, thres_down)]
	return resultArr

# return array of values of another array by index
def getValByIdx(idxArr, valArr):
	resultArr = []
	idx = 0
	for idx in idxArr:
		if idx < len(valArr):
			resultArr.append(valArr[idx])
	return resultArr

# function to create an array of time for an array
def getPlotTime(inputArr, fs):
	resultArr = []
	for idx, stim in enumerate(inputArr):
		resultArr.append((idx / fs)-5e-3)
	return resultArr

def getStimDataPerIdx(dataArr, whichStim, stimIdxArr, pre_stim, post_stim, fs):
	pre_stimIdx = int(pre_stim*fs)
	post_stimIdx = int(post_stim*fs)
	stimIdx = stimIdxArr[whichStim]		
	startIdx = stimIdx - pre_stimIdx
	endIdx = stimIdx + post_stimIdx	 
	dataValues = dataArr[startIdx:endIdx]	
	return dataValues

# get average of stimulation window based on a list of stimulation indices
def getStimAvgDataPerIdx(dataArr, whichStimIdxArr, stimIdxArr, pre_stim, post_stim, fs):
	pre_stimIdx = int(pre_stim*fs)
	post_stimIdx = int(post_stim*fs)
	resultArr = []
	for whichStim in whichStimIdxArr:	 # loop through whichStimIdxArr
		stimIdx = stimIdxArr[whichStim]	
		startIdx = stimIdx - pre_stimIdx	 # for every trigger idx, find before and after index
		endIdx = stimIdx + post_stimIdx
		if not resultArr:	# if resultArr is empty, add the data set into empty array
			for i in range(startIdx, endIdx):
				resultArr.append(dataArr[i])
		else:	# if resultArr is not empty, sum data point of new data set into existing resultArr
			n = 0
			for i in range(startIdx, endIdx):
				resultArr[n] += dataArr[i]
				n+=1
	resultArr[:] = [ x / len(whichStimIdxArr) for x in resultArr]	# divide each element in array by stimulation window count
	return resultArr

# plot per stimulation by index of stimulation with circle at stimulation
def plotDataPerIdx(dataArr, whichStim, stimIdxArr, pre_stim, post_stim, fs, yMin, yMax):
	pre_stimIdx = int(pre_stim*fs)
	post_stimIdx = int(post_stim*fs)
	plt.figure(whichStim)
	stimIdx = stimIdxArr[whichStim]		
	startIdx = stimIdx - pre_stimIdx
	endIdx = stimIdx + post_stimIdx	
	dataValues = dcRemove(dataArr[startIdx:endIdx], fs)
	time = getPlotTime(dataValues, fs)	
	time[:] = [x*1000 for x in time]
	stimValue = dataArr[stimIdx]
	stimTime = time[pre_stimIdx]
	plt.plot(time, dataValues)
	plt.plot(stimTime, stimValue, 'o')
	plt.ylim(yMin, yMax)
	plt.xlabel('mSec')
	plt.ylabel('mV')

# plot per stimulation by index of stimulation with circle at stimulation
def plotDataPerIdxFam(dataArr, whichStimIdxArr, stimIdxArr, pre_stim, post_stim, fs, figureNum):
	pre_stimIdx = int(pre_stim*fs)
	post_stimIdx = int(post_stim*fs)
	plt.figure(figureNum)
	for whichStim in whichStimIdxArr:
		stimIdx = stimIdxArr[whichStim]		
		startIdx = stimIdx - pre_stimIdx
		endIdx = stimIdx + post_stimIdx	
		dataValues = dataArr[startIdx:endIdx]
		time = getPlotTime(dataValues, fs)
		plt.plot(time, dataValues)

def plotAvgStimPerIdx(dataArr, whichStimIdxArr, stimIdxArr, pre_stim, post_stim, fs, figure):
	avgStimValues = getStimAvgDataPerIdx(dataArr, whichStimIdxArr, stimIdxArr, pre_stim, post_stim, fs)
	avgTime = getPlotTime(avgStimValues, fs)
	figure.plot(avgTime, avgStimValues)

# added 160919 to remove bias for overlay
def plotDataFamDcRemoved(dataArr, whichStimIdxArr, stimIdxArr, pre_stim, post_stim, fs, figure):
	pre_stimIdx = int(pre_stim*fs)
	post_stimIdx = int(post_stim*fs)
	for whichStim in whichStimIdxArr:
		stimIdx = stimIdxArr[whichStim]		
		startIdx = stimIdx - pre_stimIdx
		endIdx = stimIdx + post_stimIdx	
		dataValues = dcRemove(dataArr[startIdx:endIdx], fs)
		time = getPlotTime(dataValues, fs)
		figure.plot(time, dataValues)

def dcRemove(dataArr, fs):
	resultArr = dataArr
	endIdx = int(4e-3*fs)
	num = sum(resultArr[:endIdx])/len(resultArr[:endIdx])	
	resultArr[:] = [ x - num for x in dataArr]
	return resultArr

# get array of continous stimulation windows per stimulation index
def getContWinStimArr(dataArr, stimFromEnd, stimCount, stimIdxArr, pre_stim, post_stim, fs):
	pre_stimIdx = int(pre_stim*fs)
	post_stimIdx = int(post_stim*fs)
	n = len(stimIdxArr)-stimFromEnd
	resultArr = []
	for i in range(0, stimCount):
		stimIdx = stimIdxArr[n]
		if (stimIdx + post_stimIdx) > len(dataArr):
			n-=1
			stimIdx = stimIdxArr[n]		
		startIdx = stimIdx - pre_stimIdx
		endIdx = stimIdx + post_stimIdx
		newDataArr = dataArr[startIdx:endIdx]
		resultArr.extend(newDataArr)
		n+= 1
	return resultArr

# get array of idx positions to stimulation window
def getContWinStimPos(dataArr, stimFromEnd, stimCount, stimIdxArr, pre_stim, post_stim, fs):
	pre_stimIdx = int(pre_stim*fs)
	post_stimIdx = int(post_stim*fs)
	n = len(stimIdxArr)-stimFromEnd
	temp = []
	resultArr = []
	for i in range(0, stimCount):
		stimIdx = stimIdxArr[n]
		if (stimIdx + post_stimIdx) > len(dataArr):
			n-=1
			stimIdx = stimIdxArr[n]		
		startIdx = stimIdx - pre_stimIdx
		endIdx = stimIdx + post_stimIdx
		newDataArr = dataArr[startIdx:endIdx]
		temp.extend(newDataArr)
		resultArr.append(len(temp)-post_stimIdx-1)
		n+= 1
	return resultArr

# function to create a continuous graph of all stimulation windows from the data set
def contAllStimWindows(fileName, dataArr, stimTimeIdx, pre_stim, post_stimIdx, fs):
	allStimWindows = getContWinStimArr(dataArr, len(stimTimeIdx), len(stimTimeIdx), stimTimeIdx, pre_stim, post_stim, fs)
	allStimWinTime = getPlotTime(allStimWindows, fs)
	allStimIdx = getContWinStimPos(dataArr, len(stimTimeIdx), len(stimTimeIdx), stimTimeIdx, pre_stim, post_stim, fs)
	allStimValues = getValByIdx(allStimIdx, allStimWindows)
	allStimTime = getValByIdx(allStimIdx, allStimWinTime) 
	plt.figure(1)
	plt.plot(allStimWinTime, allStimWindows)
	plt.plot(allStimTime, allStimValues, 'o')
	for i, num in enumerate(allStimValues):
		plt.annotate(str(i), (allStimTime[i], allStimValues[i]))
	plt.title('All Stimulation Window Filtered n='+str(order)+'_'+fileName)
	plt.xlabel('Sec')
	plt.ylabel('mV')
