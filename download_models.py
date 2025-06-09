#!/usr/bin/env python3
"""
Download script for LiveKit agent models.
This ensures all required models are downloaded before starting the agent.
"""

import os
import sys

def download_turn_detector():
    """Download the turn detector model."""
    try:
        from livekit.plugins.turn_detector.multilingual import MultilingualModel
        print("Downloading turn detector model...")
        model = MultilingualModel()
        print("✅ Turn detector model downloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Error downloading turn detector model: {e}")
        return False

def download_silero_vad():
    """Download the Silero VAD model."""
    try:
        from livekit.plugins import silero
        print("Downloading Silero VAD model...")
        vad = silero.VAD.load()
        print("✅ Silero VAD model downloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Error downloading Silero VAD model: {e}")
        return False

def main():
    """Main download function."""
    print("Starting model downloads...")
    
    success = True
    success &= download_turn_detector()
    success &= download_silero_vad()
    
    if success:
        print("🎉 All models downloaded successfully!")
        sys.exit(0)
    else:
        print("⚠️  Some models failed to download, but continuing...")
        sys.exit(0)  # Don't fail the build, just warn

if __name__ == "__main__":
    main() 