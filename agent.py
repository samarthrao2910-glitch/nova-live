import os
import sys
import logging
from dotenv import load_dotenv

# --- STEP 1: KEY CONFIGURATION ---
# Fill these in inside the quotes. 
# This allows your parents to run the app even without a .env file.
os.environ["GOOGLE_API_KEY"] = "AIzaSyCfcexdgN_pe15EmdxJanLLakk9opRsxEw"
os.environ["LIVEKIT_URL"] = "wss://chorus-live-iv56jeqg.livekit.cloud"
os.environ["LIVEKIT_API_KEY"] = "APIgZaMfb8AtuVv"
os.environ["LIVEKIT_API_SECRET"] = "yCv9SeJTwmyitJRaYCkQiwsT390ItsRPEulJiJOPkvP"

# --- STEP 2: PATH HANDLING FOR EXECUTABLE ---
if getattr(sys, 'frozen', False):
    # Running as a bundled executable
    bundle_dir = sys._MEIPASS
    application_path = os.path.dirname(sys.executable)
else:
    # Running as a normal script
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
    application_path = bundle_dir

# Add the bundle directory to sys.path so it can find prompts.py and tools.py
sys.path.append(bundle_dir)

# Try to load .env if it exists nearby (this overrides hardcoded keys)
dotenv_path = os.path.join(application_path, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# --- STEP 3: ASSISTANT LOGIC ---
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation, google

# Import your custom logic
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import get_weather, search_web, send_email

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                voice="Charon",
                temperature=0.8,
            ),
            tools=[
                get_weather,
                search_web,
                send_email
            ],
        )

async def entrypoint(ctx: agents.JobContext):
    print("Nova Live is initializing...")
    session = AgentSession()

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()
    print(f"Connected to room: {ctx.room.name}")

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )

if __name__ == "__main__":
    print("--- Starting Nova Live Assistant ---")
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))