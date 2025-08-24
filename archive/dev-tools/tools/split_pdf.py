#!/usr/bin/env python3
"""
PDF Splitter - Split large PDF files into smaller parts
Splits a PDF into multiple files with specified number of pages per file
Default: 50 pages per output file
"""
import argparse
import os
from pathlib import Path
try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    print("PyPDF2 not found. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "PyPDF2"], check=True)
    from PyPDF2 import PdfReader, PdfWriter


class PDFSplitter:
    """Split large PDF files into smaller parts"""
    
    def __init__(self, pages_per_file: int = 50):
        self.pages_per_file = pages_per_file
    
    def split_pdf(self, input_file: str, output_dir: str = None) -> list:
        """
        Split PDF into multiple files
        
        Args:
            input_file: Path to input PDF file
            output_dir: Directory for output files (default: same as input)
        
        Returns:
            List of created output files
        """
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not input_path.suffix.lower() == '.pdf':
            raise ValueError(f"Input file must be a PDF: {input_file}")
        
        # Set output directory
        if output_dir is None:
            output_dir = input_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read the input PDF
        print(f"Reading PDF: {input_file}")
        try:
            reader = PdfReader(input_file)
        except Exception as e:
            raise ValueError(f"Cannot read PDF file: {e}")
        
        total_pages = len(reader.pages)
        print(f"Total pages: {total_pages}")
        
        if total_pages <= self.pages_per_file:
            print(f"PDF has {total_pages} pages, which is less than {self.pages_per_file}. No splitting needed.")
            return [str(input_path)]
        
        # Calculate number of output files needed
        num_files = (total_pages + self.pages_per_file - 1) // self.pages_per_file
        print(f"Will create {num_files} output files with max {self.pages_per_file} pages each")
        
        output_files = []
        base_name = input_path.stem  # filename without extension
        
        # Split the PDF
        for file_num in range(num_files):
            start_page = file_num * self.pages_per_file
            end_page = min((file_num + 1) * self.pages_per_file, total_pages)
            
            # Create output filename
            output_filename = f"{base_name}_part{file_num + 1:02d}_pages{start_page + 1}-{end_page}.pdf"
            output_path = output_dir / output_filename
            
            # Create writer for this part
            writer = PdfWriter()
            
            # Add pages to writer
            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])
            
            # Write the output file
            try:
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                
                pages_in_file = end_page - start_page
                print(f"Created: {output_filename} ({pages_in_file} pages)")
                output_files.append(str(output_path))
                
            except Exception as e:
                print(f"Error creating {output_filename}: {e}")
                continue
        
        return output_files
    
    def get_pdf_info(self, pdf_file: str) -> dict:
        """Get basic information about a PDF file"""
        try:
            reader = PdfReader(pdf_file)
            return {
                'filename': Path(pdf_file).name,
                'total_pages': len(reader.pages),
                'file_size_mb': round(Path(pdf_file).stat().st_size / (1024 * 1024), 2),
                'splits_needed': (len(reader.pages) + self.pages_per_file - 1) // self.pages_per_file
            }
        except Exception as e:
            return {'error': str(e)}


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description='Split large PDF files into smaller parts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python split_pdf.py large_dictionary.pdf
  python split_pdf.py large_dictionary.pdf --pages 25
  python split_pdf.py large_dictionary.pdf --output-dir split_files
  python split_pdf.py large_dictionary.pdf --info
        """
    )
    
    parser.add_argument('input_file', help='Input PDF file to split')
    parser.add_argument(
        '--pages', '-p', 
        type=int, 
        default=50,
        help='Number of pages per output file (default: 50)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        help='Output directory for split files (default: same as input)'
    )
    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='Show PDF information only, do not split'
    )
    
    args = parser.parse_args()
    
    # Validate pages argument
    if args.pages < 1:
        print("Error: Pages per file must be at least 1")
        return
    
    # Initialize splitter
    splitter = PDFSplitter(pages_per_file=args.pages)
    
    # Show info only
    if args.info:
        info = splitter.get_pdf_info(args.input_file)
        if 'error' in info:
            print(f"Error reading PDF: {info['error']}")
            return
        
        print(f"\n=== PDF Information ===")
        print(f"File: {info['filename']}")
        print(f"Total pages: {info['total_pages']}")
        print(f"File size: {info['file_size_mb']} MB")
        print(f"Would create {info['splits_needed']} files with {args.pages} pages each")
        return
    
    # Split the PDF
    try:
        print(f"=== PDF Splitter ===")
        print(f"Input: {args.input_file}")
        print(f"Pages per file: {args.pages}")
        print(f"Output directory: {args.output_dir or 'same as input'}")
        print()
        
        output_files = splitter.split_pdf(args.input_file, args.output_dir)
        
        print(f"\n=== Split Complete ===")
        print(f"Created {len(output_files)} files:")
        for file in output_files:
            file_size = round(Path(file).stat().st_size / (1024 * 1024), 2)
            print(f"  - {Path(file).name} ({file_size} MB)")
        
        total_size = sum(Path(f).stat().st_size for f in output_files)
        print(f"\nTotal output size: {round(total_size / (1024 * 1024), 2)} MB")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()