import streamlit as st
import base64
import json
import io
from PIL import Image
from pdf2image import convert_from_bytes
from openai import OpenAI

# Initialize OpenAI client with your API key (replace with your key)
client = OpenAI(api_key="")

def image_to_base64(image: Image.Image) -> str:
    """
    Convert a PIL Image object to a Base64-encoded PNG.
    """
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")

def convert_to_png_and_encode(file) -> str:
    """
    Convert an uploaded image file (file-like object) to a Base64-encoded PNG.
    """
    image = Image.open(file)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")

def process_image(data_uri: str):
    """
    Call GPT (using your GPT-4o endpoint) to extract structured text from an image provided as a data URI.
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all the text off the Base64 encoding of the image in a structured way if it is present. Pay attention to any elements (tables for example) that have layouts and extract them as they are."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": data_uri},
                        },
                    ],
                }
            ],
            temperature=0,  # Deterministic output
        )
        structured_text = completion.choices[0].message.content
        return structured_text, completion
    except Exception as e:
        st.error(f"Error calling GPT: {e}")
        return None, None

def main():
    st.title("Structured Text Extraction from Image/PDF")
    st.write(
        "Upload an image or a PDF file. For PDFs, each page is converted to an image and processed separately. "
        "The extracted structured text from each page is then appended with a header (e.g., 'Page 1 of 3')."
    )

    # Allow PDF files along with common image formats.
    uploaded_file = st.file_uploader("Choose an image or PDF...", type=["png", "jpg", "jpeg", "bmp", "gif", "pdf"])

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()

        if file_extension == 'pdf':
            # Read the PDF as bytes and convert pages to images
            file_bytes = uploaded_file.read()
            pages = convert_from_bytes(file_bytes, dpi=300)
            responses = []
            total_pages = len(pages)

            st.write(f"PDF uploaded with {total_pages} page(s).")
            for i, page in enumerate(pages):
                st.image(page, caption=f"Page {i + 1}", use_column_width=True)
                # Convert the PIL image to Base64
                base64_image = image_to_base64(page)
                data_uri = f"data:image/png;base64,{base64_image}"

                with st.spinner(f"Extracting structured text from page {i + 1} of {total_pages}..."):
                    structured_text, completion = process_image(data_uri)
                if structured_text:
                    responses.append(f"Page {i + 1} of {total_pages}:\n{structured_text}\n")

            final_output = "\n".join(responses)
            st.subheader("Extracted Structured Text from PDF")
            st.text_area("Structured Text", final_output, height=300)

        else:
            # Process single image file
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
            base64_image = convert_to_png_and_encode(uploaded_file)
            data_uri = f"data:image/png;base64,{base64_image}"
            st.text_area("Base64 Encoded Image", data_uri, height=200)

            if st.button("Extract Structured Text"):
                with st.spinner("Calling GPT..."):
                    structured_text, completion = process_image(data_uri)
                if structured_text:
                    st.subheader("Extracted Structured Text")
                    st.text_area("Structured Text", structured_text, height=300)
                    st.subheader("Full GPT Response")
                    try:
                        full_response = json.dumps(completion, default=lambda o: o.__dict__, indent=2)
                    except Exception as ser_e:
                        full_response = str(completion)
                    st.text_area("GPT Response", full_response, height=300)
                    if hasattr(completion, "usage"):
                        st.write("Token Usage:", completion.usage)
                    elif isinstance(completion, dict) and "usage" in completion:
                        st.write("Token Usage:", completion["usage"])

if __name__ == '__main__':
    main()
