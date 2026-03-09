import os
import tempfile
from pathlib import Path
import pandas as pd
import streamlit as st
from hallucinator import PdfExtractor, Validator, ValidatorConfig

logo_path = Path(__file__).with_name("Logo_SSL_Colored.png")

st.set_page_config(
    page_title="Reference Checker",
    page_icon=str(logo_path) if logo_path.exists() else None,
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 1.4rem;
        }
        .app-hero {
            background: linear-gradient(120deg, #f8fafc 0%, #eef2ff 100%);
            border: 1px solid #dbe4ff;
            border-radius: 12px;
            padding: 0.9rem 1rem;
            margin-bottom: 1rem;
        }
        .app-hero h1 {
            margin: 0;
            font-size: 1.6rem;
            line-height: 1.2;
        }
        .app-hero p {
            margin: 0.4rem 0 0 0;
            color: #374151;
            font-size: 0.95rem;
        }
        [data-testid="stSidebar"] img {
            max-width: 72px !important;
            margin: 0.25rem auto 0.5rem auto;
            display: block;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="app-hero">
        <h1>Reference Checker</h1>
        <p>Upload an academic PDF and validate whether extracted references exist in scholarly databases.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar
st.sidebar.header("About")
if logo_path.exists():
    st.sidebar.image(str(logo_path), width=72)
st.sidebar.write(
    "This app uses Hallucinator to extract references from PDFs and validate them. "
    "It is developed by the System Security Lab at TU Darmstadt and intended for internal use."
)
st.sidebar.markdown(
    "[Hallucinator GitHub Repository](https://github.com/gianlucasb/hallucinator)"
)

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

@st.cache_resource
def get_extractor():
    return PdfExtractor()

@st.cache_resource
def get_validator():
    config = ValidatorConfig()
    return Validator(config)

def safe_get(obj, name, default=None):
    return getattr(obj, name, default)

if uploaded_file is not None:
    st.info(f"Uploaded file: {uploaded_file.name}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        extractor = get_extractor()
        validator = get_validator()

        with st.spinner("Extracting references..."):
            extraction_result = extractor.extract(tmp_path)

        references = extraction_result.references

        st.subheader("Extraction Summary")
        st.write(f"Number of extracted references: **{len(references)}**")

        if len(references) == 0:
            st.warning("No references were extracted from this PDF.")
        else:
            with st.spinner("Checking references against databases..."):
                results = validator.check(references)

            rows = []
            for i, result in enumerate(results, start=1):
                rows.append(
                    {
                        "Reference #": i,
                        "Status": safe_get(result, "status", "UNKNOWN"),
                        "Title": safe_get(result, "title", ""),
                    }
                )

            df = pd.DataFrame(rows)

            st.subheader("Results")
            st.dataframe(df, use_container_width=True)

            st.subheader("Result Counts")
            counts = df["Status"].value_counts()
            st.bar_chart(counts)

            with st.expander("Show extracted references"):
                extracted_rows = []
                for ref in references:
                    extracted_rows.append(
                        {
                            "Title": safe_get(ref, "title", ""),
                            "Authors": ", ".join(safe_get(ref, "authors", []) or []),
                            "DOI": safe_get(ref, "doi", ""),
                            "arXiv ID": safe_get(ref, "arxiv_id", ""),
                            "Raw citation": safe_get(ref, "raw_citation", ""),
                        }
                    )
                st.dataframe(pd.DataFrame(extracted_rows), use_container_width=True)

    except Exception as e:
        st.error(f"Failed to process the PDF: {e}")

    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
else:
    st.caption("Upload a PDF to begin.")
