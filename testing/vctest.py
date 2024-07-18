import sounddevice as sd
import opuslib
import numpy as np

# Parameters
FRAME_SIZE = 960
SAMPLE_RATE = 48000
CHANNELS = 1

# Initialize Opus encoder and decoder
encoder = opuslib.Encoder(SAMPLE_RATE, CHANNELS, opuslib.APPLICATION_AUDIO)
decoder = opuslib.Decoder(SAMPLE_RATE, CHANNELS)


# Callback function for audio processing
def callback(indata, outdata, frames, time, status):
    if status:
        print(status)

    # Convert input data to the appropriate format
    pcm_data = np.frombuffer(indata, dtype=np.int16)
    encoded_data = encoder.encode(pcm_data.tobytes(), frames)
    decoded_data = decoder.decode(encoded_data, frames)

    # Convert decoded data back to numpy array and copy to outdata
    outdata[:] = np.frombuffer(decoded_data, dtype=np.int16).reshape(outdata.shape)


# Open the stream
try:
    with sd.Stream(samplerate=SAMPLE_RATE, blocksize=FRAME_SIZE, channels=CHANNELS, dtype='int16', callback=callback):
        print("Press Ctrl+C to stop.")
        sd.sleep(int(10 * 1e3))  # Run for 10 seconds
except Exception as e:
    print(f"An error occurred: {e}")
