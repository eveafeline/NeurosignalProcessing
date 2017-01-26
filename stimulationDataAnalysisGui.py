
import mainFunctions as mf
import variables

import time
from random import randint

import re
import sys
import signal
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


from PyQt5.uic import loadUiType
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
 
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

Ui_MainWindow, QMainWindow = loadUiType('dataProcessingGUI.ui')

class Main(QMainWindow, Ui_MainWindow):
	def __init__(self, ):
		super(Main, self).__init__()
		self.setupUi(self)
		self.btnOpenFile.clicked.connect(self.getFile)
		self.btnLoadFiltered.clicked.connect(self.loadFilteredData)
		self.btnLoadStimS.clicked.connect(self.loadContStimulationWindows)
		self.btnLoadStimS.clicked.connect(self.loadStimPerIdx)
		self.btnLoadRaw.clicked.connect(self.loadRawData)

		self.btnLoadOverlay.clicked.connect(self.loadOverlay)
		self.btnLoadAvg.clicked.connect(self.loadAvg)

		self.cmbStimPer.currentIndexChanged.connect(self.loadStimPerIdx)
		self.btnNextStim.clicked.connect(self.loadNextStim)
		self.btnPreviousStim.clicked.connect(self.loadPreviousStim)

		self.btnUpdateParam.clicked.connect(self.resetVariables)
		self.btnClearGraphs.clicked.connect(self.clearAllLayouts)

	def getFile(self):
		dataFileName = QFileDialog.getOpenFileName(self, 'Open file', 
         'C:\Users\eveaf\Documents\Artifact_Cancellation\dataProcessingGui\dataSource',"Text files (*.csv)")
		idx = str(dataFileName).index('2016')
		variables.fileName = str(dataFileName)[idx:idx+19]
		self.txtFileName.setText(variables.fileName)
		variables.rawFileName='./dataSource/'+variables.fileName+'_source1.csv'

	def loadFilteredData(self):
		self.tabsStimAll.setCurrentIndex(0)
		start = time.time()
		figAll = Figure()
		subAll = figAll.add_subplot(111)
		subAll.plot(variables.dataTimes, variables.dataFiltValues)
		self.addPlot(figAll, self.layoutFiltAll)
		end = time.time()
		# print('all data plot time: '+ str(end-start)+'\n')

	def loadContStimulationWindows(self):
		self.tabsStimAll.setCurrentIndex(1)
		allStimWindows = mf.getContWinStimArr(variables.dataFiltValues, len(variables.stimTimeIdx), len(variables.stimTimeIdx), variables.stimTimeIdx, variables.pre_stim, variables.post_stim, variables.fs)
		allStimWinTime = mf.getPlotTime(allStimWindows, variables.fs)
		figStim = Figure()
		subStim = figStim.add_subplot(111)
		subStim.plot(allStimWinTime, allStimWindows)
		self.addPlot(figStim, self.layoutStim)

		numOfStimS = range(0,len(variables.stimTimeIdx))
		self.cmbStimPer.addItems(map(str, numOfStimS))
		self.cmbStimPer.setCurrentIndex(randint(0,len(numOfStimS)))

	def loadRawData(self):
		self.tabsStimAll.setCurrentIndex(2)
		figRaw = Figure()
		subRaw = figRaw.add_subplot(111)
		rawTime = mf.getPlotTime(variables.rawDataValues, variables.fs)
		subRaw.plot(rawTime, variables.rawDataValues)
		self.addPlot(figRaw, self.layoutRaw)
	
	def loadOverlay(self):
		self.tabsOverlayAvg.setCurrentIndex(0)
		stimS = re.split('; |, |\*|\n|\\s',str(self.txtWhichStimS.toPlainText()))
		whichStims = map(int, stimS)
		variables.yMin = float(self.txtYMin.text())
		variables.yMax = float(self.txtYMax.text())
		figOverlay = Figure()
		subOverlay = figOverlay.add_subplot(111)
		pre_stimIdx = int(variables.pre_stim*variables.fs)
		post_stimIdx = int(variables.post_stim*variables.fs)
		for whichStim in whichStims:
			stimIdx = variables.stimTimeIdx[whichStim]		
			startIdx = stimIdx - pre_stimIdx
			endIdx = stimIdx + post_stimIdx	
			dataValues = mf.dcRemove(variables.dataFiltValues[startIdx:endIdx], variables.fs)
			time = mf.getPlotTime(dataValues, variables.fs)
			subOverlay.plot(time, dataValues)
		subOverlay.set_ylim([variables.yMin, variables.yMax])
		self.addPlot(figOverlay, self.layoutOverlay)

	def loadAvg(self):
		self.tabsOverlayAvg.setCurrentIndex(1)
		stimS = re.split('; |, |\*|\n|\s',str(self.txtWhichStimS.toPlainText()))
		whichStims = map(int, stimS)
		variables.yMin = float(self.txtYMin.text())
		variables.yMax = float(self.txtYMax.text())
		figAvg = Figure()
		subAvg = figAvg.add_subplot(111)
		avgStimValues = mf.getStimAvgDataPerIdx(variables.dataFiltValues, whichStims, variables.stimTimeIdx, variables.pre_stim, variables.post_stim, variables.fs)
		avgTime = mf.getPlotTime(avgStimValues, variables.fs)
		subAvg.plot(avgTime, avgStimValues)
		subAvg.set_ylim([variables.yMin, variables.yMax])
		self.addPlot(figAvg, self.layoutAvg)

	def loadStimPerIdx(self):
		currentIdx = int(self.cmbStimPer.currentText())
		self.plotStimPerIdx(currentIdx)

	def loadNextStim(self):
		currentIdx = int(self.cmbStimPer.currentText())+1
		self.plotStimPerIdx(currentIdx)
		self.cmbStimPer.setCurrentIndex(self.cmbStimPer.currentIndex()+1)

	def loadPreviousStim(self):
		currentIdx = int(self.cmbStimPer.currentText())-1
		self.plotStimPerIdx(currentIdx)
		self.cmbStimPer.setCurrentIndex(self.cmbStimPer.currentIndex()-1)

	def plotStimPerIdx(self, currIdx):
		whichStim = int(currIdx)
		yMin = float(self.txtYMin.text())
		yMax = float(self.txtYMax.text())

		pre_stimIdx = int(variables.pre_stim*variables.fs)
		post_stimIdx = int(variables.post_stim*variables.fs)
		stimIdx = variables.stimTimeIdx[whichStim]		
		startIdx = stimIdx - pre_stimIdx
		endIdx = stimIdx + post_stimIdx	
		dataValues = mf.dcRemove(variables.dataFiltValues[startIdx:endIdx], variables.fs)
		time = mf.getPlotTime(dataValues, variables.fs)	
		time[:] = [x*1000 for x in time]
		stimValue = variables.dataFiltValues[stimIdx]
		stimTime = time[pre_stimIdx]
		
		figPerStim = Figure()
		subPerStim = figPerStim.add_subplot(111)
		subPerStim.plot(time, dataValues)
		subPerStim.plot(stimTime, stimValue, 'o')
		subPerStim.set_ylim([yMin, yMax])
		self.addPlot(figPerStim, self.layoutPerStim)

	def clearAllLayouts(self):
		self.clearLayout(self.layoutFiltAll)
		self.clearLayout(self.layoutStim)
		self.clearLayout(self.layoutRaw)
		self.clearLayout(self.layoutOverlay)
		self.clearLayout(self.layoutAvg)
		self.clearLayout(self.layoutPerStim)
		self.cmbStimPer.clear()

	def addPlot(self, fig, layout):
		self.clearLayout(layout)
		self.canvas = FigureCanvas(fig)
		layout.addWidget(self.canvas)
		self.canvas.draw()
		self.toolbar = NavigationToolbar(self.canvas, self, coordinates=True)
		layout.addWidget(self.toolbar)

	def clearLayout(self, layout):
	    while layout.count():
	        child = layout.takeAt(0)
	        if child.widget() is not None:
	            child.widget().deleteLater()
	        elif child.layout() is not None:
	            clearLayout(child.layout())

	def resetVariables(self):
		variables.fs = self.sbFs.value()*1e3
		variables.invert = self.chkInvert.checkState()
		variables.timeDelay= self.sbTimeDelay.value()*1e-3 # time delay between trigger and stimulation
		variables.thres_up = self.sbTrigUp.value() # threshold to detect rising edge
		variables.thres_down = self.sbTrigDown.value() # threshold to detect falling edge
		variables.pre_stim = self.sbPreStim.value()*1e-3 # time before stimulation to start stimulation window
		variables.post_stim = self.sbPostStim.value()*1e-3 # time after stimulation to end stimulation window
		variables.order = self.sbOrder.value() # filter order
		variables.maxReadTime = self.sbMaxReadTime.value()
		variables.maxRows = variables.maxReadTime*variables.fs

		variables.f_high = self.sbFHigh.value()
		variables.f_low = self.sbFLow.value()

		start = time.time()
		(variables.dataValues, variables.dataTimes, variables.triggerValues) = mf.loadArtifactData(variables.fileName, variables.maxReadTime, variables.fs, variables.invert)
		end = time.time()
		print('loadartifact time: ' + str(end-start)+'\n')
		start = time.time()
		variables.rawDataValues = mf.readCsvFile(fileName='./dataSource/'+variables.fileName+'_source1.csv', maxRows=variables.maxRows)
		end = time.time()
		print('readCsvFile time: '+str(end-start)+'\n')
		start = time.time()
		variables.dataFiltValues = mf.filterData(variables.dataValues, f_low=variables.f_low, f_high=variables.f_high, fs=variables.fs, order=variables.order)
		end = time.time()
		print('filterData: '+str(end-start)+'\n')

		variables.stimTimeIdx = mf.findStimIdx(variables.triggerValues, variables.thres_up, variables.thres_down, variables.timeDelay, variables.fs)
		variables.triggerTimeIdx = mf.findTriggerIdx(variables.triggerValues, variables.thres_up, variables.thres_down)
		variables.stimTimes = mf.getValByIdx(variables.stimTimeIdx, variables.dataTimes)
		variables.dataStimValues = mf.getValByIdx(variables.stimTimeIdx, variables.dataFiltValues)

		# variables.pulse_width = str(self.txtPulseWidth.text())
		# variables.i_stim = str(self.txtIStim.text())

if __name__ == '__main__':
	import sys
	from PyQt5.QtGui import *
	from PyQt5.QtWidgets import *

	app = QApplication(sys.argv)
	main = Main()
	main.show()
	sys.exit(app.exec_())
