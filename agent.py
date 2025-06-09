import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    metrics,
    RoomInputOptions,
)
from livekit.plugins import (
    cartesia,
    openai,
    deepgram,
    noise_cancellation,
    silero,
)
# Import removed - we'll use simpler turn detection


load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")


class Assistant(Agent):
    def __init__(self) -> None:
        # This project is configured to use Deepgram STT, OpenAI LLM and Cartesia TTS plugins
        # Other great providers exist like Cerebras, ElevenLabs, Groq, Play.ht, Rime, and more
        # Learn more and pick the best one for your app:
        # https://docs.livekit.io/agents/plugins
        
        # Use simpler turn detection that doesn't require model downloads
        # The agent will use VAD-based turn detection which is more reliable in production
        turn_detection = None
        
        super().__init__(
            instructions="You are the voice of Pools, the go-to destination for reality TV lovers to talk, play, and obsess together. "
            "You're a witty, pop-culture-savvy voice agent who lives and breathes reality TV. Think of yourself as the ultimate companion "
            "for fans who want to chat about the latest drama, cast gossip, episode recaps, fan theories, and iconic moments from shows "
            "like The Bachelor, Love Island, The Kardashians, Real Housewives, Survivor, and more. "
            "\n\nYour job is to: "
            "Talk casually with users about what's happening in reality TV right now. "
            "Help them engage with Pools — whether it's checking on an active pool, explaining how leagues work, or suggesting what shows are trending in the app. "
            "Recommend shows or Pools to join based on their interests. "
            "Keep it fun, fast, and a little dramatic (in a good way). "
            "\n\nYou're like a sassy best friend who's always in the know and plugged into the Pools universe. Speak naturally and conversationally. "
            "Stay casual, excited, and helpful — your voice should make users feel like they're part of the show and the community. "
            "Use short and concise responses, avoiding unpronounceable punctuation.",
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(voice="79a125e8-cd45-4c13-8a67-188112f4dd22"),  # Cartesia female voice
            # use LiveKit's transformer-based turn detector
            turn_detection=turn_detection,
        )

    async def on_enter(self):
        # Give a fun, reality TV-themed greeting
        self.session.generate_reply(
            instructions="Hey there, reality TV obsessed bestie! What's the tea today? Want to chat about the latest drama or check out what's happening in your Pools?", 
            allow_interruptions=True
        )


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    usage_collector = metrics.UsageCollector()

    # Log metrics and collect usage data
    def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
        metrics.log_metrics(agent_metrics)
        usage_collector.collect(agent_metrics)

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        # minimum delay for endpointing, used when turn detector believes the user is done with their turn
        min_endpointing_delay=0.5,
        # maximum delay for endpointing, used when turn detector does not believe the user is done with their turn
        max_endpointing_delay=5.0,
    )

    # Trigger the on_metrics_collected function when metrics are collected
    session.on("metrics_collected", on_metrics_collected)

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # enable background voice & noise cancellation, powered by Krisp
            # included at no additional cost with LiveKit Cloud
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
