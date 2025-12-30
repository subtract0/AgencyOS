
import inspect
import pipecat.services

print("Members of pipecat.services:")
for name, member in inspect.getmembers(pipecat.services):
    if inspect.isclass(member):
        print(f"Class: {name}")
    elif inspect.ismodule(member):
        print(f"Module: {name}")

# Also check if there is a 'stt' module directly
try:
    import pipecat.services.stt
    print("\npipecat.services.stt exists!")
except ImportError:
    print("\npipecat.services.stt does NOT exist.")
