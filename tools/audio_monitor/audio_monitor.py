##############################################################################
#
# Copyright (c) 2006-2011 Curictus AB.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##############################################################################

import Queue
import audioop
import math
import sys
import threading
import time
import wave

import pyaudio

###########################################################################
# Configuration.
###########################################################################

# Record using 16 bits per sample.
FORMAT = pyaudio.paInt16

# Don't bother with stereo, mono will do.
CHANNELS = 1

# Standard 44 KHz sammpling frequency.
RATE = 44100

# Buffer this many samples per frame.
FRAMES_PER_BUFFER = 1024

# Sample width in bytes.
SAMPLE_BYTE_SIZE = 2

# When recording is triggered we'll make sure that the max RMS from this many
# seconds of audio is below our threshold in order to to stop recording.
ANALYZE_SAMPLE_SECS = 5

# Keep this many last frames around when analyzing max RMS.
NUM_ANALYZE_FRAMES = ANALYZE_SAMPLE_SECS * (RATE / FRAMES_PER_BUFFER)

# Sample audio for this many seconds to calculate max enviroment RMS.
THRESHOLD_SAMPLE_SECS = 10

# Analyze this many frames to calculate environment max RMS.
NUM_THRESHOLD_FRAMES = THRESHOLD_SAMPLE_SECS * (RATE / FRAMES_PER_BUFFER)

###########################################################################
# Utilities.
###########################################################################

def stdev(seq):
    """
    Return sample population standard deviation for ``seq``.
    """
    n = len(seq)
    k = sum(seq) / n
    return math.sqrt(sum([(x - k)**2 for x in seq]) / n-1)


def getframerms(frame):
    """
    Return RMS (root-mean-square) power level for an audio ``frame``.
    """
    return audioop.rms(frame, SAMPLE_BYTE_SIZE)


def read_audio(stream, framequeue, stopevent):
    """
    Keep populating ``framequeue`` with audio frames (chunks) from a PyAudio
    ``stream`` until ``stopevent`` is signaled.
    """
    while not stopevent.isSet():
        framequeue.put(stream.read(FRAMES_PER_BUFFER))

        
###########################################################################
# Audio monitor entry-point.
###########################################################################

if __name__ == '__main__':
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=FRAMES_PER_BUFFER)

    stopevent = threading.Event()
    framequeue = Queue.Queue()
    
    # Launch worker thread which record and buffers audio to queue.
    thread = threading.Thread(target=read_audio,
                              args=(stream, framequeue, stopevent))
    thread.start()

    try:
        start = time.time()
        print "Measuring threshold (avoid noise %d sec)" % (THRESHOLD_SAMPLE_SECS)
        samples = []
        for n in range(NUM_THRESHOLD_FRAMES):
            samples.append(getframerms(framequeue.get()))

        threshold = max(samples)
        print "Threshold max(RMS): %.2f (avg: %.2f, stdev: %.2f)" % (
            threshold, sum(samples) / len(samples), stdev(samples))

        # We keep samples in a FIFO style queue so that we have a window N secs
        # of audio to calculate max RMS from. To start with a clean slate we'll
        # simply initialize the queue with N seconds of complete silence.
        samples = [0] * NUM_ANALYZE_FRAMES

        soundfile = None
        is_recording = False

        print "Begin monitoring (window size = %d secs)" % ANALYZE_SAMPLE_SECS
        while True:
            frame = framequeue.get()
            rms = getframerms(frame)
            samples.append(rms)
            samples = samples[1:] # Pop the oldest sample.

            if rms > threshold:
                if not is_recording:
                    is_recording = True
                    print "Starting to record audio!"
                    filename = "%s.wav" % time.strftime("%Y-%m-%d %H_%M_%S")
                    soundfile = wave.open(filename, 'wb')
                    soundfile.setnchannels(CHANNELS)
                    soundfile.setsampwidth(SAMPLE_BYTE_SIZE)
                    soundfile.setframerate(RATE)
                print "-> sample (rms: %.2f, time: %.2f)" % (rms, time.time() - start)

            if is_recording:
                if max(samples) < threshold:
                    is_recording = False
                    print "Stopped recording audio!"
                    soundfile.close()
                    soundfile = None
                else:
                    soundfile.writeframes(frame)
    finally:
        stopevent.set()
        thread.join()
        if soundfile:
            soundfile.close()
            
    stream.close()
    audio.terminate()
    
    
###########################################################################
# The End.
###########################################################################
