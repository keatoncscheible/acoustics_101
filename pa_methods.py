from abc import ABC, abstractmethod
import random
import numpy as np
from PyQt5.QtWidgets import QComboBox, QWidget, QLabel, QTextEdit
from PyQt5.QtCore import pyqtSlot
from pyqtgraph import PlotWidget, ScatterPlotItem
from stimulus import EnvelopeGenerator, Stimulus, PureToneMono, PureToneStereo
from widgets.QFloatSlider import QFloatSlider


class PaMethods(ABC):
    """Physchoacoustics Methods Class"""

    def __init__(self):

        @property
        def stimulus(self):
            """Stimulus object used to generate audio stimulus for the test"""
            ...

        if not isinstance(self.stimulus, Stimulus):
            raise ValueError('stimulus must be a Stimulus object')

        # Create empty lists to log each stimulus parameter
        for parameter in self.stimulus.parameters:
            setattr(self, '{}_log'.format(parameter), [])

        @property
        def tests(self):
            """List of test names"""
            ...

        if not all(isinstance(test, str) for test in self.tests):
            raise ValueError(
                'tests must be a list of strings with the name of each test')

        self._active_test = self.tests[0]

    @abstractmethod
    def start_test(self):
        """Start the psychoacoustic test"""
        ...

    @abstractmethod
    def stop_test(self):
        """Stop the psychoacoustic test"""
        ...

    @abstractmethod
    def update_data(self):
        """Update relevant data for the psychoacoustic test"""
        ...

    def select_test(self, test):
        """Select a psychoacoustic test"""
        if test in self.tests:
            self._active_test = test
        else:
            raise ValueError(
                '{} is not a valid test. Valid tests are {}'.format(test, self.tests))

    def adjust_stimulus(self, **kwargs):
        """Adjust stimulus parameter"""
        for key, value in kwargs.items():
            assert key in self.stimulus.parameters, \
                '{} not in {} parameters. Available parameters are {}'.format(
                    key, self.stimulus.__class__(), self.stimulus.parameters)
            setattr(self.stimulus, key, value)

    def log_stimulus(self):
        """Log stimulus parameters"""
        for parameter in self.stimulus.parameters:
            parameter_attr = getattr(self.stimulus, parameter)
            if isinstance(parameter_attr, EnvelopeGenerator):
                parameter_data = parameter_attr.setpoint
            if isinstance(parameter_attr, int) or isinstance(parameter_attr, float):
                parameter_data = parameter_attr
            getattr(self, '{}_log'.format(parameter)).append(parameter_data)

    def print_logged_data(self):
        """Print logged data"""
        for parameter in self.stimulus.parameters:
            print('{}: {}'.format(parameter, getattr(
                self, '{}_log'.format(parameter))))

    def get_logged_data(self, parameter):
        return getattr(self, '{}_log'.format(parameter))


class MethodOfAdjustmentWidget(QWidget):
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
        super(MethodOfAdjustmentWidget, self).__init__()

    def showEvent(self, event):
        super().showEvent(event)
        test_name = self.testSelectorDropdown.currentText()
        self.configure_ui(test_name)

    def configure_ui(self, test):
        if test == 'Hearing Threshold':
            self.obj.configure_hearing_threshold_test()
        elif test == 'Tone Match':
            self.obj.configure_tone_match_test()
        elif test == 'Octave Match':
            self.obj.configure_octave_match_test()

        self.testInstructionsDialog.setText(
            self.obj.test_information['instructions'])

        self.stimulusControlLabel.setText(self.obj.stimulus_control['label'])

        self.stimulusControlSlider.setRange(
            self.obj.stimulus_control['min'], self.obj.stimulus_control['max'])
        self.stimulusControlSlider.precision = self.obj.stimulus_control['precision']
        self.stimulusControlSlider.pagePrecision = self.obj.stimulus_control['page_precision']
        self.stimulusControlSlider.value = self.obj.stimulus_control['default']

        self.testResultsPlot.plotItem.setTitle(self.obj.plot_control['title'])
        self.testResultsPlot.plotItem.setXRange(
            self.obj.plot_control['xmin'], self.obj.plot_control['xmax'])
        self.testResultsPlot.plotItem.setYRange(
            self.obj.plot_control['ymin'], self.obj.plot_control['ymax'])
        self.testResultsPlot.plotItem.enableAutoRange(y=True)
        self.testResultsPlot.plotItem.setAutoVisible(y=True)
        self.testResultsPlot.plotItem.setLabel(
            axis='left', text=self.obj.plot_control['ylabel'], units=self.obj.plot_control['yunits'])
        self.testResultsPlot.plotItem.setLabel(
            axis='bottom', text=self.obj.plot_control['xlabel'], units=self.obj.plot_control['xunits'])

    @pyqtSlot(str)
    def select_test(self, test):
        self.configure_ui(test)

    @pyqtSlot()
    def start_test(self):
        self.obj.start_test()

    @pyqtSlot()
    def stop_test(self):
        self.obj.stop_test()

    @pyqtSlot(float)
    def adjust_stimulus(self, value):
        self.obj.adjust_stimulus(value)

    @pyqtSlot()
    def update_data(self):
        self.obj.update_data()
        self.stimulusControlSlider.value = self.obj.stimulus_control['value']
        self.scatterPlot.addPoints(
            self.obj.test_results['independent'], self.obj.test_results['dependent'])


class MethodOfAdjustment(PaMethods):
    """Method of Adjustment"""

    def __init__(self):
        self.stimulus = PureToneMono()
        self.tests = ['Hearing Threshold', 'Tone Match', 'Octave Match']
        self.stimulus_control = {}
        self.test_control = {}
        self.test_results = {}
        self.plot_control = {}
        self.test_information = {}
        super().__init__()

    def start_test(self):
        self.stimulus.play()

    def stop_test(self):
        self.stimulus.stop()

    def adjust_stimulus(self, value):
        super().adjust_stimulus(**{self.stimulus_control['parameter']: value})

    def update_data(self):
        self.log_stimulus()

        if self._active_test == 'Hearing Threshold':
            self.update_hearing_threshold_test_data()
        elif self._active_test == 'Tone Match':
            self.update_tone_match_test_data()
        elif self._active_test == 'Octave Match':
            self.update_octave_match_test_data()

    def update_hearing_threshold_test_data(self):
        test_data = self.get_logged_data(self.test_control['parameter'])

        # Select a new test frequency
        # This algorithm randomly selects a new test frequency from the
        # parameter list. When there are no frequencies left in the parameter
        # list, a new list of frequencies is generated, where all the new
        # frequencies are equally spaced between the existing frequencies.
        self.test_control['parameter_list'] = list(
            set(self.test_control['parameter_list']) - set(test_data))
        if(len(self.test_control['parameter_list']) == 0):
            self.test_control['parameter_search_precision'] /= 2
            self.test_control['parameter_list'] = np.arange(
                self.test_control['parameter_search_precision'], self.test_control['max'],
                self.test_control['parameter_search_precision'])
            self.test_control['parameter_list'] = list(
                set(self.test_control['parameter_list']) - set(test_data))

        next_frequency = random.choice(
            self.test_control['parameter_list'])

        # Reset the volume to the default level
        self.stimulus_control['value'] = self.stimulus_control['default']
        # Adjust the frequency
        setattr(self.stimulus,
                self.test_control['parameter'], next_frequency)
        # Reset the volume to the default value
        setattr(self.stimulus,
                self.stimulus_control['parameter'], self.stimulus_control['default'])

        # Save the independent and dependent test results
        self.test_results['independent'] = self.get_logged_data(
            self.test_control['parameter'])
        self.test_results['dependent'] = self.get_logged_data(
            self.stimulus_control['parameter'])

    def update_tone_match_test_data(self):
        pass

    def update_octave_match_test_data(self):
        pass

    def configure_hearing_threshold_test(self):

        self.test_information['instructions'] = \
            '<ol>' \
            '<li>Start the test by pressing the <b>Start Test</b> button. You should hear a tone.</li><br>' \
            '<li>Use the slider to adjust the volume until the tone is just barely peceivable, then press the <b>Update Plot</b> button.</li><br>' \
            '<li>Repeat step 2 to capture additional data points.</li><br>' \
            '<li>Press the <b>Stop Test</b> button when you are finished.</li>' \
            '</ol>'


        self.stimulus_control['parameter'] = 'A'
        self.stimulus_control['min'] = -100
        self.stimulus_control['max'] = -40
        self.stimulus_control['default'] = -50
        self.stimulus_control['precision'] = 0.1
        self.stimulus_control['page_precision'] = 1
        self.stimulus_control['label'] = 'Volume'
        self.stimulus_control['value'] = self.stimulus_control['default']
        setattr(self.stimulus,
                self.stimulus_control['parameter'], self.stimulus_control['default'])

        self.test_control['parameter'] = 'f'
        self.test_control['min'] = 100
        self.test_control['max'] = 15000
        self.test_control['default'] = 1000
        self.test_control['value'] = self.test_control['default']
        self.test_control['parameter_search_precision'] = 1000
        self.test_control['parameter_list'] = np.arange(
            self.test_control['parameter_search_precision'], self.test_control['max'],
            self.test_control['parameter_search_precision'])
        setattr(self.stimulus,
                self.test_control['parameter'], self.test_control['default'])

        self.plot_control['title'] = 'Hearing Threshold Vs Frequency'
        self.plot_control['xmin'] = self.test_control['min']
        self.plot_control['xmax'] = self.test_control['max']
        self.plot_control['ymin'] = self.stimulus_control['min']
        self.plot_control['ymax'] = self.stimulus_control['max']
        self.plot_control['xlabel'] = 'Frequency'
        self.plot_control['xunits'] = 'Hz'
        self.plot_control['ylabel'] = 'Volume'
        self.plot_control['yunits'] = 'dB'

        self.test_results['independent'] = []
        self.test_results['dependent'] = []

    def configure_tone_match_test(self):
        pass

    def configure_octave_match_test(self):
        pass

# class MethodOfTracking(PaMethods):
#     def __init__(self):
#         """
#         """
#         pass


# class MagnitudeEstimation(PaMethods):
#     def __init__(self):
#         """
#         """
#         pass


# class YesNoProcedure(PaMethods):
#     def __init__(self):
#         """
#         """
#         pass


# class TwoIntervalForcedChoice(PaMethods):
#     def __init__(self):
#         """
#         """
#         pass


# class AdaptiveProcedure(PaMethods):
#     def __init__(self):
#         """
#         """
#         pass


# class ComparisonOfStimulusPairs(PaMethods):
#     def __init__(self):
#         """
#         """
#         pass
