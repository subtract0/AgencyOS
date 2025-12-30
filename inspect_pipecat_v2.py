
import pipecat
import pipecat.services
import pkgutil

print("Submodules in pipecat.services:")
for loader, module_name, is_pkg in pkgutil.walk_packages(pipecat.services.__path__):
    print(module_name)
    
print("\nChecking for STTService in pipecat.services:")
try:
    from pipecat.services.stt import STTService
    print("Found at pipecat.services.stt")
except ImportError:
    print("Not at pipecat.services.stt")
