import PyPDF2
import sys

pdf_path = 'docs/vc투자메모.pdf'
try:
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        print(f"Total pages: {len(reader.pages)}\n")
        
        for i, page in enumerate(reader.pages):
            print(f"\n{'='*80}")
            print(f"PAGE {i+1}")
            print(f"{'='*80}")
            text = page.extract_text()
            print(text)
            print("\n")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
