
import pyaudio
import time
import struct
import math

def test_device(index):
    p = pyaudio.PyAudio()
    try:
        info = p.get_device_info_by_index(index)
        name = info.get('name')
        max_channels = int(info.get('maxInputChannels'))
        default_rate = int(info.get('defaultSampleRate'))
        print(f"\n--- Testing Device {index}: {name} ---")
        print(f"Max Channels: {max_channels}, Default Rate: {default_rate}")

        if max_channels == 0:
            print("Skipping: Output only device.")
            return

        # Configurations to try
        configs = [
            (16000, 1), # Target
            (default_rate, 1),
            (default_rate, max_channels),
            (44100, 1),
            (48000, 1)
        ]
        
        success = False
        for rate, channels in configs:
            if channels > max_channels: continue
            
            print(f"Attempting: Rate={rate}, Channels={channels}...", end="", flush=True)
            try:
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=rate,
                    input=True,
                    input_device_index=index,
                    frames_per_buffer=1024
                )
                
                # Try reading
                data = stream.read(1024, exception_on_overflow=False)
                
                # Check levels
                # Convert first few bytes to samples
                count = len(data) // 2
                format_str = "<" + "h" * count
                samples = struct.unpack(format_str, data)
                peak = max(abs(s) for s in samples)
                avg = sum(abs(s) for s in samples) / count
                
                print(f" ✅ Success! Peak Level: {peak}/32768, Avg: {avg:.2f}")
                stream.stop_stream()
                stream.close()
                success = True
                
                # If this is our target config (16k/1ch) and it works, we are good.
                if rate == 16000 and channels == 1:
                    print(">>> TARGET CONFIG (16kHz, Mono) WORKS <<<")
                
            except Exception as e:
                print(f" ❌ Failed: {e}")
        
    except Exception as e:
        print(f"Error querying device {index}: {e}")
    finally:
        p.terminate()

# Test the microphone we selected
test_device(3)
