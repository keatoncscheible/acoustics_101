from PyQt5.QtWidgets import QComboBox, QWidget, QLabel, QTextEdit
from PyQt5.QtCore import pyqtSlot
from pyqtgraph import PlotWidget, ScatterPlotItem
from .QFloatSlider import QFloatSlider
from PaMethods import MethodOfAdjustment


class QMethodOfAdjustment(QWidget):
    def __init__(self, parent):
        self.obj = MethodOfAdjustment(test='Tone Match')
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
        
        self._setupUi()

    def _setupUi(self):
        self._updateTestSelectorDropdown()
        self._updateTestInstructionsDialog()
        self._updateStimulusControlLabel()
        self._updateStimulusControlSlider()
        self._updateTestResultsPlot()
        self._clearTestResultsPlot()

    @pyqtSlot(str)
    def selectTest(self, test):
        self.obj.selectTest(test)
        self._setupUi()

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
        if self.obj.updateData():
            self._setStimulusControlSliderDefaultValue()
            self._updateTestResultsPlotData()
            self._autoscaleYTestResultsPlot()

    def _updateTestResultsPlot(self):
        self._updateTestResultsPlotTitle()
        self._updateTestResultsPlotXRange()
        self._updateTestResultsPlotYRange()
        self._updateTestResultsPlotXLabel()
        self._updateTestResultsPlotYLabel()

    def _updateStimulusControlSlider(self):
        self._setStimulusControlSliderDefaultValue()
        self._updateStimulusControlSliderRange()
        self._updateStimulusControlSliderPrecision()
        self._updateStimulusControlSliderPagePrecision()
        

    def _updateTestSelectorDropdown(self):
        self.testSelectorDropdown.setCurrentText(self.obj.selectedTest)

    def _updateTestInstructionsDialog(self):
        self.testInstructionsDialog.setText(
            self.obj.testInformation['instructions'])

    def _updateStimulusControlLabel(self):
        self.stimulusControlLabel.setText(self.obj.userStimulus['label'])

    def _updateStimulusControlSliderRange(self):
        self.stimulusControlSlider.setRange(
            self.obj.userStimulus['min'], self.obj.userStimulus['max'])

    def _updateStimulusControlSliderPrecision(self):
        self.stimulusControlSlider.precision = self.obj.userStimulus['precision']

    def _updateStimulusControlSliderPagePrecision(self):
        self.stimulusControlSlider.pagePrecision = self.obj.userStimulus['pagePrecision']

    def _setStimulusControlSliderDefaultValue(self):
        self.stimulusControlSlider.value = self.obj.userStimulus['default']

    def _updateTestResultsPlotData(self):
        self.scatterPlot.addPoints(
            self.obj.testResults['independent'], self.obj.testResults['dependent'])

    def _updateTestResultsPlotTitle(self):
        self.testResultsPlot.plotItem.setTitle(self.obj.plotControl['title'])

    def _updateTestResultsPlotXRange(self):
        self.testResultsPlot.plotItem.setXRange(
            self.obj.plotControl['xmin'], self.obj.plotControl['xmax'])

    def _updateTestResultsPlotYRange(self):
        self.testResultsPlot.plotItem.setYRange(
            self.obj.plotControl['ymin'], self.obj.plotControl['ymax'])

    def _updateTestResultsPlotXLabel(self):
        self.testResultsPlot.plotItem.setLabel(
            axis='bottom', text=self.obj.plotControl['xlabel'], units=self.obj.plotControl['xunits'])

    def _updateTestResultsPlotYLabel(self):
        self.testResultsPlot.plotItem.setLabel(
            axis='left', text=self.obj.plotControl['ylabel'], units=self.obj.plotControl['yunits'])

    def _autoscaleYTestResultsPlot(self):
        self.testResultsPlot.plotItem.setAutoVisible(y=True)
        self.testResultsPlot.plotItem.enableAutoRange(y=True)

    def _clearTestResultsPlot(self):
        self.scatterPlot.clear()
