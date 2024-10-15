import pyaudio
import os
import wave
import librosa
import numpy as np
from sys import byteorder
from array import array
from struct import pack
from .train import train_model
THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 16000
SILENCE = 30

def is_silent(snd_data):
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    MAXIMUM = 16384
    times = float(MAXIMUM) / max(abs(i) for i in snd_data)
    r = array('h')
    for i in snd_data:
        r.append(int(i * times))
    return r

def trim(snd_data):
    def _trim(snd_data):
        snd_started = False
        r = array('h')
        for i in snd_data:
            if not snd_started and abs(i) > THRESHOLD:
                snd_started = True
                r.append(i)
            elif snd_started:
                r.append(i)
        return r

    snd_data = _trim(snd_data)
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data

def add_silence(snd_data, seconds):
    r = array('h', [0 for _ in range(int(seconds * RATE))])
    r.extend(snd_data)
    r.extend([0 for _ in range(int(seconds * RATE))])
    return r

def record():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
                    input=True, output=True,
                    frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False
    r = array('h')

    while 1:
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

        if snd_started and num_silent > SILENCE:
            break

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r

def record_to_file(path):
    sample_width, data = record()
    data = pack('<' + ('h' * len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

def extract_feature(file_name, **kwargs):
    X, sample_rate = librosa.core.load(file_name)
    stft = np.abs(librosa.stft(X))
    result = np.array([])

    if kwargs.get("mfcc"):
        mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=40).T, axis=0)
        result = np.hstack((result, mfccs))
    
    if kwargs.get("chroma"):
        chroma = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T, axis=0)
        result = np.hstack((result, chroma))
    
    if kwargs.get("mel"):
        mel = np.mean(librosa.feature.melspectrogram(y=X, sr=sample_rate).T, axis=0)
        result = np.hstack((result, mel))
    
    if kwargs.get("contrast"):
        contrast = np.mean(librosa.feature.spectral_contrast(S=stft, sr=sample_rate).T, axis=0)
        result = np.hstack((result, contrast))
    
    if kwargs.get("tonnetz"):
        tonnetz = np.mean(librosa.feature.tonnetz(y=librosa.effects.harmonic(X), sr=sample_rate).T, axis=0)
        result = np.hstack((result, tonnetz))

    return result

def predict_gender(audio_file_path):
    #sample_width, _ = record()
    #record_to_file(audio_file_path)
    
    features = extract_feature(audio_file_path, mel=True).reshape(1, -1)
    
    # Load the model and weights
    from .utils import create_model
    model = create_model()
    model.load_weights("gender/results/model.h5")
    
    male_prob = model.predict(features)[0][0]
    female_prob = 1 - male_prob
    gender = "male" if male_prob > female_prob else "female"
    
    return gender

if __name__ == "__main__":

    audio_file = "/Users/shreerammeka/Desktop/titan-v5/gender/test-samples/17-363-0002.wav"
    #train_model()
    print(audio_file)
    if not audio_file or not os.path.isfile(audio_file):
        print("Please provide a valid audio file.")
    else:
        result = predict_gender(audio_file)
        print(result)