
import inspect
try:
    import pipecat.services.google
    print("Classes in pipecat.services.google:")
    for name, obj in inspect.getmembers(pipecat.services.google):
        if inspect.isclass(obj):
            print(f"- {name} (Base: {obj.__bases__})")
except ImportError:
    print("Could not import pipecat.services.google")
