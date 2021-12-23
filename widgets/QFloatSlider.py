from PyQt5.QtWidgets import QSlider
from PyQt5.QtCore import pyqtSignal


class QFloatSlider(QSlider):

    valueChanged = pyqtSignal(float)

    def __init__(self, parent, minimum=0, maximum=1.0, precision=0.1, pagePrecision=1):
        """Floating point slider

        FloatSlider is a floating point implementation of the QSlider widget.
        The 'precision' value sets the step size of the slider and the 
        'pagePrecision' value sets the page step size. The range of the 
        slider, (maximum - minimum), must be divisible by both the 'precision'
        and the 'pagePrecision'. Also, 'pagePrecision' must be a multiple of
        'precision'.
        """

        super(QFloatSlider, self).__init__(parent)
        super().valueChanged.connect(self._valueChanged)

        # Load variables that are returned by the propery getters
        self._minimum = minimum
        self._maximum = maximum
        self._precision = precision
        self._pagePrecision = pagePrecision
        self._value = minimum

        # Call the property setters to propagate the updated values to the parent widget
        self.minimum = minimum
        self.maximum = maximum
        self.precision = precision
        self.pagePrecision = pagePrecision

    def _valueChanged(self, value: int) -> None:
        self.valueChanged.emit(float(value * self.precision))

    @property
    def minimum(self):
        return self._minimum

    @minimum.setter
    def minimum(self, value):

        sliderRange = self.maximum - value

        if sliderRange / self._precision != int(sliderRange / self._precision):
            raise ValueError(
                'Slider range must be an integer multiple of precision')

        self._minimum = value
        self._minimumInt = int(value / self._precision)

        super(QFloatSlider, self).setMinimum(self._minimumInt)

    @property
    def maximum(self):
        return self._maximum

    @maximum.setter
    def maximum(self, value):

        sliderRange = value - self.minimum

        if sliderRange / self._precision != int(sliderRange / self._precision):
            raise ValueError(
                'Slider range must be an integer multiple of precision')

        self._maximum = value
        self._maximumInt = int(value / self._precision)

        super(QFloatSlider, self).setMaximum(self._maximumInt)

    @property
    def precision(self):
        return self._precision

    @precision.setter
    def precision(self, value):
        sliderRange = self.maximum - self.minimum

        if sliderRange / value != int(sliderRange / value):
            raise ValueError(
                'Slider range must be an integer multiple of precision')

        if self._pagePrecision / value != int(self._pagePrecision / value):
            raise ValueError(
                'Page precision must be an integer multiple of precision')

        self._precision = value
        self.minimum = self.minimum
        self.maximum = self.maximum
        self.pagePrecision = self.pagePrecision

    @property
    def pagePrecision(self):
        return self._pagePrecision

    @pagePrecision.setter
    def pagePrecision(self, value):

        if value / self.precision != int(value / self.precision):
            raise ValueError(
                'Page precision must be an integer multiple of precision')

        self._pagePrecision = value
        self._pagePrecisionInt = int(value / self.precision)

        super(QFloatSlider, self).setPageStep(self._pagePrecisionInt)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):

        if value / self._precision != int(value / self._precision):
            raise ValueError(
                'Value must be an integer multiple of precision')

        self._value = value
        self._valueInt = int(value / self._precision)

        super(QFloatSlider, self).setValue(self._valueInt)
        super(QFloatSlider, self).setSliderPosition(self._valueInt)

    @property
    def range(self):
        return self.minimum, self.maximum

    def setRange(self, minimum, maximum):
        """Set the minimum and maximum values"""
        self.maximum = maximum
        self.minimum = minimum
