from PyQt5 import QtCore
from PyQt5.QtWidgets import QSlider
from PyQt5.QtCore import pyqtSlot, pyqtSignal


class FloatSlider(QSlider):

    valueChanged = pyqtSignal(float)

    def __init__(self, parent, minimum=0, maximum=1.0, precision=0.1, page_precision=1):
        """Floating point slider

        FloatSlider is a floating point implementation of the QSlider widget.
        The 'precision' value sets the step size of the slider and the 
        'page_precision' value sets the page step size. The range of the 
        slider, (maximum - minimum), must be divisible by both the 'precision'
        and the 'page_precision'. Also, 'page_precision' must be a multiple of
        'precision'.
        """

        super(FloatSlider, self).__init__(parent)
        super().valueChanged.connect(self._valueChanged)

        # Load variables that are returned by the propery getters
        self._minimum = minimum
        self._maximum = maximum
        self._precision = precision
        self._page_precision = page_precision
        self._value = minimum

        # Call the property setters to propagate the updated values to the parent widget
        self.minimum = minimum
        self.maximum = maximum
        self.precision = precision
        self.page_precision = page_precision

    def _valueChanged(self, value: int) -> None:
        self.valueChanged.emit(float(value * self.precision))

    @property
    def minimum(self):
        return self._minimum

    @minimum.setter
    def minimum(self, value):

        slider_range = self.maximum - value

        if slider_range / self._precision != int(slider_range / self._precision):
            raise ValueError(
                'Slider range must be an integer multiple of precision')

        self._minimum = value
        self._minimum_int = int(value / self._precision)

        super(FloatSlider, self).setMinimum(self._minimum_int)

    @property
    def maximum(self):
        return self._maximum

    @maximum.setter
    def maximum(self, value):

        slider_range = value - self.minimum

        if slider_range / self._precision != int(slider_range / self._precision):
            raise ValueError(
                'Slider range must be an integer multiple of precision')

        self._maximum = value
        self._maximum_int = int(value / self._precision)

        super(FloatSlider, self).setMaximum(self._maximum_int)

    @property
    def precision(self):
        return self._precision

    @precision.setter
    def precision(self, value):
        slider_range = self.maximum - self.minimum

        if slider_range / value != int(slider_range / value):
            raise ValueError(
                'Slider range must be an integer multiple of precision')

        if self._page_precision / value != int(self._page_precision / value):
            raise ValueError(
                'Page precision must be an integer multiple of precision')

        # precision_change_scale_factor = self._precision / value
        self._precision = value
        self.minimum = self.minimum
        self.maximum = self.maximum
        self.page_precision = self.page_precision

    @property
    def page_precision(self):
        return self._page_precision

    @page_precision.setter
    def page_precision(self, value):

        if value / self.precision != int(value / self.precision):
            raise ValueError(
                'Page precision must be an integer multiple of precision')

        self._page_precision = value
        self._page_precision_int = int(value / self.precision)

        super(FloatSlider, self).setPageStep(self._page_precision_int)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):

        if value / self._precision != int(value / self._precision):
            raise ValueError(
                'Value must be an integer multiple of precision')

        self._value = value
        self._value_int = int(value / self._precision)

        super(FloatSlider, self).setValue(self._value_int)
        super(FloatSlider, self).setSliderPosition(self._value_int)

    @property
    def range(self):
        return self.minimum, self.maximum

    def set_range(self, minimum, maximum):
        """Set the minimum and maximum values"""
        self.maximum = maximum
        self.minimum = minimum
