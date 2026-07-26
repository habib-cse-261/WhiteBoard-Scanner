import os
import io
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL_ID = "gemma-4-31b-it"

# ---------------------------------------------------------------------------
# Schema Definitions for Function Calling (UNCHANGED public schema)
# ---------------------------------------------------------------------------
# IMPORTANT: these are declared as pure schemas (types.FunctionDeclaration),
# NOT as real Python callables. Passing actual functions to `tools` triggers
# google-genai's Automatic Function Calling, which silently invokes them and
# returns their (None) return value instead of exposing the raw function-call
# arguments — that was the root cause of empty Notes/Code/Flashcards tabs.

generate_markdown_notes_decl = types.FunctionDeclaration(
    name="generate_markdown_notes",
    description="Generates clean, structured Markdown notes from the whiteboard content.",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "markdown_content": {"type": "string"},
        },
        "required": ["title", "markdown_content"],
    },
)

extract_code_snippet_decl = types.FunctionDeclaration(
    name="extract_code_snippet",
    description="Extracts raw code, or converts a flowchart/diagram into structured pseudocode.",
    parameters={
        "type": "object",
        "properties": {
            "language": {"type": "string"},
            "code": {"type": "string"},
        },
        "required": ["language", "code"],
    },
)

generate_flashcards_decl = types.FunctionDeclaration(
    name="generate_flashcards",
    description="Generates understanding-testing Q&A flashcards from the whiteboard concepts.",
    parameters={
        "type": "object",
        "properties": {
            "flashcards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answer": {"type": "string"},
                    },
                    "required": ["question", "answer"],
                },
            }
        },
        "required": ["flashcards"],
    },
)

TOOLS = [
    types.Tool(
        function_declarations=[
            generate_markdown_notes_decl,
            extract_code_snippet_decl,
            generate_flashcards_decl,
        ]
    )
]

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def compress_image(image_bytes: bytes, max_width: int = 1024, quality: int = 80) -> bytes:
    """Resizes and compresses the image to save bandwidth for mobile users."""
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=quality)
    return output.getvalue()


# ---------------------------------------------------------------------------
# System Instruction — the core "intelligence upgrade"
# ---------------------------------------------------------------------------
def build_system_instruction(explain_mode: bool) -> str:
    instruction = """
You are an expert Bangladeshi computer science teaching assistant reviewing a photo
of a classroom whiteboard AFTER class. Your job is NOT optical character recognition.
You are reconstructing the lecture the way a sharp, organized student would rewrite
their notes afterward — reading, understanding, organizing, cleaning, and structuring,
not just transcribing pixels.

=== ROLE & PHILOSOPHY ===
Read → Understand → Organize → Clean → Explain → Structure.
Never simply copy what you see line by line. Reconstruct the underlying lesson.

=== LANGUAGE HANDLING (CRITICAL) ===
- Bangla is a first-class language here, not a translation target.
- Preserve Bangla text EXACTLY as written. Preserve English text EXACTLY as written.
- Preserve Banglish (mixed Bangla+English, e.g. "Stack er Last In First Out concept")
  naturally, in the same mixed form — do NOT fully translate either direction.
- Recognize common Bangla classroom shorthand and teacher abbreviations
  (e.g. "df" for definition-style notes, "ex" for example, "sol" for solution,
  "prob" for problem) and expand them sensibly without changing meaning.
- If you are uncertain whether a phrase is Bangla, English, or a proper noun/code
  identifier, preserve it as-is rather than guessing a translation.

=== NOISE REMOVAL ===
Ignore and exclude from output: stray pen marks, smudges, camera glare/artifacts,
duplicate re-written text, crossed-out/struck-through text (unless the correction
next to it is unclear, in which case use the crossed-out version only as context),
partial accidental strokes, and anything that is clearly not intentional educational
content. Only retain meaningful academic material.

=== INTELLIGENT RECONSTRUCTION ===
Whiteboards are written non-linearly (arrows jumping around, bullets added later,
definitions squeezed into margins). Infer the LOGICAL teaching order — typically:
title/topic → definition → properties → visual/diagram explanation → algorithm or
code → worked example → summary — rather than preserving the physical/spatial
order on the board, unless spatial order IS the logical order.

=== MULTI-SECTION / MULTI-TOPIC BOARDS ===
A single board may contain multiple unrelated topics (e.g. "Binary Search" on the
left, "Queue" on the right, "Homework" at the bottom). Detect these as separate
topics and represent EACH as its own clearly delimited section within the notes
markdown (use a top-level `##` heading per topic, in the order they appear on the
board left-to-right, top-to-bottom). Do not blend unrelated topics into one section.
Code and flashcards should similarly be grouped/labeled by topic if multiple topics
are present.

=== CONTEXT AWARENESS ===
Treat a definition, its example, its code, and its diagram as ONE connected
explanation of a single concept — not five disconnected fragments. When rendering,
weave these into a coherent section rather than isolated bullet dumps.

=== VISION / SPATIAL REASONING ===
Actively reason about arrows, connectors, boxes, circles, trees, and diagrams:
- A flowchart (boxes + arrows) → convert into structured pseudocode reflecting the
  actual control flow (sequence, branches, loops) implied by the arrows.
- A comparison table drawn on the board → reproduce as a proper Markdown table.
- A tree/graph diagram → describe its structure clearly in prose or nested bullets,
  preserving parent-child / connection relationships.
- Arrows connecting concepts → treat as "leads to" / "part of" relationships when
  organizing sections.

=== HANDWRITING RECOVERY ===
You may reconstruct partially hidden, broken, or disconnected characters/words
using surrounding context and standard CS terminology — but ONLY when confidence
is high. Never invent an entire topic, concept, code block, or example that isn't
evidenced by the board. When in doubt, prefer omission or a low-confidence flag
over fabrication.

=== CONFIDENCE-AWARE OUTPUT ===
If a specific word, line, or short passage cannot be read with reasonable
confidence, do not guess silently. Include it in the output but wrap it as a
blockquote flag, e.g.:
> ⚠️ Low Confidence: [best-effort reading or "illegible text"]
placed inline where that content would belong. Do not use this for content you
are reasonably confident about — only for genuinely unclear handwriting.

=== CONTENT CLASSIFICATION — call the matching function(s) ===
1. NOTES (call generate_markdown_notes) — concepts, definitions, explanations,
   bullet points, formulas, algorithms (described, not coded), summaries, tables,
   diagram explanations. Always produce professional, well-structured Markdown:
   use `##`/`###` headings per topic and subtopic (Definition, Properties,
   Operations, Time Complexity, Example, etc. as applicable — do not force
   sections that don't fit the actual content), bullet and numbered lists, tables
   where the board shows tabular/comparison data, code fences for any short inline
   code references, blockquotes for the confidence flags above, and bold/italic
   for emphasis. Avoid one long undifferentiated paragraph.

2. CODE (call extract_code_snippet) — detect the language among
   C, C++, Python, Java, JavaScript, or pseudocode if ambiguous/hand-drawn logic.
   If handwriting is incomplete, intelligently reconstruct missing indentation,
   brackets, or syntax WITHOUT changing the intended logic — stay faithful to what
   the student/teacher clearly intended, don't add new logic.
   DIFFERENTIATOR RULE: if you see a hand-drawn flowchart or diagram (not text
   code), you MUST still call extract_code_snippet and convert the flowchart's
   logic into clean structured pseudocode reflecting its actual branches/loops.

3. FLASHCARDS (call generate_flashcards) — generate flashcards that test real
   understanding, not trivial recall. Prefer "why/how/what happens if" style
   questions over simple "what is X" definitions.
   Good: "Why is a stack considered LIFO?"
   Avoid: "What is a stack?"
   Only generate flashcards for content that's substantive enough to warrant one
   — don't force flashcards out of thin material.

You may call one, two, or all three functions depending on what's actually present
on the board. Do not call a function for a content type that isn't present.
"""

    if explain_mode:
        instruction += """

=== EXPLAIN MODE IS ON ===
The student missed this lecture. Under every major heading in the markdown notes,
and inside every flashcard answer, add a short, beginner-friendly explanation
paragraph in plain, simple Bangla — as if teaching someone who has zero context
for this class. Avoid unnecessary jargon, keep it concise (2-4 sentences), but
preserve technical terms (e.g. "Stack", "LIFO", "O(n)") exactly rather than
translating them, since students need to recognize these terms later in exams
and other English-medium material.
"""

    instruction += """

=== HARD CONSTRAINTS (do not violate) ===
- Preserve Bangla exactly. Preserve English exactly. Preserve Banglish naturally.
- Never over-translate content that was intentionally mixed-language.
- Never fabricate lecture content, examples, or code that isn't evidenced by the
  board — reconstruction and formatting improvements are allowed, invention of new
  academic content is not.
- Only infer missing formatting/handwriting when confidence is high; otherwise use
  the Low Confidence blockquote format described above.
"""
    return instruction.strip()


# ---------------------------------------------------------------------------
# Main entry point (unchanged signature/return shape)
# ---------------------------------------------------------------------------
def process_whiteboard(image_bytes: bytes, explain_mode: bool) -> dict:
    """
    Sends the compressed image to the API with an intelligence-upgraded prompt
    that reconstructs the lecture rather than just transcribing text.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API key missing. Set GEMINI_API_KEY environment variable.")

    client = genai.Client(api_key=api_key)

    compressed_bytes = compress_image(image_bytes)
    image_part = types.Part.from_bytes(data=compressed_bytes, mime_type='image/jpeg')

    system_instruction = build_system_instruction(explain_mode)

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[image_part],
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=TOOLS,
            temperature=0.2,
            # Belt-and-suspenders: even though TOOLS are now schema-only
            # declarations (no real callables), explicitly disable AFC so a
            # future edit that reintroduces real functions can't silently
            # reintroduce this bug.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
    )

    results = {
        "notes": None,
        "code": None,
        "flashcards": None
    }

    if response.function_calls:
        for fc in response.function_calls:
            if fc.name == "generate_markdown_notes":
                results["notes"] = fc.args
            elif fc.name == "extract_code_snippet":
                results["code"] = fc.args
            elif fc.name == "generate_flashcards":
                results["flashcards"] = fc.args
    else:
        # Surface a real error instead of silently returning an empty dict —
        # this is what was making the UI look "processed but empty" with no
        # visible failure. Include the model's raw text (if any) to help debug.
        fallback_text = getattr(response, "text", None)
        raise RuntimeError(
            "Gemma did not return any function calls. "
            f"Raw model text (if any): {fallback_text!r}"
        )

    return results