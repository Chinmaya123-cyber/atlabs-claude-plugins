#!/usr/bin/env python3
"""QC one Atlabs clip: frame sheets, transcript, detected language, match vs VO, sync offset.

usage (with the venv from setup):
  ~/.story-fixer-venv/bin/python qc_clip.py <clip.mp4 | url> [--vo vo.mp3] [--lang he]
      [--model small|large-v3] --out qc/12

writes <out>.jpg (8-frame sheet), <out>_first1s.jpg (every frame of the first 1.25 s),
<out>.wav, <out>_vo.wav, <out>.json, and prints the json.
--lang only biases the transcript; the language is DETECTED separately, so a clip
speaking the wrong language is caught.
Needs ffmpeg/ffprobe; faster-whisper (preferred) or openai-whisper; numpy.
Any missing piece or failure is skipped and reported in "notes", never fatal.
"""
import argparse, difflib, json, os, re, subprocess, sys, tempfile


def sh(*a, **k):
    return subprocess.run(list(a), capture_output=True, text=True, **k)


def duration(p):
    r = sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p)
    return float(r.stdout.strip() or 0)


def probe_video(p):
    r = sh("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
           "stream=width,height,r_frame_rate", "-of", "json", p)
    try:
        s = json.loads(r.stdout)["streams"][0]
        num, den = s["r_frame_rate"].split("/")
        return {"width": s["width"], "height": s["height"], "fps": round(int(num) / int(den), 2)}
    except Exception:
        return {}


def fresh(*paths):
    for p in paths:
        try:
            os.remove(p)
        except FileNotFoundError:
            pass


def to_wav(src, dst):
    fresh(dst)
    r = sh("ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", dst)
    return r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 1000


def mean_db(wav):
    r = sh("ffmpeg", "-i", wav, "-af", "volumedetect", "-f", "null", "-")
    m = re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr)
    return float(m.group(1)) if m else None


def load_pcm(wav):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


_model = None


def detect_language(wav, size):
    """language detected WITHOUT forcing: (code, probability) or (None, None)"""
    global _model
    try:
        from faster_whisper import WhisperModel
        if _model is None:
            _model = WhisperModel(size, device="cpu", compute_type="int8")
        _, info = _model.transcribe(load_pcm(wav), language=None, vad_filter=True)
        return info.language, round(info.language_probability, 2)
    except ImportError:
        pass
    try:
        import whisper
        if _model is None:
            _model = whisper.load_model(size)
        audio = whisper.pad_or_trim(whisper.load_audio(wav))
        mel = whisper.log_mel_spectrogram(audio, n_mels=_model.dims.n_mels).to(_model.device)
        _, probs = _model.detect_language(mel)
        code = max(probs, key=probs.get)
        return code, round(float(probs[code]), 2)
    except ImportError:
        return None, None


def transcribe(wav, lang, size):
    """returns dict(text, language, language_p, segments[(s,e)], words[(w,s,e)], backend) or None"""
    global _model
    try:
        from faster_whisper import WhisperModel
        if _model is None:
            _model = WhisperModel(size, device="cpu", compute_type="int8")
        segs, info = _model.transcribe(load_pcm(wav), language=lang, vad_filter=True, word_timestamps=True)
        segs = list(segs)
        words = [(w.word.strip(), round(w.start, 2), round(w.end, 2)) for s in segs for w in (s.words or [])]
        return {"text": " ".join(s.text.strip() for s in segs), "language": info.language,
                "language_p": round(info.language_probability, 2),
                "segments": [(round(s.start, 2), round(s.end, 2)) for s in segs],
                "words": words, "backend": "faster-whisper"}
    except ImportError:
        pass
    try:
        import whisper
        if _model is None:
            _model = whisper.load_model(size)
        r = _model.transcribe(wav, language=lang, word_timestamps=True)
        words = [(w["word"].strip(), round(w["start"], 2), round(w["end"], 2))
                 for s in r["segments"] for w in s.get("words", [])]
        return {"text": r["text"].strip(), "language": r.get("language"), "language_p": None,
                "segments": [(round(s["start"], 2), round(s["end"], 2)) for s in r["segments"]],
                "words": words, "backend": "openai-whisper"}
    except ImportError:
        return None


def norm(t):
    return re.sub(r"[\W_]+", "", (t or "").lower())


def speech_span(words, segments):
    if words:
        return round(words[-1][2] - words[0][1], 2)
    if segments:
        return round(segments[-1][1] - segments[0][0], 2)
    return None


def word_offset(cw, vw):
    """median difference of matching word centres, clip minus VO (s)."""
    if not cw or not vw:
        return None
    a = [norm(w[0]) for w in cw]
    b = [norm(w[0]) for w in vw]
    diffs = []
    for blk in difflib.SequenceMatcher(None, a, b).get_matching_blocks():
        for i in range(blk.size):
            c, v = cw[blk.a + i], vw[blk.b + i]
            diffs.append(((c[1] + c[2]) / 2) - ((v[1] + v[2]) / 2))
    if not diffs:
        return None
    diffs.sort()
    return round(diffs[len(diffs) // 2], 2)


def env_corr(wa, wb):
    try:
        import numpy as np
        a, b = load_pcm(wa), load_pcm(wb)
        hop = 160
        ea = np.sqrt(np.convolve(a ** 2, np.ones(hop) / hop, "valid")[::hop])
        eb = np.sqrt(np.convolve(b ** 2, np.ones(hop) / hop, "valid")[::hop])
        ea = (ea - ea.mean()) / (ea.std() + 1e-9)
        eb = (eb - eb.mean()) / (eb.std() + 1e-9)
        c = np.correlate(ea, eb, "full") / len(eb)
        k = int(c.argmax()) - (len(eb) - 1)
        return round(float(c.max()), 2), round(k * hop / 16000, 2)
    except Exception:
        return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--vo")
    ap.add_argument("--lang", help="ISO code of the story language, e.g. en, he, ar, hi")
    ap.add_argument("--model", default="small", help="whisper size; use large-v3 for he/ar/hi")
    ap.add_argument("--out", required=True, help="output path prefix, e.g. qc/12")
    ap.add_argument("--frames", type=int, default=8)
    a = ap.parse_args()

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    clip = a.clip
    if clip.startswith("http"):
        local = a.out + ".mp4"
        subprocess.run(["curl", "-sfL", clip, "-o", local], check=True)
        clip = local

    out = {"clip": clip, "notes": []}
    d = duration(clip)
    out["duration_s"] = round(d, 2)
    out.update(probe_video(clip))

    fresh(a.out + ".jpg", a.out + "_first1s.jpg", a.out + ".json", a.out + "_vo.wav")
    n = a.frames
    cols = 4
    rows = (n + cols - 1) // cols
    r1 = sh("ffmpeg", "-v", "error", "-y", "-i", clip, "-vf",
            f"fps={n}/{max(d, 0.1)},scale=360:-2,tile={cols}x{rows}", "-frames:v", "1", a.out + ".jpg")
    # every frame of the first 1.25 s (30 frames at 24 fps) to catch character-sheet / reference flashes
    r2 = sh("ffmpeg", "-v", "error", "-y", "-i", clip, "-vf",
            "trim=end_frame=30,scale=200:-2,tile=6x5", "-frames:v", "1", a.out + "_first1s.jpg")
    if r1.returncode or r2.returncode:
        out["notes"].append("frame sheet failed: " + (r1.stderr or r2.stderr).strip()[:200])
    out["sheet"] = a.out + ".jpg"
    out["first_second_sheet"] = a.out + "_first1s.jpg"

    wav = a.out + ".wav"
    if not to_wav(clip, wav):
        out["notes"].append("clip has no audio track")
        print(json.dumps(out, ensure_ascii=False, indent=1))
        json.dump(out, open(a.out + ".json", "w"), ensure_ascii=False, indent=1)
        return
    out["clip_mean_db"] = mean_db(wav)
    if out["clip_mean_db"] is not None and out["clip_mean_db"] < -35:
        out["notes"].append("clip audio is near-silent (no speech likely)")

    try:
        out["detected_language"], out["detected_language_p"] = detect_language(wav, a.model)
        ct = transcribe(wav, a.lang, a.model)
    except Exception as e:  # model download, decode errors, etc.
        out["notes"].append(f"whisper failed: {type(e).__name__}: {str(e)[:200]}")
        ct = None
    if ct is None:
        if not any(n.startswith("whisper failed") for n in out["notes"]):
            out["notes"].append("whisper not installed: speech checks skipped")
    else:
        out["clip_text"] = ct["text"]
        out["clip_language"] = ct["language"]
        out["clip_language_p"] = ct["language_p"]
        out["clip_speech_segments"] = ct["segments"]
        out["clip_speech_span_s"] = speech_span(ct["words"], ct["segments"])
        dl = out.get("detected_language")
        if a.lang and dl and dl != a.lang and ct["text"].strip():
            out["notes"].append(f"language mismatch: clip sounds like {dl} (p={out.get('detected_language_p')}), expected {a.lang}")
        if re.search(r"thank(s| you) for watching", ct["text"] or "", re.I):
            out["notes"].append("whisper filler phrase found: likely silence or hallucination")

    if a.vo:
        vwav = a.out + "_vo.wav"
        if not to_wav(a.vo, vwav):
            out["notes"].append("could not decode the VO file: VO checks skipped")
            json.dump(out, open(a.out + ".json", "w"), ensure_ascii=False, indent=1)
            print(json.dumps(out, ensure_ascii=False, indent=1))
            return
        out["vo_duration_s"] = round(duration(a.vo), 2)
        try:
            vt = transcribe(vwav, a.lang, a.model) if ct is not None else None
        except Exception as e:
            out["notes"].append(f"whisper failed on VO: {type(e).__name__}")
            vt = None
        if vt:
            out["vo_text"] = vt["text"]
            out["vo_speech_span_s"] = speech_span(vt["words"], vt["segments"])
            out["text_similarity"] = round(difflib.SequenceMatcher(None, norm(ct["text"]), norm(vt["text"])).ratio(), 2)
            out["word_offset_s"] = word_offset(ct["words"], vt["words"])
            if out.get("clip_speech_span_s") and out.get("vo_speech_span_s"):
                ratio = out["clip_speech_span_s"] / max(out["vo_speech_span_s"], 0.01)
                out["speech_span_ratio"] = round(ratio, 2)
                if ratio > 1.12 or ratio < 0.88:
                    out["notes"].append("speech span differs >12% from VO: line may be re-voiced or re-timed")
        corr, off = env_corr(wav, vwav)
        out["env_corr"], out["env_offset_s"] = corr, off

    json.dump(out, open(a.out + ".json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
