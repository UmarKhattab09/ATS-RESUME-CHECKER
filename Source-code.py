import streamlit as st
import base64
import os
import io
from PIL import Image
import pdf2image
import google.generativeai as genai

# Load API Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input_prompt, pdf_content, job_desc):
    """Generate AI response using Google Gemini API safely."""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content([input_prompt, pdf_content[0], job_desc])

        # Debugging: Print the response to check its structure
        print("API Response:", response)

        # Check if the response is a tuple or complex object
        if isinstance(response, tuple):
            print("Response is a tuple. First item:", response[0])
            return response[0] if response else "Error: No content in response."
        
        # Assuming 'response' has a 'text' attribute
        elif hasattr(response, "text") and response.text:
            return response.text
        else:
            return "Error: No valid response received from AI."

    except Exception as e:
        return f"Error: {str(e)}"

def input_pdf_setup(uploaded_file):
    """ Convert PDF to image and encode as base64 with error handling """
    if uploaded_file is not None:
        if uploaded_file.size == 0:
            st.error("Error: The uploaded PDF is empty. Please upload a valid file.")
            return None

        try:
            # Convert PDF to image
            images = pdf2image.convert_from_bytes(uploaded_file.read())

            if len(images) > 0:
                first_page = images[0]
                img_byte_arr = io.BytesIO()
                first_page.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()

                pdf_parts = [{
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(img_byte_arr).decode()
                }]
                st.success("PDF Uploaded Successfully!")
                return pdf_parts
            else:
                st.error("PDF has no pages. Please upload a valid PDF with content.")
                return None

        except pdf2image.exceptions.PDFPageCountError:
            st.error("Error: Unable to read the PDF. It might be empty or corrupted.")
            return None
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            return None
    else:
        st.warning("Please upload a PDF file.")
        return None

# Store job list in session state
if "job_list" not in st.session_state:
    st.session_state.job_list = []


# Predefined prompts
input_prompt1 = """
You are an experienced Technical Human Resource Manager. Review the provided resume against the job description. 
Evaluate whether the candidate's profile aligns with the role. Highlight strengths and weaknesses.
"""

input_prompt3 = """
You are an ATS (Applicant Tracking System) scanner with expertise in data science. Evaluate the resume against the job description.
Provide a match percentage, missing keywords, and final thoughts.
"""

input_prompt4 = """
Provide a match percentage based on the job description. And provide list of keywords that matches. only few lines answer
"""
def main():
    st.subheader("AI Powered Resume Checker")

    # Navigation sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select a section:", ["Home", "Students","Recruiters"])
    
    if page == "Recruiters":
        st.sidebar.subheader("Recruiter Portal")
        job_desc = st.sidebar.text_area("Enter Job Description for Matching:")
        matched_results = []
        if st.sidebar.button("Find Matches") and job_desc:
            matched_results = []
            for candidate in st.session_state.job_list:
                response = get_gemini_response(input_prompt4, candidate["pdf_content"], job_desc)
                matched_results.append({
                "name": candidate["name"],
                "job": candidate["job"],
                "match_score": response
            })
        st.sidebar.subheader("Matching Candidates:")
        for result in matched_results:
            st.sidebar.write(f"**{result['name']} - {result['job']}**: {result['match_score']}")


    if page == "Home":
        st.subheader("Resume")
        st.write("Explore the sections from the sidebar.")

    elif page == "Students":
        st.subheader("Resume Evaluation")
        name = st.text_input("Enter Your Name:")
        job = st.text_input("What Job You Are Applying To:")
        stage = st.radio("Select Your Stage:", ['Applied', 'Interview', 'Accepted', 'Rejected'])
        uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])
        job_desc = st.text_area("Enter Job Description:", key="input")

        # Process PDF
        pdf_content = input_pdf_setup(uploaded_file) if uploaded_file else None

        # AI Resume Evaluation
        col1, col2 = st.columns(2)
        with col1:
            submit1 = st.button("Analyze Resume")
        with col2:
            submit3 = st.button("Check Match Percentage")

        if submit1 and pdf_content:
            if job_desc:
                response = get_gemini_response(input_prompt1, pdf_content, job_desc)
                st.subheader("Evaluation Response:")
                st.write(response)
            else:
                st.warning("Please enter the job description.")

        if submit3 and pdf_content:
            if job_desc:
                response = get_gemini_response(input_prompt3, pdf_content, job_desc)
                st.subheader("Match Percentage Response:")
                st.write(response)
            else:
                st.warning("Please enter the job description.")

        # Job Tracking System
        if st.button("Add to Sidebar") and name and job and pdf_content:
            st.session_state.job_list.append({
                "name":name,
                "job":job,
                "stage":stage,
                "pdf_content":pdf_content
            })
            st.success(f"{name}'s application for {job} added!")



        if st.session_state.job_list:
            st.sidebar.subheader("Tracked Jobs")
            selected_job = st.sidebar.selectbox(
                "Select a job to update or delete:", 
                [f"{job['name']} - {job['job']} ({job['stage']})" for job in st.session_state.job_list]
            )
            selected_job_dict = next(job for job in st.session_state.job_list if f"{job['name']} - {job['job']} ({job['stage']})" == selected_job)
            # Updating Job Entry
            new_name = st.sidebar.text_input("Update Name:", selected_job_dict["name"])
            new_job = st.sidebar.text_input("Update Job Title:", selected_job_dict["job"])
            new_stage = st.sidebar.radio("Update Stage:", ['Applied', 'Interview', 'Accepted', 'Rejected'], 
                                 index=['Applied', 'Interview', 'Accepted', 'Rejected'].index(selected_job_dict["stage"]))

        
            if st.sidebar.button("Update Job"):
                selected_job_dict.update({"name": new_name, "job": new_job, "stage": new_stage})
                st.rerun()

             # Deleting Job Entry
            if st.sidebar.button("Delete Job"):
                st.session_state.job_list.remove(selected_job_dict)
                st.rerun()
if __name__ == "__main__":
    main()