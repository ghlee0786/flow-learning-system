"""Supertonic TTS로 레슨 음성을 만듭니다.

문장(장면)마다 따로 합성해 앞뒤 무음을 잘라 내고, 사이에 짧은 쉼을 넣어 이어 붙입니다.
이어 붙이는 동안 각 문장이 몇 초에 시작하고 끝나는지 기록해 timing.json에 남기고,
플레이어는 이 시각표로 장면을 바꿉니다. 같은 문장·같은 음성은 캐시를 다시 씁니다.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import wave
from pathlib import Path

SR = 44100
GAP = 0.45


def cache_dir() -> Path:
    d = Path(os.environ.get("FLS_CACHE", Path.home() / ".cache" / "flow-learning-system" / "speech"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def lesson_hash(sentences: list[str], voice: str, speed: float) -> str:
    h = hashlib.sha1(f"{voice}|{speed}".encode())
    for s in sentences:
        h.update(s.encode("utf-8") + b"\x00")
    return h.hexdigest()[:16]


class Synth:
    def __init__(self, voice: str = "F1", speed: float = 1.05, steps: int = 8):
        try:
            import numpy as np  # noqa: F401
            from supertonic import TTS
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("음성 합성에는 supertonic이 필요합니다: pip install 'flow-learning-system[tts]'") from e
        self.tts = TTS(auto_download=True)
        self.style = self.tts.get_voice_style(voice_name=voice)
        self.voice, self.speed, self.steps = voice, speed, steps

    def sentence(self, parts):
        """parts: 읽을 문장 문자열, 또는 [(언어, 문장), …] (한국어와 영어가 섞인 문장)"""
        import numpy as np
        if isinstance(parts, str):
            parts = [("ko", parts)]
        out = []
        for i, (lang, text) in enumerate(parts):
            if i:
                out.append(np.zeros(int(0.12 * SR), np.float32))
            out.append(self._part(lang, text))
        return np.concatenate(out) if out else np.zeros(int(0.3 * SR), np.float32)

    def _part(self, lang: str, text: str):
        import numpy as np
        tag = f"{self.voice}|{self.speed}|{text}" if lang == "ko" else f"{self.voice}|{self.speed}|{lang}|{text}"
        key = hashlib.md5(tag.encode()).hexdigest()[:20]
        f = cache_dir() / f"{key}.npy"
        if f.exists():
            return np.load(f)
        w, _ = self.tts.synthesize(text, voice_style=self.style, lang=lang, total_steps=self.steps, speed=self.speed)
        w = np.asarray(w).reshape(-1).astype(np.float32)
        a = np.abs(w)
        idx = np.where(a > 0.004)[0]
        if len(idx):
            w = w[max(0, idx[0] - int(0.03 * SR)): min(len(w), idx[-1] + int(0.08 * SR))]
        np.save(f, w)
        return w


def write_audio(samples, out_base: Path) -> Path:
    """samples(float32) → mp3(ffmpeg가 있으면) 또는 wav."""
    import numpy as np
    pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes()
    if shutil.which("ffmpeg"):
        out = out_base.with_suffix(".mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "48k", str(out)], input=pcm, check=True)
        return out
    out = out_base.with_suffix(".wav")
    with wave.open(str(out), "wb") as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes(pcm)
    return out


def synthesize_lesson(synth: Synth, sentences: list, out_base: Path, progress=None):
    """문장(또는 [(언어, 문장), …]) 목록 → 음성 파일과 [[시작, 끝], …]"""
    import numpy as np
    parts, segs, pos = [], [], 0.0
    for i, s in enumerate(sentences):
        w = synth.sentence(s)
        segs.append([round(pos, 3), round(pos + len(w) / SR, 3)])
        parts.append(w)
        pos += len(w) / SR
        parts.append(np.zeros(int(GAP * SR), np.float32))
        pos += GAP
        if progress:
            progress(i + 1, len(sentences))
    out = write_audio(np.concatenate(parts), out_base)
    return out, segs
