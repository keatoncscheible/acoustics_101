from abc import ABC, abstractmethod
import pyaudio
import numpy as np
from enum import Enum


class Stimulus(ABC):

    def __init__(self, frames_per_buffer=1024):
        """Stimuli Abstract Base Class

        The concrete class must define the following properties:
            Fs              - Sample rate in Hz
            duration        - Stimuli playback duration in seconds
            num_channels    - Number of PyAudio playback channels

        The concrete class must define the following methods:
            callback        - PyAudio stream non-blocking callback function

        The concrete class must call super().__init__() at the end of its own
        __init__ function
        """
        # Sample rate in Hz
        @property
        def Fs(self):
            ...

        # Stimuli playback duration in seconds
        @property
        def duration(self):
            ...

        # Number of PyAudio playback channels
        @property
        def num_channels(self):
            ...

        # Get a list of all the controllable stimulus parameters
        self.parameters = list(
            set(dir(self)) - set(dir(self.__class__.__bases__[0])))
        self.parameters = [
            parameter for parameter in self.parameters if parameter[0] != '_']
        self.parameters.remove('Fs')
        self.parameters.remove('num_channels')

        # Ensure a valid sample rate was provided
        supported_sample_rates = [44100, 48000]
        if self.Fs not in supported_sample_rates:
            raise ValueError(
                'Sample rate of {0} Hz is not supported. Supported sample rates are {1}'.format(
                    self.Fs, supported_sample_rates))

        # Sample period
        self.Ts = 1/self.Fs

        # Create PyAudio object and open stream
        self._pa_obj = pyaudio.PyAudio()
        self._stream = self._pa_obj.open(format=pyaudio.paFloat32,
                                         channels=self.num_channels,
                                         rate=int(self.Fs),
                                         output=True,
                                         start=False,
                                         stream_callback=self.callback,
                                         frames_per_buffer=frames_per_buffer)

    @abstractmethod
    def callback(self, in_data, frame_count, time_info, status):
        """PyAudio stream non-blocking callback function

        This callback is called when PyAudio is ready for new output data.
        This abstract method updates the timing parameters and sets the 
        paComplete flag when all the data has been output. The concrete method
        must first call this abstract method with super().callback(...) to 
        update the timing parameters. The concrete method can then use 
        self.time when generating a time varying stimulus. The concrete method
        must return the following tuple, (data, self.pa_flag), where data
        is the time varying stimulus. The pa_flag is handled by the Stimuli
        class, so there is no need to modify it in the child class.
        """
        self.time = np.arange(self._frame, self._frame + frame_count) * self.Ts
        self._frame += frame_count
        if self.time[0] > self.duration:
            self.pa_flag = pyaudio.paComplete

    def play(self):
        """Play the stimulus

        The stimulus will be played until either the configured duration is
        reached or until stop() is called. is_playing() can be used to check 
        if the stimulus is actively producing audio.
        """
        # no need to do anything if we are already playing
        if self._stream.is_active():
            return

        # stream must be stopped before it can be started
        if not self._stream.is_stopped():
            self._stream.stop_stream()

        # start the stream
        self._frame = 0
        self.pa_flag = pyaudio.paContinue
        self._stream.start_stream()

    def is_playing(self):
        """Check if the stimulus is playing"""
        return self._stream.is_active()

    def stop(self):
        """Stop playing the stimulus"""
        self._stream.stop_stream()

    def is_stopped(self):
        """Check if the stimulus is stopped"""
        return self._stream.is_stopped()

    def done(self):
        """Stop and close the stream and shutdown PyAudio"""
        # stop and close the stream
        self._stream.stop_stream()
        self._stream.close()

        # close PyAudio
        self._pa_obj.terminate()


class VolumeMode(Enum):
    LINEAR = 1
    DB = 2


class PureToneMono(Stimulus):
    """Pure Sine Wave (Mono)"""

    def __init__(self, Fs=48e3, A=-60, f=1e3, volume_mode=VolumeMode.DB, duration=np.inf):

        if volume_mode not in [VolumeMode.LINEAR, VolumeMode.DB]:
            raise ValueError(
                'volume_mode must either be VolumeMode.LINEAR or VolumeMode.DB')

        if A > 1 and volume_mode == VolumeMode.LINEAR:
            raise ValueError(
                'Maximum allowable ampliutde is 1 when volume_mode is VolumeMode.LINEAR')

        if A > 0 and volume_mode == VolumeMode.DB:
            raise ValueError(
                'Maximum allowable ampliutde is 0 when volume_mode is VolumeMode.DB')

        self.num_channels = 1
        self.Fs = Fs
        self._Ts = 1/Fs
        self._A = EnvelopeGenerator(setpoint=A, rate=200, Fs=Fs)
        self._f = EnvelopeGenerator(setpoint=f, rate=Fs/2, Fs=Fs)
        self._theta = 0
        self.volume_mode = volume_mode
        self.duration = duration
        super().__init__()
        # Remove parameters that should not be controlled
        self.parameters.remove('volume_mode')

    def callback(self, in_data, frame_count, time_info, status):
        super().callback(in_data, frame_count, time_info, status)
        f_arr = self.f.next(frame_count)
        A_arr = self.A.next(frame_count)
        theta_accum = np.cumsum((2 * np.pi * f_arr) * self._Ts) + self._theta
        self._theta = theta_accum[-1] % (2 * np.pi)
        if self.volume_mode == VolumeMode.LINEAR:
            data = A_arr * np.sin(theta_accum)
        else:  # self.volume_mode == VolumeMode.DB
            data = np.power(10, (A_arr / 20)) * np.sin(theta_accum)

        return (data, self.pa_flag)

    @property
    def f(self):
        return self._f

    @ f.setter
    def f(self, value):
        self._f.setpoint = value

    @property
    def A(self):
        return self._A

    @ A.setter
    def A(self, value):
        self._A.setpoint = value


class PureToneStereo(Stimulus):
    """Pure Sine Wave (Stereo)"""

    def __init__(self, Fs=48e3, A_L=-60, f_L=1e3, A_R=-60, f_R=1e3,
                 volume_mode=VolumeMode.DB, duration=np.inf):

        if volume_mode not in [VolumeMode.LINEAR, VolumeMode.DB]:
            raise ValueError(
                'volume_mode must either be VolumeMode.LINEAR or VolumeMode.DB')

        if (A_L > 1 or A_R > 1) and volume_mode == VolumeMode.LINEAR:
            raise ValueError(
                'Maximum allowable ampliutde is 1 when volume_mode is VolumeMode.LINEAR')

        if (A_L > 0 or A_R > 0) and volume_mode == VolumeMode.DB:
            raise ValueError(
                'Maximum allowable ampliutde is 0 when volume_mode is VolumeMode.DB')

        self.num_channels = 2
        self.Fs = Fs
        self._Ts = 1/Fs
        self._A_L = EnvelopeGenerator(setpoint=A_L, rate=200, Fs=Fs)
        self._f_L = EnvelopeGenerator(setpoint=f_L, rate=Fs/2, Fs=Fs)
        self._A_R = EnvelopeGenerator(setpoint=A_R, rate=200, Fs=Fs)
        self._f_R = EnvelopeGenerator(setpoint=f_R, rate=Fs/2, Fs=Fs)
        self._theta_L = 0
        self._theta_R = 0
        self.volume_mode = volume_mode
        self.duration = duration
        super().__init__()

    def callback(self, in_data, frame_count, time_info, status):
        super().callback(in_data, frame_count, time_info, status)
        f_arr = self.f.next(frame_count)
        A_arr = self.A.next(frame_count)
        theta_accum = np.cumsum((2 * np.pi * f_arr) * self._Ts) + self._theta
        self._theta = theta_accum[-1] % (2 * np.pi)
        if self.volume_mode == VolumeMode.LINEAR:
            data = A_arr * np.sin(theta_accum)
        else:  # self.volume_mode == VolumeMode.DB
            data = np.power(10, (A_arr / 20)) * np.sin(theta_accum)

        return (data, self.pa_flag)

    def callback(self, in_data, frame_count, time_info, status):
        super().callback(in_data, frame_count, time_info, status)
        f_L_arr = self.f_L.next(frame_count)
        A_L_arr = self.A_L.next(frame_count)
        f_R_arr = self.f_R.next(frame_count)
        A_R_arr = self.A_R.next(frame_count)
        theta_accum_L = np.cumsum(
            (2 * np.pi * f_L_arr) * self._Ts) + self._theta_L
        self._theta_L = theta_accum_L[-1] % (2 * np.pi)
        theta_accum_R = np.cumsum(
            (2 * np.pi * f_R_arr) * self._Ts) + self._theta_R
        self._theta_R = theta_accum_R[-1] % (2 * np.pi)
        data = np.empty(2*frame_count, dtype=np.float32)
        if self.volume_mode == VolumeMode.LINEAR:
            data[0::2] = A_L_arr * np.sin(theta_accum_L)
            data[1::2] = A_R_arr * np.sin(theta_accum_R)
        else:  # self.volume_mode == VolumeMode.DB
            data[0::2] = np.power(10, (A_L_arr / 20)) * np.sin(theta_accum_L)
            data[1::2] = np.power(10, (A_R_arr / 20)) * np.sin(theta_accum_R)

        return (data, self.pa_flag)

    @property
    def f_L(self):
        return self._f_L

    @ f_L.setter
    def f_L(self, value):
        self._f_L.setpoint = value

    @property
    def A_L(self):
        return self._A_L

    @ A_L.setter
    def A_L(self, value):
        self._A_L.setpoint = value

    @property
    def f_R(self):
        return self._f_R

    @ f_R.setter
    def f_R(self, value):
        self._f_R.setpoint = value

    @property
    def A_R(self):
        return self._A_R

    @ A_R.setter
    def A_R(self, value):
        self._A_R.setpoint = value


class EnvelopeGenerator:
    def __init__(self, setpoint=0, rate=1, Fs=48000):
        """Envelope Generator

        The envelope generator creates an array of values that approach a 
        setpoint at a constant rate. Once the setpoint is reached, the
        generator returns an array of the specified size, where all values are
        at the setpoint. The arrays that are returned are of type np.float32.

        Attributes:
            setpoint: 
                The setpoint is the value that the generated output will 
                approach until it is reached. Once the setpoint is reached, 
                the generator will return the setpoint.
            rate: 
                Rate at which the setpoint will be approached. The units of 
                rate are 'setpoint units' per second.
            Fs: Sample rate in Hz

        Methods:
            set(value):
                Interface to set the setpoint

        Typical usage example:

            env = EnvelopeGenerator()  
            env.setpoint = 1 
            env.rate = 10   
            arr = env.next(10)
            # Do something with arr...
            arr = env.next(10)
            .
            .
            .

        """
        self._setpoint = setpoint
        self._current = setpoint
        self._rate = rate
        self._inv_rate = 1/rate
        self._Fs = Fs
        self._Ts = 1/Fs
        self._steady_state = True

    @property
    def setpoint(self):
        return self._setpoint

    @setpoint.setter
    def setpoint(self, value):
        self._setpoint = value
        self._steady_state = False

    def set(self, setpoint):
        self.setpoint = setpoint

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, value):
        self._rate = value
        self._inv_rate = 1/value

    def __iter__(self):
        return self

    def __next__(self, n=1):
        return self.next(n)

    def next(self, n=1):

        # Steady state output
        if self._steady_state:
            return np.full(n, self._setpoint, dtype=np.float32)

        # Changing output
        change_until_steady_state = self._setpoint - self._current
        change_direction = np.sign(change_until_steady_state)
        current_change = change_direction * self._rate * n * self._Ts
        if np.abs(change_until_steady_state) > np.abs(current_change):
            envelope = np.linspace(
                self._current, self._current + current_change, n, dtype=np.float32)
            self._current += current_change
            return envelope

        # Transitioning to steady state
        samples_until_steady_state = int(
            np.abs(change_until_steady_state) * self._inv_rate * self._Fs)
        assert samples_until_steady_state < n, \
            "Samples until steady state calculation error. Something went wrong."
        remaining_transition_section = np.linspace(
            self._current, self._current + change_until_steady_state, samples_until_steady_state, dtype=np.float32)
        steady_state_section = np.full(
            n - samples_until_steady_state, self._setpoint, dtype=np.float32)
        self._steady_state = True
        self._current = self._setpoint
        return np.concatenate((remaining_transition_section, steady_state_section), axis=0)
