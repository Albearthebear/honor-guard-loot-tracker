#!/usr/bin/env python3
"""
Data Processing Script for Dragon Soul Loot Manager

This script processes CSV data files and generates JSON data files for the application.
"""

import os
import sys
from data_processor import DataProcessor

def main():
    """Main function to process data"""
    print("Starting data processing...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set paths relative to the script directory
    data_dir = os.path.join(script_dir, "..", "data")
    processed_data_dir = os.path.join(script_dir, "..", "processed_data")
    
    # Ensure directories exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Check if processed_data directory exists
    if not os.path.exists(processed_data_dir):
        print(f"Error: Processed data directory not found at {processed_data_dir}")
        print("Please ensure the directory exists and contains CSV files.")
        sys.exit(1)
    
    # Check if CSV files exist
    csv_files = [f for f in os.listdir(processed_data_dir) if f.endswith('.csv')]
    if not csv_files:
        print(f"Error: No CSV files found in {processed_data_dir}")
        print("Please ensure the directory contains CSV files.")
        sys.exit(1)
    
    print(f"Found {len(csv_files)} CSV files to process.")
    
    # Initialize and run data processor
    processor = DataProcessor(data_dir=data_dir, processed_data_dir=processed_data_dir)
    
    try:
        processor.process_all_data()
        print("Data processing completed successfully.")
        print(f"Generated JSON files in {data_dir}:")
        for json_file in [f for f in os.listdir(data_dir) if f.endswith('.json')]:
            file_path = os.path.join(data_dir, json_file)
            file_size = os.path.getsize(file_path) / 1024  # Size in KB
            print(f"  - {json_file} ({file_size:.2f} KB)")
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 