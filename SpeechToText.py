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
import numpy as np
import keyboard
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from itertools import count
from vosk import Model, KaldiRecognizer

def install_packages():
    required = {"pyaudio", "vosk", "transformers", "torch", "keyboard"}
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
        self.RECORD_SECONDS = 0.5
        self.AUDIO_FORMAT = pyaudio.paInt16
        self.SAMPLE_SIZE = 2
        self.CHUNK = 1024
        self.frames = []
        self.recordings = queue.Queue()
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.AUDIO_FORMAT,
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



class SpeechToText():
    def __init__(self, deviceindex, threshold=100):
        self.audio = MicrophoneAudio(deviceindex)
        self.model = Model(model_name="vosk-model-small-en-us-0.15")
        self.rec = KaldiRecognizer(self.model, self.audio.FRAME_RATE)
        self.rec.SetWords(True)
        self.quit = False
        self.SpeechToTextThread = threading.Thread(target=self.speech_recognition, args=(), name="SpeechToTextThread").start()
        self.audioInt = []
        self.THRESHOLD = threshold  # The audio magnitude threshold to continue to record/buffer without inputting to Vosk AI.
    
    def speech_recognition(self):
        while not self.quit:
            frames = self.audio.recordings.get()
            # convert frames to int so that we can plot them
            audioBit = b''.join(frames)

            # Buffer audio before inputting into VOSK AI to prevent cut offs
            latestAudioBit = audioBit
            audioMagnitude = self.THRESHOLD
            while audioMagnitude >= self.THRESHOLD:
                # If audio magnitude in the cycle exceeds a threshold, add more audio (another cycle) until silent
                self.audioInt = np.frombuffer(latestAudioBit, dtype='<i2').reshape(-1, self.audio.CHANNELS)
                audioMagnitude = np.average(np.abs(self.audioInt))
                if audioMagnitude > self.THRESHOLD:
                    print(f"BUFFERING AUDIO {audioMagnitude}")
                    time.sleep(self.audio.RECORD_SECONDS)  # Wait till next recording frames
                    # Get the frames and append them to the audio bits to input into the AI
                    frames = self.audio.recordings.get()
                    latestAudioBit = b''.join(frames)
                    audioBit += latestAudioBit

            # Pass audio into vosk AI
            self.rec.AcceptWaveform(audioBit)
            result = self.rec.Result()
            text = json.loads(result)["text"]
            if text != "":
                print(f"{text}", end=' ')
        # Terminate SpeechToText Thread
        self.audio.close()
        print("SpeechToText was Successfully Terminated!")


    def animate(self, i):
        """
        Plots the audio file to a live graph
        """
        y = self.audioInt[0:len(ai.audioInt):100]
        x = np.arange(0, len(y), dtype=int)
        plt.cla()
        plt.plot(x, y, label='Microphone Audio')
        plt.ylim((-1000, 1000))
        plt.tight_layout()
        if self.quit:
            plt.close()


    def close(self):
        self.quit = True
        

    def __del__(self):
        self.close()

def TerminateProgramThread(ai:SpeechToText):
    while True:
        if keyboard.is_pressed('q'):
            ai.close()
            print("\n User Pressed 'q', Terminating Program!")
            break

if __name__ == "__main__":
    #install_packages()

    p = pyaudio.PyAudio()
    deviceinfo = p.get_default_input_device_info()
    index = deviceinfo['index']
    print(f"Device with name \" {deviceinfo['name']} \" and index \"{index}\" was selected")
    p.terminate()
    
    ai = SpeechToText(index)

    # Start the terminate program thread to wait for 'q' to be pressed
    threading.Thread(target=TerminateProgramThread, args=(ai,)).start()

    # Plot live Audio
    ani = FuncAnimation(plt.gcf(), ai.animate, interval=100)
    plt.tight_layout()
    plt.show()

    #print("Converting Speech To Text!")
    #input("Enter any key to quit!\n")
    ai.close()
    cv2.destroyAllWindows()
