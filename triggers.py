#import pyaudio
#import wave

def trigger_playback():
    chunk = 1024
    wav = wave.open("/Users/bradcolquitt/projects/opencv/beep-01a.wav", "rb")
    p = pyaudio.PyAudio()
    #open stream
    stream = p.open(format = p.get_format_from_width(wav.getsampwidth()),
                channels = wav.getnchannels(),
                rate = wav.getframerate(),
                output = True)
    #read data
    data = wav.readframes(chunk)

    #paly stream
    while data != '':
        stream.write(data)
        data = wav.readframes(chunk)

    #stop stream
    stream.stop_stream()
    stream.close()

    #close PyAudio
    p.terminate()
