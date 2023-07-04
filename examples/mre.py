import os
import sys
import random

from datetime import datetime
from typing import Any, Callable

from voicechangerio import VoiceChangerIO


def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        execution_time = end_time.timestamp() - start_time.timestamp()

        print(f"Function '{func.__name__}'")
        print(f"Start time: {start_time}")
        print(f"End time: {end_time}")
        print(f"Execution time: {execution_time:.3}s.")

        return result
    return wrapper


@measure_time
def main() -> int:
    voice_changer_io = VoiceChangerIO("--headless", "--mute-audio")
    voice_effect = random.choice(voice_changer_io.voice_effects)
    with open(os.path.abspath("sample.mp3"), "rb") as file:
        file_bytes = file.read()

    audio_file = voice_changer_io.apply_voice_effect(audio_file=file_bytes, voice_effect=voice_effect)
    voice_changer_io.save_audio_file(audio_file, "TEST")
    return 0


if __name__ == "__main__":
    sys.exit(main())
