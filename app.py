import streamlit as st
import arxiv
import PyPDF2
import io
import requests
import re
from sympy import symbols, sympify, lambdify
import matplotlib.pyplot as plt
import numpy as np
import os
import ollama
import json
from streamlit_pdf_viewer import pdf_viewer

st.set_page_config(layout="wide")
st.title("arXiv Paper Analyzer")

# Function to get cache directory
def get_cache_dir():
    cache_dir = "paper_cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir

# Function to get paper path from cache
def get_paper_path(paper_id):
    cache_dir = get_cache_dir()
    return os.path.join(cache_dir, f"{paper_id}.pdf")

# Function to clean arXiv ID
def clean_arxiv_id(arxiv_id):
    # Remove .pdf extension if present
    arxiv_id = arxiv_id.replace('.pdf', '')
    # Remove any URL parts
    if 'arxiv.org' in arxiv_id:
        arxiv_id = arxiv_id.split('/')[-1]
    return arxiv_id

# Function to extract equations from PDF
def extract_equations(pdf_content):
    equations = []
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    for page in pdf_reader.pages:
        text = page.extract_text()
        # Look for equations between $...$ or \[...\]
        inline_eqs = re.findall(r'\$(.*?)\$', text)
        display_eqs = re.findall(r'\\\[(.*?)\\\]', text)
        # Also look for equation environments
        equation_envs = re.findall(r'\\begin{equation}(.*?)\\end{equation}', text, re.DOTALL)
        align_envs = re.findall(r'\\begin{align}(.*?)\\end{align}', text, re.DOTALL)
        # Look for other math environments
        gather_envs = re.findall(r'\\begin{gather}(.*?)\\end{gather}', text, re.DOTALL)
        multline_envs = re.findall(r'\\begin{multline}(.*?)\\end{multline}', text, re.DOTALL)
        equations.extend(inline_eqs + display_eqs + equation_envs + align_envs + gather_envs + multline_envs)
    return equations

# Function to analyze equations with Ollama
def analyze_equations_with_ollama(equations):
    if not equations:
        return []
    
    analysis_results = []
    for eq in equations:
        prompt = f"""
        Analyze this mathematical equation and provide:
        1. A clear explanation of what the equation represents
        2. Python code to implement and plot this equation
        3. Key parameters and their meanings
        
        Equation: {eq}
        
        Respond in JSON format with these keys:
        - explanation
        - python_code
        - parameters
        """
        
        try:
            response = ollama.generate(model='deepseek-r1:1.5b', prompt=prompt)
            print("Raw Ollama Response:", response['response'])  # Print raw response
            result = json.loads(response['response'])
            analysis_results.append({
                'equation': eq,
                'analysis': result,
                'raw_response': response['response']
            })
        except Exception as e:
            print("Error:", str(e))  # Print error
            analysis_results.append({
                'equation': eq,
                'analysis': {
                    'error': str(e),
                    'explanation': 'Could not analyze equation',
                    'python_code': '',
                    'parameters': {}
                },
                'raw_response': str(e)
            })
    
    return analysis_results

# Main app layout
st.header("PDF Viewer")
arxiv_url = st.text_input("Enter arXiv URL or paper ID (e.g., 2504.02828 or https://arxiv.org/abs/2504.02828):")

if arxiv_url:
    try:
        # Clean the arXiv ID
        paper_id = clean_arxiv_id(arxiv_url)
        st.write(f"Processing paper: {paper_id}")
        
        # Check if paper exists in cache
        paper_path = get_paper_path(paper_id)
        if os.path.exists(paper_path):
            st.write("Loading paper from cache...")
            with open(paper_path, "rb") as f:
                pdf_content = f.read()
        else:
            st.write("Downloading paper...")
            # Download the paper
            paper = next(arxiv.Search(id_list=[paper_id]).results())
            pdf_url = paper.pdf_url
            response = requests.get(pdf_url)
            pdf_content = response.content
            
            # Save to cache
            with open(paper_path, "wb") as f:
                f.write(pdf_content)
        
        # Create two columns for PDF and equations
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.header("PDF Viewer")
            # Save PDF temporarily
            with open("temp.pdf", "wb") as f:
                f.write(pdf_content)
            
            # Display PDF using the viewer with scrollbar
            st.markdown("""
                <style>
                .pdf-container {
                    height: 800px;
                    overflow-y: scroll;
                    border: 1px solid #ccc;
                    padding: 10px;
                }
                </style>
                <div class="pdf-container">
            """, unsafe_allow_html=True)
            
            pdf_viewer("temp.pdf", width=700)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.download_button(
                label="Download PDF",
                data=pdf_content,
                file_name=f"{paper_id}.pdf",
                mime="application/pdf"
            )
        
        with col2:
            st.header("Equations and Analysis")
            equations = extract_equations(pdf_content)
            
            if not equations:
                st.write("No equations found in the paper. Analyzing with Ollama...")
                # Extract text from PDF for analysis
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                # Analyze with Ollama
                prompt = f"""
                Analyze this research paper and identify:
                1. Key mathematical equations or formulas
                2. Their explanations
                3. Python code to implement them
                
                Paper text: {text[:2000]}  # First 2000 characters for analysis
                
                Respond in JSON format with these keys:
                - equations (list of equations found)
                - explanations (list of explanations)
                - python_codes (list of Python implementations)
                """
                
                try:
                    print(text[:2000])
                    response = ollama.generate(model='deepseek-r1:1.5b', prompt=prompt)
                    print("Raw Ollama Response:", response['response'])  # Print raw response
                    analysis = json.loads(response['response'])
                    
                    # Show raw response
                    with st.expander("Raw Ollama Response"):
                        st.code(response['response'], language='json')
                    
                    for i, (eq, expl, code) in enumerate(zip(analysis['equations'], 
                                                           analysis['explanations'], 
                                                           analysis['python_codes'])):
                        with st.expander(f"Equation {i+1}: {eq}"):
                            st.write("Explanation:", expl)
                            st.code(code, language='python')
                            
                            # Try to execute and plot the code
                            try:
                                exec(code)
                                st.pyplot(plt.gcf())
                            except Exception as e:
                                st.write(f"Could not plot equation: {str(e)}")
                except Exception as e:
                    st.error(f"Error analyzing paper: {str(e)}")
            else:
                st.write(f"Found {len(equations)} equations in the paper.")
                analysis_results = analyze_equations_with_ollama(equations)
                
                for i, result in enumerate(analysis_results):
                    with st.expander(f"Equation {i+1}: {result['equation']}"):
                        # Show raw response
                        with st.expander("Raw Ollama Response"):
                            st.code(result['raw_response'], language='json')
                        
                        st.write("Explanation:", result['analysis']['explanation'])
                        st.write("Parameters:", result['analysis']['parameters'])
                        st.code(result['analysis']['python_code'], language='python')
                        
                        # Try to execute and plot the code
                        try:
                            exec(result['analysis']['python_code'])
                            st.pyplot(plt.gcf())
                        except Exception as e:
                            st.write(f"Could not plot equation: {str(e)}")
    
    except Exception as e:
        st.error(f"Error: {str(e)}") 