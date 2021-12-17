import pyaudio
import time
import numpy as np
from abc import ABC, abstractmethod


class Stimuli(ABC):

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

        # Ensure a valid sample rate was provided
        supported_sample_rates = [44100, 48000]
        assert self.Fs in supported_sample_rates,   \
            "Sample rate of {0} Hz is not supported. Supported sample rates are {1}".format(
                self.Fs, supported_sample_rates)

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
