# arXiv Paper Analyzer

This Streamlit app allows you to analyze arXiv papers by:
1. Viewing and downloading the PDF
2. Extracting equations from the paper
3. Converting equations to Python code
4. Generating plots of the equations

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. Enter an arXiv URL or paper ID in the input field. For example:
   - Full URL: https://arxiv.org/abs/2103.00001
   - Paper ID: 2103.00001

4. The app will:
   - Display a download button for the PDF
   - Show extracted equations on the right side
   - Convert equations to Python code
   - Generate and display plots of the equations

## Features

- PDF viewer and downloader
- Equation extraction from PDFs
- LaTeX to Python code conversion
- Automatic plot generation
- Interactive equation exploration

## Note

Some equations might not be convertible to Python code or plottable due to their complexity or the limitations of the conversion tools.
