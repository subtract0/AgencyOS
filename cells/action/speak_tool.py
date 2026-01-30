
from cells.shared.lean_agent import tool, ToolParameter, ToolPropertySchema
import asyncio
from cells.shared.message_bus import async_message_bus

@tool(
    name="speak",
    description="Speak a message clearly to the user via TTS. Use this to give bold announcements or critical updates. Do not overuse.",
    parameters=ToolParameter(
        type="object",
        properties={
            "text": ToolPropertySchema(type="string", description="The text to speak")
        },
        required=["text"]
    )
)
def speak(text: str) -> str:
    print(f"📣 Calling Voice Cell: {text}")
    
    async def _publish():
        try:
            async with async_message_bus() as bus:
                await bus.publish("voice", {
                    "action": "speak",
                    "text": text
                })
        except Exception as e:
            print(f"Bus Error: {e}")
            raise e

    try:
        # Check if we are already in an event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            # We are in an async loop (unlikely for ActionCell sync tools but possible)
            # This is tricky. Ideally tools should be async.
            # For now, assuming ActionCell runs tools in a thread or sync.
             asyncio.run(_publish())
        else:
             asyncio.run(_publish())
             
        return f"Voice Command Sent: '{text}'"
    except Exception as e:
        return f"Error connecting to Voice Cell: {e}"
