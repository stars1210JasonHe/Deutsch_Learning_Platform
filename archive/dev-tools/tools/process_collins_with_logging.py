#!/usr/bin/env python3
"""
Enhanced Collins PDF processor with logging and error recovery
"""
import os
import sys
import subprocess
import json
import glob
from pathlib import Path
from datetime import datetime
import logging

def setup_logging():
    """Set up detailed logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"collins_processing_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return log_file

def load_progress():
    """Load processing progress from file"""
    progress_file = Path("collins_progress.json")
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                return json.load(f)
        except:
            return {"processed": [], "failed": [], "current": 0}
    return {"processed": [], "failed": [], "current": 0}

def save_progress(progress):
    """Save processing progress to file"""
    with open("collins_progress.json", 'w') as f:
        json.dump(progress, f, indent=2)

def main():
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    # Set up paths
    base_dir = Path(__file__).parent
    sources_output_dir = base_dir / "Sources" / "Output"
    processor_script = base_dir / "complete_collins_processor.py"
    
    logger.info(f"Starting Collins PDF processing")
    logger.info(f"Log file: {log_file}")
    
    # Check if directories exist
    if not sources_output_dir.exists():
        logger.error(f"Directory not found: {sources_output_dir}")
        return
    
    if not processor_script.exists():
        logger.error(f"Processor script not found: {processor_script}")
        return
    
    # Find all PDF files
    pdf_files = list(sources_output_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error(f"No PDF files found in {sources_output_dir}")
        return
    
    # Load progress
    progress = load_progress()
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    logger.info(f"Previously processed: {len(progress['processed'])}")
    logger.info(f"Previously failed: {len(progress['failed'])}")
    
    # Filter out already processed files
    pdf_files = sorted(pdf_files)
    remaining_files = []
    
    for pdf_file in pdf_files:
        if str(pdf_file) not in progress['processed']:
            remaining_files.append(pdf_file)
    
    logger.info(f"Remaining files to process: {len(remaining_files)}")
    
    if not remaining_files:
        logger.info("All files already processed!")
        return
    
    # Process each PDF file
    total_files = len(remaining_files)
    processed_this_run = 0
    failed_this_run = 0
    
    for i, pdf_file in enumerate(remaining_files, 1):
        logger.info(f"[{i}/{total_files}] Processing: {pdf_file.name}")
        
        try:
            # Set environment for Unicode handling
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Run the processor with enhanced error handling
            cmd = [
                sys.executable, 
                str(processor_script),
                str(pdf_file),
                "--max-chunks", "50",  # Reasonable chunk size
                "--chunk-size", "2000"  # Smaller chunks for better JSON parsing
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            
            # Run with timeout and capture output for logging
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=2400  # 40 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✓ Successfully processed: {pdf_file.name}")
                progress['processed'].append(str(pdf_file))
                processed_this_run += 1
                
                # Log some output
                if result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines[-10:]:  # Last 10 lines
                        if line.strip() and ('entries' in line.lower() or 'saved' in line.lower()):
                            logger.info(f"  Output: {line.strip()}")
            else:
                logger.error(f"✗ Failed to process: {pdf_file.name}")
                logger.error(f"Return code: {result.returncode}")
                
                # Log error details
                if result.stderr:
                    error_lines = result.stderr.split('\n')
                    for line in error_lines[-5:]:  # Last 5 error lines
                        if line.strip():
                            logger.error(f"  Error: {line.strip()}")
                
                progress['failed'].append({
                    "file": str(pdf_file),
                    "error": result.stderr[-500:] if result.stderr else "Unknown error",
                    "timestamp": datetime.now().isoformat()
                })
                failed_this_run += 1
            
            # Save progress after each file
            save_progress(progress)
            
        except subprocess.TimeoutExpired:
            logger.error(f"✗ Timeout processing: {pdf_file.name}")
            progress['failed'].append({
                "file": str(pdf_file),
                "error": "Timeout after 40 minutes",
                "timestamp": datetime.now().isoformat()
            })
            failed_this_run += 1
            save_progress(progress)
            
        except Exception as e:
            logger.error(f"✗ Exception processing {pdf_file.name}: {e}")
            progress['failed'].append({
                "file": str(pdf_file),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            failed_this_run += 1
            save_progress(progress)
        
        # Progress update
        total_processed = len(progress['processed'])
        total_failed = len(progress['failed'])
        remaining = len(pdf_files) - total_processed - total_failed
        
        logger.info(f"Progress: {total_processed} total processed, {total_failed} total failed, {remaining} remaining")
        logger.info("-" * 80)
    
    # Final summary
    logger.info(f"\n=== PROCESSING SESSION COMPLETE ===")
    logger.info(f"This session: {processed_this_run} processed, {failed_this_run} failed")
    logger.info(f"Total: {len(progress['processed'])} processed, {len(progress['failed'])} failed")
    logger.info(f"Success rate: {100 * len(progress['processed']) / len(pdf_files):.1f}%")
    
    # Show failed files for retry
    if progress['failed']:
        logger.info(f"\n=== FAILED FILES (for retry) ===")
        for failed in progress['failed'][-5:]:  # Show last 5 failures
            logger.info(f"Failed: {Path(failed['file']).name}")
            logger.info(f"  Error: {failed['error'][:100]}...")
            logger.info(f"  Time: {failed['timestamp']}")
    
    logger.info(f"\nTo retry failed files, run this script again.")
    logger.info(f"To start fresh, delete collins_progress.json")

if __name__ == "__main__":
    main()