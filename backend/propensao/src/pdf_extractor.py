"""
PDF to Markdown converter for extracting quarterly financial data.
"""

import fitz  # pymupdf
from pathlib import Path
import re


def extract_pdf_to_markdown(pdf_path: Path, output_path: Path) -> str:
    """
    Extract text from PDF and convert to markdown.
    
    Args:
        pdf_path: Path to PDF file
        output_path: Path to save markdown
        
    Returns:
        Extracted text
    """
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    
    text_content = []
    text_content.append(f"# {pdf_path.stem}\n")
    text_content.append(f"*Extração automática do arquivo: {pdf_path.name}*\n")
    text_content.append("---\n")
    
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        
        # Clean up text
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        text_content.append(f"\n## Página {page_num}\n")
        text_content.append(text)
    
    doc.close()
    
    full_text = '\n'.join(text_content)
    
    # Save to markdown
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    print(f"Extracted {num_pages} pages to {output_path}")
    return full_text


def main():
    docs_dir = Path(__file__).parent.parent / "docs"
    
    pdfs = [
        "Informações Trimestrais 1T2025.pdf",
        "Informações Trimestrais 2T2025.pdf",
        "Informações Trimestrais 3T2025.pdf",
        "Dados Econômico-Financeiros Intermediários - 1S2025.pdf"
    ]
    
    for pdf_name in pdfs:
        pdf_path = docs_dir / pdf_name
        if pdf_path.exists():
            md_name = pdf_name.replace('.pdf', '.md')
            output_path = docs_dir / md_name
            
            print(f"Processing: {pdf_name}")
            extract_pdf_to_markdown(pdf_path, output_path)
        else:
            print(f"Not found: {pdf_path}")


if __name__ == "__main__":
    main()
