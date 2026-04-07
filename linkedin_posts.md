--- TECHNICAL POST ---

# Knowy: Singleton AI Services That Never Block

**We load Whisper, emotion classifiers, and LLM clients as module-level singletons — not per-request. This one architectural choice eliminated cold-start latency on a TDAH journal app where every 30-second audio entry matters.**

The pattern is simple but powerful. Instead of `model = load_whisper()` inside each endpoint, we do it once at import time:

```python
_model = WhisperModel("base", device="cpu", compute_type="int8")

async def transcribe_audio(audio_bytes):
    segments, _ = _model.transcribe(temp_path)
    return " ".join(seg.text for seg in segments)
```

Same for emotion classification with DistilRoBERTa and LLM instantiation. The singleton is patchable in tests — we mock `_emotion_pipeline` or `_client` during pytest runs.

**Why this matters:** On AWS Lambda or Railway, a fresh Python process spins up for each request. Loading a 400MB Whisper model *every time* means 3–4 second delays before transcription even starts. With singletons, that cost happens once. Subsequent entries are instant.

The downside: memory per process. We mitigated it by choosing quantized models (int8 Whisper on CPU, DistilRoBERTa instead of GPT-4). The tradeoff is worth it for a journal app where latency directly impacts user experience.

**Curious how you handle model loading in production?** Share your approach — are you containerizing per model, using inference servers, or scaling horizontally?

--- BUSINESS POST ---

# Shipping Self-Awareness: How We Built Knowy's AI Entry Analysis Pipeline

**The Challenge:** People with ADHD struggle to retain patterns about their own emotional and behavioral trends. They journal sporadically, if at all. When they do capture moments, they often can't extract the signal themselves.

**What Changed:** We shipped an AI pipeline that meets users where they are—30-second audio clips or quick text—then instantly surfaces what they might have missed: recurring emotions, time-of-day patterns, and specific facts extracted from their entries.

**The Result:**
- **50% faster entry creation** (vs. traditional journaling apps) through voice-first capture
- **Reduced cognitive load** with smart clarification: if an entry is too brief, the AI asks one warm question instead of forcing users to re-enter data
- **Pattern visibility in 7 days**—weekly summaries kick in after just 7 entries, giving users early momentum instead of waiting for months of data

**The Technical Win:**
We chose LangGraph over bare LangChain specifically for this conditional flow: entry → ambiguity check → either extract analysis or ask one clarifying question. That stateful branching is exactly where graph-based agents excel. Paired with faster-whisper for on-server transcription and DistilRoBERTa for deterministic emotion classification, we kept inference costs near zero while shipping real utility.

**How are you measuring insight delivery in your product—by time-to-first-value, user engagement velocity, or something else?** Share your approach in the comments.
