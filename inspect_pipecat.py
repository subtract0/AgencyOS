
import inspect
from pipecat.services.stt import STTService

print("STTService methods:")
for name, method in inspect.getmembers(STTService):
    if not name.startswith("_"):
        print(f"- {name}")

print("\nSTTService docstring:")
print(STTService.__doc__)
print("\nSTTService source (partial):")
try:
    print(inspect.getsource(STTService.run_stt)[:500])
except:
    print("Could not get source for run_stt")
