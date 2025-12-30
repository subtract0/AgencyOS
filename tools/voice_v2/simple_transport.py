
import pyaudio
import threading
import logging
from pipecat.transports.base_input import BaseInputTransport
from pipecat.transports.base_output import BaseOutputTransport
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.frames.frames import InputAudioRawFrame, OutputAudioRawFrame, StartFrame
import asyncio

class SimpleInputTransport(BaseInputTransport):
    def __init__(self, params: TransportParams, input_device_index: int):
        super().__init__(params)
        self._input_device_index = input_device_index
        self._p = pyaudio.PyAudio()
        self._stream = None
        self._running = False
        self._thread = None
        self._loop = None
        # Fix: Ensure attribute exists
        self._audio_in_queue = None

    async def start(self, frame: StartFrame):
        await super().start(frame)
        
        # Defensive: Ensure queue exists even if BaseInputTransport failed
        if not self._audio_in_queue:
            logging.warning("SimpleInputTransport: _audio_in_queue missing after super().start(), creating manually.")
            self._audio_in_queue = asyncio.Queue()
            # Must also start the consumer task
            if not getattr(self, '_audio_task', None):
                 logging.warning("SimpleInputTransport: _audio_task missing, starting handler.")
                 self._audio_task = self.create_task(self._audio_task_handler())
            
        self._loop = asyncio.get_running_loop()
        self._running = True
        
        # Start capture thread
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logging.info(f"SimpleInputTransport: Started access to device {self._input_device_index}")

    def _capture_loop(self):
        try:
            self._stream = self._p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=self._input_device_index,
                frames_per_buffer=1024 # 64ms chunks
            )
            
            logging.info("SimpleInputTransport: Stream opened. Reading...")
            
            while self._running:
                try:
                    data = self._stream.read(1024, exception_on_overflow=False)
                    if not data: continue
                    
                    # Push frame to async loop
                    frame = InputAudioRawFrame(
                        audio=data,
                        sample_rate=16000,
                        num_channels=1
                    )
                    
                    if self._audio_in_queue:
                        self._loop.call_soon_threadsafe(self._audio_in_queue.put_nowait, frame)
                    else:
                        logging.warning("SimpleInputTransport: No audio queue available!")
                    
                except Exception as e:
                    logging.error(f"SimpleInputTransport Read Error: {e}")
                    break
        except Exception as e:
             logging.error(f"SimpleInputTransport Open Error: {e}")
        finally:
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()

    async def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self._p.terminate()

class SimpleTransport(BaseTransport):
    def __init__(self, input_device_index: int = 3):
        super().__init__()
        self._params = TransportParams(audio_in_sample_rate=16000, audio_out_sample_rate=16000)
        self._input = SimpleInputTransport(self._params, input_device_index)
        # Use default LocalAudioOutputTransport for output since that likely works, 
        # or we can just leave it as is if we only changed input. 
        # Actually simplest is to just mix-and-match.
        # But for 'BaseTransport' interface, we need .input() and .output()
        
        from pipecat.transports.local.audio import LocalAudioOutputTransport, LocalAudioTransportParams
        # We'll use the standard output transport
        op = LocalAudioTransportParams(audio_out_sample_rate=16000)
        self._output = LocalAudioOutputTransport(pyaudio.PyAudio(), op) 

    def input(self):
        return self._input

    def output(self):
        return self._output
