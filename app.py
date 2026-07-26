import streamlit as st
import os
from gemma_client import process_whiteboard

# ---------------------------------------------------------------------------
# UI Configuration (Minimal, low-literacy friendly)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Whiteboard Study Guide", page_icon="🎓", layout="centered")

# Basic CSS to make UI elements larger and clearer for mobile
st.markdown("""
<style>
    .big-font { font-size: 20px !important; font-weight: bold; }
    .error-text { color: #D32F2F; font-weight: bold; padding: 10px; border-left: 4px solid #D32F2F; background-color: #ffebee;}
</style>
""", unsafe_allow_html=True)

st.title("🎓 Whiteboard Scanner")
st.markdown("<p class='big-font'>Take a photo of the board</p>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Input Handling (Prioritize Camera, Fallback to File)
# ---------------------------------------------------------------------------
image_source = st.camera_input("Open Camera")
st.write("Or")
uploaded_file = st.file_uploader("Upload from gallery", type=["jpg", "jpeg", "png"])

# Determine final image bytes
final_image = None
if image_source:
    final_image = image_source.getvalue()
elif uploaded_file:
    final_image = uploaded_file.getvalue()

# ---------------------------------------------------------------------------
# Differentiator: Explain Mode Toggle
# ---------------------------------------------------------------------------
st.write("---")
explain_mode = st.toggle("I missed the class (Explain like I missed the class)", value=False)

# ---------------------------------------------------------------------------
# Processing and State Management
# ---------------------------------------------------------------------------
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

if final_image and st.button("Process Image", type="primary", use_container_width=True):
    with st.spinner("Processing, please wait..."):
        try:
            # Call the client module
            st.session_state.processed_data = process_whiteboard(final_image, explain_mode)
        except Exception as e:
            # Connectivity resilience: clear error message
            st.markdown(
                f"<div class='error-text'>Sorry, there was a connection issue. Please try again.<br><small>({str(e)})</small></div>",
                unsafe_allow_html=True
            )
            st.session_state.processed_data = None

# ---------------------------------------------------------------------------
# Result Rendering
# ---------------------------------------------------------------------------
if st.session_state.processed_data:
    data = st.session_state.processed_data
    st.write("---")

    # Clearly labeled tabs with icons
    tab1, tab2, tab3 = st.tabs(["Notes", "Code", "Flashcards"])

    # Compile markdown for the download button
    export_markdown = ""

    # Tab 1: Notes
    with tab1:
        if data["notes"]:
            notes = data["notes"]
            st.subheader(notes.get("title", "Class Notes"))
            st.markdown(notes.get("markdown_content", ""))

            export_markdown += f"# {notes.get('title', 'Class Notes')}\n\n"
            export_markdown += f"{notes.get('markdown_content', '')}\n\n---\n\n"
        else:
            st.info("No general notes detected.")

    # Tab 2: Code / Pseudocode
    with tab2:
        if data["code"]:
            code_data = data["code"]
            language = code_data.get("language", "text")
            snippet = code_data.get("code", "")

            st.subheader("Extracted Logic / Code")
            st.code(snippet, language=language.lower())

            export_markdown += f"## Code/Pseudocode ({language})\n\n```{language.lower()}\n{snippet}\n```\n\n---\n\n"
        else:
            st.info("No code or flowchart detected.")

    # Tab 3: Flashcards
    with tab3:
        if data["flashcards"] and "flashcards" in data["flashcards"]:
            st.subheader("Study Flashcards")
            cards = data["flashcards"]["flashcards"]
            for i, card in enumerate(cards):
                # Using expanders for a simple interactive flashcard feel
                with st.expander(f"**Q:** {card.get('question', '')}"):
                    st.write(f"**A:** {card.get('answer', '')}")

                export_markdown += f"**Q:** {card.get('question', '')}\n\n**A:** {card.get('answer', '')}\n\n"
        else:
            st.info("No flashcard material detected.")

    # Export functionality
    if export_markdown.strip():
        st.write("---")
        st.download_button(
            label="Save Notes (Download .md)",
            data=export_markdown,
            file_name="study_guide.md",
            mime="text/markdown",
            use_container_width=True
        )