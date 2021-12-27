from PyQt5.QtWidgets import QComboBox, QWidget, QLabel, QTextEdit
from PyQt5.QtCore import pyqtSlot
from pyqtgraph import PlotWidget, ScatterPlotItem
from .QFloatSlider import QFloatSlider
from PaMethods import MethodOfAdjustment

class QMethodOfAdjustment(QWidget):
    def __init__(self, parent):
        self.obj = MethodOfAdjustment()
        self.stimulusControlLabel = parent.findChild(
            QLabel, 'stimulusControlLabel')
        self.stimulusControlSlider = parent.findChild(
            QFloatSlider, 'stimulusControlSlider')
        self.testSelectorDropdown = parent.findChild(
            QComboBox, 'testSelectorDropdown')
        self.testResultsPlot = parent.findChild(
            PlotWidget, 'testResultsPlot')
        self.scatterPlot = ScatterPlotItem()
        self.testResultsPlot.addItem(self.scatterPlot)
        self.testInstructionsDialog = parent.findChild(
            QTextEdit, 'testInstructionsDialog')
        super(QMethodOfAdjustment, self).__init__()

    def showEvent(self, event):
        super().showEvent(event)
        testName = self.testSelectorDropdown.currentText()
        self.configureUi(testName)

    def configureUi(self, test):
        self.scatterPlot.clear()
        if test == 'Hearing Threshold':
            self.obj.configureHearingThresholdTest()
        elif test == 'Tone Match':
            self.obj.configureToneMatchTest()
        elif test == 'Octave Match':
            self.obj.configureOctaveMatchTest()

        self.testInstructionsDialog.setText(
            self.obj.testInformation['instructions'])

        self.stimulusControlLabel.setText(self.obj.stimulusControl['label'])

        self.stimulusControlSlider.setRange(
            self.obj.stimulusControl['min'], self.obj.stimulusControl['max'])
        self.stimulusControlSlider.precision = self.obj.stimulusControl['precision']
        self.stimulusControlSlider.pagePrecision = self.obj.stimulusControl['pagePrecision']
        self.stimulusControlSlider.value = self.obj.stimulusControl['default']

        self.testResultsPlot.plotItem.setTitle(self.obj.plotControl['title'])
        self.testResultsPlot.plotItem.setXRange(
            self.obj.plotControl['xmin'], self.obj.plotControl['xmax'])
        self.testResultsPlot.plotItem.setYRange(
            self.obj.plotControl['ymin'], self.obj.plotControl['ymax'])
        self.testResultsPlot.plotItem.enableAutoRange(y=True)
        self.testResultsPlot.plotItem.setAutoVisible(y=True)
        self.testResultsPlot.plotItem.setLabel(
            axis='left', text=self.obj.plotControl['ylabel'], units=self.obj.plotControl['yunits'])
        self.testResultsPlot.plotItem.setLabel(
            axis='bottom', text=self.obj.plotControl['xlabel'], units=self.obj.plotControl['xunits'])

    @pyqtSlot(str)
    def selectTest(self, test):
        self.obj.selectTest(test)
        self.configureUi(test)

    @pyqtSlot()
    def startTest(self):
        self.obj.startTest()

    @pyqtSlot()
    def stopTest(self):
        self.obj.stopTest()

    @pyqtSlot(float)
    def adjustStimulus(self, value):
        self.obj.adjustStimulus(value)

    @pyqtSlot()
    def updateData(self):
        self.obj.updateData()
        self.stimulusControlSlider.value = self.obj.stimulusControl['value']
        self.scatterPlot.addPoints(
            self.obj.testResults['independent'], self.obj.testResults['dependent'])

