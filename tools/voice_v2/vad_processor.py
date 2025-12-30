
import logging
from typing import Optional

from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    Frame,
    AudioRawFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    StartFrame
)
from pipecat.audio.vad.vad_analyzer import VADAnalyzer, VADState

class VADProcessor(FrameProcessor):
    def __init__(self, analyzer: VADAnalyzer, **kwargs):
        super().__init__(**kwargs)
        self._analyzer = analyzer
        self._last_state = VADState.QUIET

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame):
             if self._analyzer:
                 # Initialize analyzer with pipeline sample rate
                 rate = frame.audio_in_sample_rate
                 logging.info(f"VADProcessor: Initializing analyzer with sample rate {rate}")
                 self._analyzer.set_sample_rate(rate)
        
        if isinstance(frame, AudioRawFrame):
            if not self._analyzer:
                await self.push_frame(frame, direction)
                return # Pipecat usually passes audio through.
            # Pass through audio first? Or after VAD?
            # Pipecat usually passes audio through.
            await self.push_frame(frame, direction)
            
            # Analyze
            state = await self._analyzer.analyze_audio(frame.audio)


            if state != self._last_state:
                logging.info(f"VAD State Change: {self._last_state} -> {state}")
                if state == VADState.SPEAKING and self._last_state != VADState.SPEAKING:
                    logging.info("VAD: User Started Speaking")
                    await self.push_frame(UserStartedSpeakingFrame(), direction)
                elif state == VADState.QUIET and self._last_state != VADState.QUIET:
                     # Note: transitions go QUIET -> STARTING -> SPEAKING -> STOPPING -> QUIET
                     # Typically we care about SPEAKING entry and QUIET entry.
                    logging.info("VAD: User Stopped Speaking")
                    await self.push_frame(UserStoppedSpeakingFrame(), direction)
                    
            self._last_state = state
        else:
            await self.push_frame(frame, direction)
