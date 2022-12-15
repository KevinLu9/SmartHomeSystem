#!/dev/python

import subprocess
import sys
import pkg_resources
import time
import pyaudio
import threading
import queue
import json
import cv2
from vosk import Model, KaldiRecognizer

def install_packages():
    required = {"pyaudio", "vosk", "transformers", "torch"}
    # Get installed packages from pkg_resources
    installed = {pkg.key for pkg in pkg_resources.working_set}
    missing = required - installed
    # Install missing packages
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])


class MicrophoneAudio():
    def __init__(self, deviceindex):
        self.DEVICE_INDEX = deviceindex
        self.CHANNELS = 1
        self.FRAME_RATE = 16000
        self.RECORD_SECONDS = 2
        self.AUDIO_FORMAT = pyaudio.paInt16
        self.SAMPLE_SIZE = 2
        self.CHUNK = 1024
        self.frames = []
        self.recordings = queue.Queue()
        self.p = pyaudio.PyAudio()
        self.stream = p.open(format=self.AUDIO_FORMAT,
                                channels=self.CHANNELS,
                                rate=self.FRAME_RATE,
                                input=True,
                                input_device_index=self.DEVICE_INDEX,
                                frames_per_buffer=self.CHUNK)
        self.quit = False
        self.recThread = threading.Thread(target=self.record_microphone, args={}, name="RecordingThread").start()

        

    def record_microphone(self):
        while not self.quit:
            data = self.stream.read(self.CHUNK)
            self.frames.append(data)
            if len(self.frames) >= (self.FRAME_RATE * self.RECORD_SECONDS) / self.CHUNK:
                self.recordings.put(self.frames.copy())
                self.frames = []
        
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        print("MicrophoneAudio Was Successfully Terminated")


    # Must be called at end of program to allow for graceful termination
    def close(self):
        self.quit = True


    def __del__(self):
        self.close()
