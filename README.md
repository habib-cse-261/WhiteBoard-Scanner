Live URL: https://whiteboard-scanner-f4kha2jakqpjczwl36sny8.streamlit.app/

# 🎓 Whiteboard to Interactive Study Guide

An AI-powered tool that turns a photo of a messy classroom whiteboard — Bangla, English, or mixed — into a clean, structured, interactive study guide, powered by **Gemma 4 Vision** with native function calling.

Built for **The Multimodal Track** (Best use of Gemma 4's vision capabilities for vision-to-text use cases).

---

## The Problem

Bangladeshi CS students take photos of whiteboards after every class, but those photos are usually messy, mixed-language (Bangla/English/Banglish), full of crossed-out corrections, arrows, and half-finished diagrams — and they just sit unused in a camera roll. Re-reading and organizing them into usable study material takes real time and effort, especially for students who missed the class entirely.

## The Solution

Snap a photo → Gemma 4 Vision reads, understands, and reconstructs the lecture → get back organized Markdown notes, extracted/cleaned code, and quality flashcards, all in one pass.

This is **not OCR**. The system is explicitly instructed to reason like a teaching assistant: read → understand → organize → clean → explain → structure — not just transcribe pixels into text.

---

## Core Features

- **Multimodal Vision Understanding** — reads handwriting, diagrams, flowcharts, and tables directly from a photo.
- **Bangla-First Language Handling** — preserves Bangla, English, and Banglish exactly as written; never force-translates.
- **Intelligent Lecture Reconstruction** — reorders scattered board content into a logical teaching flow instead of a literal transcription.
- **Automatic Content Classification via Function Calling** — Gemma decides which function(s) to call based on actual content: Notes, Code/Pseudocode, or Flashcards.
- **Flowchart-to-Pseudocode Conversion** *(differentiator)* — hand-drawn flowcharts are converted into structured pseudocode reflecting the real logic, not just transcribed shapes.
- **Multi-Topic Detection** — separates unrelated topics on the same board into distinct labeled sections.
- **Noise Filtering** — ignores smudges, crossed-out text, and camera artifacts.
- **Confidence-Aware Output** — flags illegible handwriting instead of hallucinating content.
- **"Explain Like I Missed the Class" Mode** *(differentiator)* — one-tap toggle that expands every concept with simple, beginner-friendly Bangla explanations.
- **Quality-Focused Flashcards** — generates understanding-testing questions, not trivial recall questions.
- **Bandwidth-Conscious Design** — client-side image compression, built for Bangladesh's variable mobile connectivity.
- **Zero-Friction Mobile UX** — camera-first capture, no login required.
- **Exportable Output** — one-click download as a `.md` file.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python |
| UI | [Streamlit](https://streamlit.io) |
| Vision Model | Gemma 4 (`gemma-4-31b-it`) via the Gemini API |
| SDK | `google-genai` |
| Image handling | Pillow (PIL) |
| Env config | `python-dotenv` |

---

## Architecture

```
[Phone Camera / Upload]
        │
        ▼
[Streamlit UI]  (app.py)
        │
        ▼
[Image Preprocessing]  (resize + compress for low bandwidth)
        │
        ▼
[Gemma 4 Vision API Call]  (gemma_client.py)
   — structured function-calling output —
        │
        ▼
[Router: which function(s) did Gemma call?]
        │
        ├─→ generate_markdown_notes()   → clean structured notes
        ├─→ extract_code_snippet()      → code / pseudocode
        └─→ generate_flashcards()       → Q&A flashcards
        │
        ▼
[Streamlit Output View]  (tabs: Notes / Code / Flashcards)
        │
        ▼
[Export] → Download as .md
```

### Project Structure

```
.
├── app.py              # Streamlit UI: input, state, rendering, export
├── gemma_client.py      # Image preprocessing, prompt, Gemma API call, parsing
├── .env                  # GEMINI_API_KEY (not committed)
└── README.md
```

---

## Setup

### 1. Install dependencies

```bash
pip install streamlit pillow google-genai python-dotenv
```

### 2. Get a Gemini API key

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Create an API key
3. Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

### 3. Run the app

```bash
streamlit run app.py
```

---

## Usage

1. Open the app (browser or phone).
2. Take a photo of a whiteboard, or upload one from your gallery.
3. (Optional) Toggle **"I missed the class"** for extended plain-Bangla explanations.
4. Click **Process Image**.
5. Browse results across the **Notes**, **Code**, and **Flashcards** tabs.
6. Download the combined study guide as a `.md` file.

---

## Bangladesh-Context Design Decisions

- **Language**: prompt explicitly preserves Bangla/Banglish instead of translating, since students think and write in mixed language.
- **Connectivity**: images are compressed client-side before upload to reduce data usage on mobile networks.
- **Device access**: camera-first input, designed for phone use over desktop/scanner workflows.
- **Literacy/accessibility**: no login, no settings screen — one clear action, one clear output.

---

## Hackathon Track

**The Multimodal Track** — Whiteboard to Interactive Study Guide (localized theme)
Uses Gemma 4's vision capabilities and native function calling to go beyond a simple chatbot, delivering real automation (classification, structuring, export) grounded in Bangladesh's language and connectivity context.
