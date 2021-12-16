import numpy as np
from stimuli import Stimuli
import time


class PureToneMono(Stimuli):
    """Pure Sine Wave (Mono)"""

    def __init__(self, Fs=48e3, A=1, f=1e3, theta=0, duration=1):
        self.num_channels = 1
        self.Fs = Fs
        self.A = A
        self.f = f
        self.theta = theta
        self.duration = duration
        super().__init__()

    def callback(self, in_data, frame_count, time_info, status):
        super().callback(in_data, frame_count, time_info, status)
        data = self.A * np.sin(2 * np.pi * self.f *
                               self.time + self.theta, dtype=np.float32)
        return (data, self.pa_flag)


class PureToneStereo(Stimuli):
    """Pure Sine Wave (Stereo)"""

    def __init__(self, Fs=48e3, A_L=1, f_L=1e3, theta_L=0, A_R=1, f_R=1e3,
                 theta_R=0, duration=1):
        self.num_channels = 2
        self.Fs = Fs
        self.A_L = A_L
        self.f_L = f_L
        self.theta_L = theta_L
        self.A_R = A_R
        self.f_R = f_R
        self.theta_R = theta_R
        self.duration = duration
        super().__init__()

    def callback(self, in_data, frame_count, time_info, status):
        super().callback(in_data, frame_count, time_info, status)
        data = np.empty(2*frame_count, dtype=np.float32)
        data[0::2] = self.A_L * \
            np.sin(2 * np.pi * self.f_L * self.time +
                   self.theta_L, dtype=np.float32)
        data[1::2] = self.A_R * \
            np.sin(2 * np.pi * self.f_R * self.time +
                   self.theta_R, dtype=np.float32)

        return (data, self.pa_flag)
