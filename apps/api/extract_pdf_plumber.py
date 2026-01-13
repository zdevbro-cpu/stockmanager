import pdfplumber

pdf_path = r'c:\ProjectCode\stockmanager\docs\vc투자메모.pdf'
with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}\n")
    for i, page in enumerate(pdf.pages):
        print(f"\n{'='*80}")
        print(f"PAGE {i+1}")
        print(f"{'='*80}")
        text = page.extract_text()
        if text:
            print(text)
        else:
            print("[No text found - image-based page]")
