
import inspect
try:
    from pipecat.services.deepgram import DeepgramSTTService
    print("DeepgramSTTService found.")
    print("MRO:", inspect.getmro(DeepgramSTTService))
except ImportError:
    print("Could not import DeepgramSTTService. Checking pipecat.services.deepgram module...")
    try:
        import pipecat.services.deepgram
        print("Module contents:", dir(pipecat.services.deepgram))
    except ImportError:
        print("Module not found.")
