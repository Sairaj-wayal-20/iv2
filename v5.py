from dotenv import load_dotenv
import streamlit as st
import os
from PIL import Image
import pdf2image
from PyPDF2 import PdfReader
import google.generativeai as genai
from io import BytesIO

# Load environment variables
load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load OpenAI model and get responses
def get_gemini_response(input, images, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input, *images, prompt])
    return response.text

# Function to set up image input
def input_image_setup(uploaded_files):
    image_parts = []
    for uploaded_file in uploaded_files:
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            image_parts.append({"mime_type": uploaded_file.type, "data": bytes_data})
        else:
            raise FileNotFoundError("No file uploaded")
    return image_parts

# Function to convert PDF to images and extract text
def process_pdf(uploaded_files):
    pdf_text = ""
    image_parts = []
    for uploaded_file in uploaded_files:
        pdf_images = pdf2image.convert_from_bytes(uploaded_file.getvalue())
        pdf_reader = PdfReader(uploaded_file)

        for page in pdf_reader.pages:
            pdf_text += page.extract_text()

        for image in pdf_images:
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            image_parts.append({"mime_type": "image/png", "data": buffered.getvalue()})

    return pdf_text, image_parts

# Initialize Streamlit app
st.set_page_config(page_title="Gemini Image and PDF Demo")
st.header("Gemini Application")

input_text = st.text_input("Input Prompt: ", key="input")
uploaded_files = st.file_uploader("Choose images or PDFs...", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

images = []
pdf_text = ""

if uploaded_files:
    file_types = [uploaded_file.type for uploaded_file in uploaded_files]
    if any("image" in file_type for file_type in file_types):
        images = [Image.open(uploaded_file) for uploaded_file in uploaded_files if "image" in uploaded_file.type]
        for image in images:
            st.image(image, caption="Uploaded Image.", use_column_width=True)
    if any("pdf" in file_type for file_type in file_types):
        pdf_files = [uploaded_file for uploaded_file in uploaded_files if "pdf" in uploaded_file.type]
        pdf_text, pdf_images = process_pdf(pdf_files)
        st.write("PDF Text Extracted:", pdf_text[:500], "...")  # Display first 500 characters
        images.extend(pdf_images)

submit = st.button("Extract Information")

input_prompt = """
               You are an expert in understanding invoices.
               You will receive input images as invoices &
               you will have to answer questions based on the input image.
               """

# If submit button is clicked
if submit:
    if images:
        response = get_gemini_response(input_prompt, images, input_text + "\n" + pdf_text)
        st.subheader("The Response is")
        st.write(response, save_as_pdf=True)
