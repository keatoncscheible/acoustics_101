from abc import ABC, abstractmethod
import random
import numpy as np
from stimulus import EnvelopeGenerator, Stimulus, PureToneMono, PureToneStereo


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

        self._activeTest = self.tests[0]

    @abstractmethod
    def startTest(self):
        """Start the psychoacoustic test"""
        ...

    @abstractmethod
    def stopTest(self):
        """Stop the psychoacoustic test"""
        ...

    @abstractmethod
    def updateData(self):
        """Update relevant data for the psychoacoustic test"""
        ...

    def selectTest(self, test):
        """Select a psychoacoustic test"""
        if test in self.tests:
            self._activeTest = test
        else:
            raise ValueError(
                '{} is not a valid test. Valid tests are {}'.format(test, self.tests))

    def adjustStimulus(self, **kwargs):
        """Adjust stimulus parameter"""
        for key, value in kwargs.items():
            assert key in self.stimulus.parameters, \
                '{} not in {} parameters. Available parameters are {}'.format(
                    key, self.stimulus.__class__(), self.stimulus.parameters)
            setattr(self.stimulus, key, value)

    def logStimulus(self):
        """Log stimulus parameters"""
        for parameter in self.stimulus.parameters:
            parameterAttr = getattr(self.stimulus, parameter)
            if isinstance(parameterAttr, EnvelopeGenerator):
                parameterData = parameterAttr.setpoint
            if isinstance(parameterAttr, int) or isinstance(parameterAttr, float):
                parameterData = parameterAttr
            getattr(self, '{}_log'.format(parameter)).append(parameterData)

    def printLoggedData(self):
        """Print logged data"""
        for parameter in self.stimulus.parameters:
            print('{}: {}'.format(parameter, getattr(
                self, '{}_log'.format(parameter))))

    def getLoggedData(self, parameter):
        return getattr(self, '{}_log'.format(parameter))


class MethodOfAdjustment(PaMethods):
    """Method of Adjustment"""

    def __init__(self):
        self.stimulus = PureToneMono()
        self.tests = ['Hearing Threshold', 'Tone Match', 'Octave Match']
        self.stimulusControl = {}
        self.testControl = {}
        self.testResults = {}
        self.plotControl = {}
        self.testInformation = {}
        super().__init__()

    def startTest(self):
        self.stimulus.play()

    def stopTest(self):
        self.stimulus.stop()

    def adjustStimulus(self, value):
        super().adjustStimulus(**{self.stimulusControl['parameter']: value})

    def updateData(self):
        self.logStimulus()

        if self._activeTest == 'Hearing Threshold':
            self.updateHearingThresholdTestData()
        elif self._activeTest == 'Tone Match':
            self.updateToneMatchTestData()
        elif self._activeTest == 'Octave Match':
            self.updateOctaveMatchTestData()

    def updateHearingThresholdTestData(self):
        testData = self.getLoggedData(self.testControl['parameter'])

        # Select a new test frequency
        # This algorithm randomly selects a new test frequency from the
        # parameter list. When there are no frequencies left in the parameter
        # list, a new list of frequencies is generated, where all the new
        # frequencies are equally spaced between the existing frequencies.
        self.testControl['parameterList'] = list(
            set(self.testControl['parameterList']) - set(testData))
        if(len(self.testControl['parameterList']) == 0):
            self.testControl['parameterSearchPrecision'] /= 2
            self.testControl['parameterList'] = np.arange(
                self.testControl['parameterSearchPrecision'], self.testControl['max'],
                self.testControl['parameterSearchPrecision'])
            self.testControl['parameterList'] = list(
                set(self.testControl['parameterList']) - set(testData))

        nextFrequency = random.choice(
            self.testControl['parameterList'])

        # Reset the volume to the default level
        self.stimulusControl['value'] = self.stimulusControl['default']
        # Adjust the frequency
        setattr(self.stimulus,
                self.testControl['parameter'], nextFrequency)
        # Reset the volume to the default value
        setattr(self.stimulus,
                self.stimulusControl['parameter'], self.stimulusControl['default'])

        # Save the independent and dependent test results
        self.testResults['independent'] = self.getLoggedData(
            self.testControl['parameter'])
        self.testResults['dependent'] = self.getLoggedData(
            self.stimulusControl['parameter'])

    def updateToneMatchTestData(self):
        pass

    def updateOctaveMatchTestData(self):
        pass

    def configureHearingThresholdTest(self):

        self.testInformation['instructions'] = \
            '<ol>' \
            '<li>Start the test by pressing the <b>Start Test</b> button. You should hear a tone.</li><br>' \
            '<li>Use the slider to adjust the volume until the tone is just barely peceivable, then press the <b>Update Plot</b> button.</li><br>' \
            '<li>Repeat step 2 to capture additional data points.</li><br>' \
            '<li>Press the <b>Stop Test</b> button when you are finished.</li>' \
            '</ol>'

        self.stimulusControl['parameter'] = 'A'
        self.stimulusControl['min'] = -100
        self.stimulusControl['max'] = -40
        self.stimulusControl['default'] = -50
        self.stimulusControl['precision'] = 0.1
        self.stimulusControl['pagePrecision'] = 1
        self.stimulusControl['label'] = 'Volume'
        self.stimulusControl['value'] = self.stimulusControl['default']
        setattr(self.stimulus,
                self.stimulusControl['parameter'], self.stimulusControl['default'])

        self.testControl['parameter'] = 'f'
        self.testControl['min'] = 100
        self.testControl['max'] = 15000
        self.testControl['default'] = 1000
        self.testControl['value'] = self.testControl['default']
        self.testControl['parameterSearchPrecision'] = 1000
        self.testControl['parameterList'] = np.arange(
            self.testControl['parameterSearchPrecision'], self.testControl['max'],
            self.testControl['parameterSearchPrecision'])
        setattr(self.stimulus,
                self.testControl['parameter'], self.testControl['default'])

        self.plotControl['title'] = 'Hearing Threshold Vs Frequency'
        self.plotControl['xmin'] = self.testControl['min']
        self.plotControl['xmax'] = self.testControl['max']
        self.plotControl['ymin'] = self.stimulusControl['min']
        self.plotControl['ymax'] = self.stimulusControl['max']
        self.plotControl['xlabel'] = 'Frequency'
        self.plotControl['xunits'] = 'Hz'
        self.plotControl['ylabel'] = 'Volume'
        self.plotControl['yunits'] = 'dB'

        self.testResults['independent'] = []
        self.testResults['dependent'] = []

    def configureToneMatchTest(self):
        pass

    def configureOctaveMatchTest(self):
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
