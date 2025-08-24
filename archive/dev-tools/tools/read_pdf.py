#!/usr/bin/env python3
"""
Simple PDF Reader Script
Reads text content from PDF files using PyPDF2
"""
import sys
import os
from typing import Optional

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not found. Install with: uv add pypdf2")
    sys.exit(1)


def read_pdf(pdf_path: str) -> Optional[str]:
    """
    Read text from a PDF file
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content or None if failed
    """
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return None
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            print(f"Reading PDF with {len(pdf_reader.pages)} pages...")
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num + 1} ---\n"
                    text += page_text + "\n"
                    
                    if page_num % 5 == 0:
                        print(f"   Processed page {page_num + 1}...")
                        
                except Exception as e:
                    print(f"   Error reading page {page_num + 1}: {e}")
                    continue
            
            return text.strip()
            
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Read text from PDF file')
    parser.add_argument('pdf_file', help='Path to PDF file')
    parser.add_argument('-o', '--output', help='Save text to file (optional)')
    parser.add_argument('--pages', type=int, help='Limit number of pages to read')
    
    args = parser.parse_args()
    
    print("PDF Reader")
    print("=" * 30)
    
    # Read PDF
    text = read_pdf(args.pdf_file)
    
    if not text:
        print("Failed to extract text from PDF")
        return
    
    # Limit pages if requested
    if args.pages:
        lines = text.split('\n')
        page_lines = []
        page_count = 0
        
        for line in lines:
            if line.startswith('--- Page '):
                page_count += 1
                if page_count > args.pages:
                    break
            page_lines.append(line)
        
        text = '\n'.join(page_lines)
    
    # Output results
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Text saved to: {args.output}")
        except Exception as e:
            print(f"Error saving file: {e}")
    else:
        print(f"\nExtracted Text:")
        print("=" * 50)
        print(text)
        print("=" * 50)
        print(f"Total characters: {len(text)}")


if __name__ == "__main__":
    main()