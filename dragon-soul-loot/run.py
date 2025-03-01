#!/usr/bin/env python3
"""
Run script for Dragon Soul Loot Manager

This script runs the FastAPI application with uvicorn.
"""

import os
import sys
import uvicorn
import argparse

def main():
    """Main function to run the application"""
    parser = argparse.ArgumentParser(description="Run the Dragon Soul Loot Manager application")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--process-data", action="store_true", help="Process CSV data before starting")
    
    args = parser.parse_args()
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Process data if requested
    if args.process_data:
        print("Processing CSV data...")
        try:
            from app.process_data import main as process_data_main
            process_data_main()
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            sys.exit(1)
    
    # Run the application
    print(f"Starting Dragon Soul Loot Manager on http://{args.host}:{args.port}")
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main() 