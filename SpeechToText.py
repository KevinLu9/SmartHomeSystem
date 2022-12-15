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
