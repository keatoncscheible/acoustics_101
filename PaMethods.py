from abc import ABC, abstractmethod
import random
import numpy as np
from stimulus import EnvelopeGenerator, Stimulus, PureToneMono, PureToneStereo, VolumeMode


class PaMethods(ABC):
    """Physchoacoustics Methods Class"""

    def __init__(self):

        @property
        def tests(self):
            """List of test names"""
            ...

        if not all(isinstance(test, str) for test in self.tests):
            raise ValueError(
                'tests must be a list of strings with the name of each test')

        @property
        def stimulus(self):
            """Stimulus object used to generate audio stimulus for the test"""
            ...

        if not isinstance(self.stimulus, Stimulus):
            raise ValueError('stimulus must be a Stimulus object')

        @property
        def userStimulus(self):
            ...

        requiredUserStimulusKeys = [
            'parameter', 'min', 'max', 'default', 'precision', 'pagePrecision', 'label']
        for key in requiredUserStimulusKeys:
            if key not in self.userStimulus.keys():
                raise ValueError('Missing userStimulus["{}"]'.format(key))

        @property
        def testStimulus(self):
            ...

        requiredTestStimulusKeys = [
            'parameter', 'min', 'max', 'default', 'parameterSearchPrecision', 'parameterList']
        for key in requiredTestStimulusKeys:
            if key not in self.testStimulus.keys():
                raise ValueError('Missing testStimulus["{}"]'.format(key))

        @property
        def testResults(self):
            ...

        requiredTestResultsKeys = ['independent', 'dependent']
        for key in requiredTestResultsKeys:
            if key not in self.testResults.keys():
                raise ValueError('Missing testStimulus["{}"]'.format(key))

        @property
        def plotControl(self):
            ...

        requiredPlotControlKeys = [
            'title', 'xmin', 'xmax', 'ymin', 'ymax', 'xlabel', 'xunits', 'ylabel', 'yunits']
        for key in requiredPlotControlKeys:
            if key not in self.plotControl.keys():
                raise ValueError('Missing plotControl["{}"]'.format(key))

        @property
        def testInformation(self):
            ...

        requiredTestInformationKeys = ['instructions']
        for key in requiredTestInformationKeys:
            if key not in self.testInformation.keys():
                raise ValueError('Missing testInformation["{}"]'.format(key))

    @abstractmethod
    def _configureTest(self):
        """Configure a test based on the test name

        This method should setup the following dictionaries with the required
        information:

            self.userStimulus
            self.testStimulus
            self.testResults
            self.plotControl
            self.testInformation 

        The required infromation is listed in the below the property 
        declarations in the above code.
        """
        ...

    @abstractmethod
    def _setStimulus(self):
        """Set the stimulus for each test

        This method should set self.stimulus to a child of the 'Stimulus'  
        class for each test defined in self.tests. The stimulus should be set
        according to the selected test. For example:

            if self.selectedTest == 'Test 1':
                self.stimulus = PureToneMono()
            elif self.selectedTest == 'Test 2':
                self.stimulus = PureToneStereo()
            .
            .
            .
        """
        ...

    @abstractmethod
    def updateData(self):
        """Update relevant data for the test when the test is in progress.

        When implementing the updateData() method, the user should first call
        the superclass updateData() function. This will return True if there 
        is data to be updated and False if no updates are needed. If there is 
        data to update, the following things should be done:

            1. Update self.testResults['independent'] and self.testResults['dependent']
               with any new values to add to the test results plot

            2. Update the test stimulus and user stimulus values for the next test

        An example implementation of the updateData function is as follows:

            if super().updateData():
                if self.selectedTest == 'Test 1':
                    self.updateTest1Data()
                elif self.selectedTest == 'Test 2':
                    self.updateTest2Data()
        """
        if not self._testInProgress:
            return False
        self._logStimulus()
        return True

    @property
    def selectedTest(self):
        return self._selectedTest

    def selectTest(self, test=None):
        """Select a test

        Setup the stimulus, configure the test parameters and setup logs for
        the selected test. If no test name was provided, the first test in 
        self.tests will be selected by default. 
        """

        self._testInProgress = False

        # Default to first test in test list
        if test is None:
            test = self.tests[0]

        if test in self.tests:

            # Stop stimulus if there is one running
            try:
                self.stimulus.done()
            except AttributeError:
                pass

            self._selectedTest = test
            self._setStimulus()
            self._configureTest()
            self._resetStimulusLogs()
        else:
            raise ValueError(
                '{} is not a valid test. Valid tests are {}'.format(test, self.tests))

    def startTest(self):
        """Start the test"""
        self.stimulus.play()
        self._testInProgress = True

    def stopTest(self):
        """Stop the test"""
        self.stimulus.stop()
        self._testInProgress = False

    def adjustStimulus(self, value):
        """Adjust the user controlled stimulus parameter"""
        setattr(self.stimulus, self.userStimulus['parameter'], value)

    def _resetStimulusLogs(self):
        """Delete any existing stimulus logs and create new logs for each 
        stimulus parameter.
        """
        # Delete logs
        for parameter in dir(self):
            if '_log' in parameter and parameter != '_logStimulus':
                delattr(self, parameter)

        # Create new logs
        for parameter in self.stimulus.parameters:
            setattr(self, '{}_log'.format(parameter), [])

    def _logStimulus(self):
        """Log stimulus parameters"""
        for parameter in self.stimulus.parameters:
            parameterAttr = getattr(self.stimulus, parameter)
            if isinstance(parameterAttr, EnvelopeGenerator):
                parameterData = parameterAttr.setpoint
            if isinstance(parameterAttr, int) or isinstance(parameterAttr, float) \
                    or isinstance(parameterAttr, VolumeMode):
                parameterData = parameterAttr
            getattr(self, '{}_log'.format(parameter)).append(parameterData)

    def _getLoggedStimulusData(self, parameter):
        """Get logged stimulus data by the parameter name"""
        return getattr(self, '{}_log'.format(parameter))

    def _printLoggedData(self):
        """Print logged stimulus data"""
        for parameter in self.stimulus.parameters:
            print('{}: {}'.format(parameter, getattr(
                self, '{}_log'.format(parameter))))


class MethodOfAdjustment(PaMethods):
    """Method of Adjustment"""

    def __init__(self, test=None):

        self.userStimulus = {}
        self.testStimulus = {}
        self.testResults = {}
        self.plotControl = {}
        self.testInformation = {}

        self.tests = ['Hearing Threshold', 'Tone Match', 'Octave Match']
        self.selectTest(test)

        super().__init__()

    def _configureTest(self):
        """Configure test"""

        if self.selectedTest == 'Hearing Threshold':
            self._configureHearingThresholdTest()
        elif self.selectedTest == 'Tone Match':
            self._configureToneMatchTest()
        elif self.selectedTest == 'Octave Match':
            self._configureOctaveMatchTest()

    def _setStimulus(self):
        """Set stimulus based on the currently selected test"""
        if self.selectedTest == 'Hearing Threshold':
            self.stimulus = PureToneMono(A=-40)
        elif self.selectedTest == 'Tone Match':
            self.stimulus = PureToneStereo(A_L=-40, A_R=-40)
        elif self.selectedTest == 'Octave Match':
            self.stimulus = PureToneStereo(A_L=-40, A_R=-40)

    def updateData(self):
        if super().updateData():
            if self.selectedTest == 'Hearing Threshold':
                self.updateHearingThresholdTestData()
            elif self.selectedTest == 'Tone Match':
                self.updateToneMatchTestData()
            elif self.selectedTest == 'Octave Match':
                self.updateOctaveMatchTestData()
            return True
        return False

    def _configureHearingThresholdTest(self):

        self.testInformation['instructions'] = \
            '<ol>' \
            '<li>Start the test by pressing the <b>Start Test</b> button. You should hear a tone.</li><br>' \
            '<li>Use the slider to adjust the volume until the tone is just barely peceivable, then press the <b>Update Plot</b> button.</li><br>' \
            '<li>Repeat step 2 to capture additional data points.</li><br>' \
            '<li>Press the <b>Stop Test</b> button when you are finished.</li>' \
            '</ol>'

        self.userStimulus['parameter'] = 'A'
        self.userStimulus['min'] = -100
        self.userStimulus['max'] = -40
        self.userStimulus['default'] = -40
        self.userStimulus['precision'] = 0.1
        self.userStimulus['pagePrecision'] = 1
        self.userStimulus['label'] = 'Volume'
        setattr(self.stimulus,
                self.userStimulus['parameter'], self.userStimulus['default'])

        self.testStimulus['parameter'] = 'f'
        self.testStimulus['min'] = 100
        self.testStimulus['max'] = 15000
        self.testStimulus['default'] = 1000
        self.testStimulus['parameterSearchPrecision'] = 1000
        self.testStimulus['parameterList'] = np.arange(
            self.testStimulus['parameterSearchPrecision'], self.testStimulus['max'],
            self.testStimulus['parameterSearchPrecision'])
        setattr(self.stimulus,
                self.testStimulus['parameter'], self.testStimulus['default'])

        self.plotControl['title'] = 'Hearing Threshold Vs Frequency'
        self.plotControl['xmin'] = self.testStimulus['min']
        self.plotControl['xmax'] = self.testStimulus['max']
        self.plotControl['ymin'] = self.userStimulus['min']
        self.plotControl['ymax'] = self.userStimulus['max']
        self.plotControl['xlabel'] = 'Frequency'
        self.plotControl['xunits'] = 'Hz'
        self.plotControl['ylabel'] = 'Volume'
        self.plotControl['yunits'] = 'dB'

        self.testResults['independent'] = []
        self.testResults['dependent'] = []

    def _configureToneMatchTest(self):

        self.testInformation['instructions'] = \
            '<ol>' \
            '<li>Start the test by pressing the <b>Start Test</b> button. You should hear different tones in the left and right ears.</li><br>' \
            '<li>Use the slider to adjust the tone in the right ear until it matches the tone in the left ear, then press the <b>Update Plot</b> button.</li><br>' \
            '<li>Repeat step 2 to capture additional data points.</li><br>' \
            '<li>Press the <b>Stop Test</b> button when you are finished.</li>' \
            '</ol>'

        self.userStimulus['parameter'] = 'f_R'
        self.userStimulus['min'] = 100
        self.userStimulus['max'] = 15000
        self.userStimulus['default'] = 100
        self.userStimulus['precision'] = 1
        self.userStimulus['pagePrecision'] = 10
        self.userStimulus['label'] = 'Frequency'
        setattr(self.stimulus,
                self.userStimulus['parameter'], self.userStimulus['default'])

        self.testStimulus['parameter'] = 'f_L'
        self.testStimulus['min'] = 100
        self.testStimulus['max'] = 15000
        self.testStimulus['default'] = 1000
        self.testStimulus['parameterSearchPrecision'] = 1000
        self.testStimulus['parameterList'] = np.arange(
            self.testStimulus['parameterSearchPrecision'], self.testStimulus['max'],
            self.testStimulus['parameterSearchPrecision'])
        setattr(self.stimulus,
                self.testStimulus['parameter'], self.testStimulus['default'])

        self.plotControl['title'] = 'Tone Match Error Vs Frequency'
        self.plotControl['xmin'] = self.testStimulus['min']
        self.plotControl['xmax'] = self.testStimulus['max']
        self.plotControl['ymin'] = 0
        self.plotControl['ymax'] = 5
        self.plotControl['xlabel'] = 'Frequency'
        self.plotControl['xunits'] = 'Hz'
        self.plotControl['ylabel'] = 'Error'
        self.plotControl['yunits'] = 'octaves'

        self.testResults['independent'] = []
        self.testResults['dependent'] = []

    def _configureOctaveMatchTest(self):

        self.testInformation['instructions'] = \
            '<ol>' \
            '<li>Start the test by pressing the <b>Start Test</b> button. You should hear different tones in the left and right ears.</li><br>' \
            '<li>Use the slider to adjust the tone in the right ear until it is an octave above the tone in the left ear, then press the <b>Update Plot</b> button.</li><br>' \
            '<li>Repeat step 2 to capture additional data points.</li><br>' \
            '<li>Press the <b>Stop Test</b> button when you are finished.</li>' \
            '</ol>'

        self.userStimulus['parameter'] = 'f_R'
        self.userStimulus['min'] = 100
        self.userStimulus['max'] = 15000
        self.userStimulus['default'] = 100
        self.userStimulus['precision'] = 1
        self.userStimulus['pagePrecision'] = 10
        self.userStimulus['label'] = 'Frequency'
        setattr(self.stimulus,
                self.userStimulus['parameter'], self.userStimulus['default'])

        self.testStimulus['parameter'] = 'f_L'
        self.testStimulus['min'] = 100
        self.testStimulus['max'] = 7500
        self.testStimulus['default'] = 1000
        self.testStimulus['parameterSearchPrecision'] = 1000
        self.testStimulus['parameterList'] = np.arange(
            self.testStimulus['parameterSearchPrecision'], self.testStimulus['max'],
            self.testStimulus['parameterSearchPrecision'])
        setattr(self.stimulus,
                self.testStimulus['parameter'], self.testStimulus['default'])

        self.plotControl['title'] = 'Octave Match Error Vs Frequency'
        self.plotControl['xmin'] = self.testStimulus['min']
        self.plotControl['xmax'] = self.testStimulus['max']
        self.plotControl['ymin'] = 0
        self.plotControl['ymax'] = 5
        self.plotControl['xlabel'] = 'Frequency'
        self.plotControl['xunits'] = 'Hz'
        self.plotControl['ylabel'] = 'Error'
        self.plotControl['yunits'] = 'octaves'

        self.testResults['independent'] = []
        self.testResults['dependent'] = []

    def updateHearingThresholdTestData(self):
        # Save the test frequency
        self.testResults['independent'] = self._getLoggedStimulusData(
            self.testStimulus['parameter'])
        # Save the volume that the user selected
        self.testResults['dependent'] = self._getLoggedStimulusData(
            self.userStimulus['parameter'])

        self._updateTestStimulus()

    def updateToneMatchTestData(self):
        # Calculate the users guessed frequency error in octaves
        actualFrequencies = np.array(
            self._getLoggedStimulusData(self.testStimulus['parameter']))
        guessedFrequencies = np.array(
            self._getLoggedStimulusData(self.userStimulus['parameter']))
        self.testResults['independent'] = actualFrequencies
        self.testResults['dependent'] = np.log2(
            guessedFrequencies/actualFrequencies)

        self._updateTestStimulus()

    def updateOctaveMatchTestData(self):
        # Calculate the users guessed frequency error in octaves
        actualFrequencies = np.array(
            self._getLoggedStimulusData(self.testStimulus['parameter']))
        guessedFrequencies = np.array(
            self._getLoggedStimulusData(self.userStimulus['parameter']))
        self.testResults['independent'] = actualFrequencies
        self.testResults['dependent'] = np.log2(
            guessedFrequencies/(2*actualFrequencies))

        self._updateTestStimulus()

    def _updateTestStimulus(self):
        """Generate a new test stimulus and reset the user controlled stimulus
        to the default value. 

        The new test stimulus is selected randomly from a prepopulated list of
        equally stimulus values. When there are no stimulus values left in the 
        list, a new list of stimulus values is generated, where all the new 
        values are equally spaced between the existing values.
        """
        usedTestStimuli = self._getLoggedStimulusData(
            self.testStimulus['parameter'])

        self.testStimulus['parameterList'] = list(
            set(self.testStimulus['parameterList']) - set(usedTestStimuli))
        if(len(self.testStimulus['parameterList']) == 0):
            self.testStimulus['parameterSearchPrecision'] /= 2
            self.testStimulus['parameterList'] = np.arange(
                self.testStimulus['parameterSearchPrecision'], self.testStimulus['max'],
                self.testStimulus['parameterSearchPrecision'])
            self.testStimulus['parameterList'] = list(
                set(self.testStimulus['parameterList']) - set(usedTestStimuli))

        nextTestStimuli = random.choice(self.testStimulus['parameterList'])

        # Set the test stimulus to the new stimulus value
        setattr(self.stimulus, self.testStimulus['parameter'], nextTestStimuli)

        # Reset the user stimulus to the default value
        setattr(self.stimulus,
                self.userStimulus['parameter'], self.userStimulus['default'])

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
