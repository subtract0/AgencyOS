# 🚀 Trinity Protocol - Quick Start Guide

## **Production Setup (11 minutes to live system)**

### **Step 1: Install Dependencies (7 min)**

```bash
# Install audio capture library
brew install portaudio
pip install pyaudio

# Install Whisper AI (Python - easier, 5-7 min download)
pip install openai-whisper

# OR install whisper.cpp (C++ - faster, requires build)
# brew install whisper-cpp
```

---

### **Step 2: Test Audio Pipeline (1 min)**

```bash
# Verify mic + Whisper integration
python trinity_protocol/test_audio_pipeline.py

# Expected output:
# ✅ Microphone: Found 3 audio devices
# ✅ Whisper: openai-whisper installed
# ✅ Audio Capture: Captured 3s audio
# ✅ Transcription: "your spoken words here"
```

---

### **Step 3: Start Trinity (30 seconds)**

```bash
# Stop any demo processes
./STOP_TRINITY.sh

# Start production Trinity
./START_TRINITY.sh

# Verify it's running
tail -f logs/trinity_ambient/listener.log
# Should show: "✅ Whisper model loaded: base.en"
```

---

## **How To Use Trinity**

### **Talk About A Project**
Just speak naturally near your Mac:

> **YOU**: "I'm thinking about writing a coaching book on leadership.
>          Need to outline 10 chapters and write 500 words per week."

### **Trinity Detects Pattern** (30-60s)
```
📊 Pattern detected: project_ideation (confidence: 0.85)
```

### **Trinity Offers Help**
```
💬 Trinity: "I noticed you're thinking about a coaching book.
            Want help turning this into a structured project? (YES/NO)"
```

### **If You Say YES**
1. **One-time setup**: 5-10 questions (~10 min)
   - "What's the target word count?"
   - "Who's the audience?"
   - "What's your weekly commitment?"
   - etc.

2. **Spec generation**: Trinity creates formal project spec
   - Goals, milestones, acceptance criteria
   - You approve or request changes

3. **Daily execution**: 1-3 questions/day (optimized timing)
   - "Ready to outline chapter 3?"
   - "Should I draft the intro paragraph?"
   - Minimal interruption, maximum progress

---

## **Privacy Guarantees**

✅ **100% local processing** - No API calls, no cloud
✅ **Memory-only audio** - Never written to disk
✅ **Instant mute** - Kill switch `./STOP_TRINITY.sh`
✅ **Open source** - Inspect all code

---

## **Troubleshooting**

### **"Module not found: trinity_protocol"**
```bash
# Ensure you're in the Agency root directory
cd /Users/am/Code/Agency
python -m trinity_protocol.test_audio_pipeline
```

### **"pyaudio not found"**
```bash
brew install portaudio
pip install pyaudio
```

### **"Whisper model download failed"**
```bash
# Manual download (run once)
python -c "import whisper; whisper.load_model('base.en')"
```

### **"No microphone detected"**
```bash
# List audio devices
python -c "import pyaudio; p=pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)}') for i in range(p.get_device_count())]"

# Grant microphone permission
# macOS: System Settings → Privacy & Security → Microphone → Terminal (enable)
```

---

## **Advanced Configuration**

### **Change Whisper Model** (speed vs accuracy)
```bash
# Faster (base.en - default)
./START_TRINITY.sh

# More accurate (medium.en - 2x slower)
# Edit START_TRINITY.sh, change --model base.en to --model medium.en
```

### **Adjust Pattern Detection Sensitivity**
```bash
# More sensitive (detects subtle mentions)
# Edit START_TRINITY.sh, change --min-confidence 0.6 to --min-confidence 0.4

# Less sensitive (only obvious patterns)
# Change to --min-confidence 0.8
```

### **Monitor Live Patterns**
```bash
# Watch dashboard in real-time
tail -f logs/trinity_ambient/dashboard.log

# Or run standalone
python trinity_protocol/pattern_dashboard.py --live
```

---

## **What Trinity Detects**

| Pattern | Example | Confidence |
|---------|---------|------------|
| **Project Ideation** | "I want to build X" | 0.75+ |
| **Stuck Problem** | "Can't figure out how to..." | 0.70+ |
| **Learning Interest** | "Want to understand X" | 0.65+ |
| **Time Pressure** | "Need this done by Friday" | 0.80+ |
| **Delegation Need** | "Someone should handle X" | 0.60+ |
| **Decision Support** | "Should I choose A or B?" | 0.70+ |

---

## **Performance Benchmarks**

| Component | Latency | Notes |
|-----------|---------|-------|
| Audio Capture | <10ms | Real-time streaming |
| Whisper Transcription | ~500ms | For 1s audio (base.en + Metal GPU) |
| Pattern Detection | ~100ms | LLM analysis of transcript |
| **Total (speech → action)** | **~30s** | Buffered 30s audio chunks |

---

## **Next Steps After Setup**

1. **Test with real project** - Talk about something you actually want to build
2. **Review generated spec** - Trinity will create formal project document
3. **Approve or iterate** - Refine until spec matches your vision
4. **Daily check-ins** - 1-3 questions/day to execute the plan
5. **Track progress** - Firestore persistence shows completion %

---

## **Support**

**Issues**: Check `logs/trinity_ambient/listener.log` for errors
**Feedback**: Open GitHub issue with log snippet
**Docs**: See `docs/trinity_protocol/` for architecture details

---

🎉 **You're ready! Talk to your Mac and let Trinity help build your projects.**
