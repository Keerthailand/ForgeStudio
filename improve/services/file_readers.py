import os

def extract_text_from_upload(uploaded_file):
    """
    Returns: (text, note)
    note is included to inform the user about limitations.
    """
    name = uploaded_file.name.lower()

    if name.endswith(".txt"):
        text = uploaded_file.read().decode("utf-8", errors="ignore")
        return text.strip(), "Loaded text from .txt file."

    if name.endswith(".docx"):
        # Optional dependency: python-docx
        try:
            import docx  # python-docx package
            doc = docx.Document(uploaded_file)
            text = "\n".join([p.text for p in doc.paragraphs]).strip()
            if not text:
                return "", "DOCX uploaded, but no readable text found."
            return text, "Loaded text from .docx file."
        except Exception:
            return "", "DOCX uploaded, but DOCX parsing isn't available. Paste the text for best results."

    if name.endswith(".pdf"):
        # PDF parsing is non-trivial without extra deps; don’t pretend.
        return "", "PDF uploaded. For best results, paste the text you want improved (PDF parsing not enabled yet)."

    return "", "File uploaded, but that type isn’t supported yet. Use .txt, .docx, or paste text."
