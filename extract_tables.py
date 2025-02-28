import pandas as pd
import os

def excel_to_csv(excel_path, output_dir='csv_output'):
    """
    Convert each sheet of an Excel file to a CSV file.
    
    Args:
        excel_path (str): Path to the Excel file
        output_dir (str): Directory to save CSV files
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Processing Excel file: {excel_path}")
    
    # Get all sheet names
    excel = pd.ExcelFile(excel_path)
    
    # Process each sheet in the workbook
    for sheet_name in excel.sheet_names:
        print(f"Processing sheet: {sheet_name}")
        
        # Read the sheet with pandas
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Clean up the data
        # Drop rows and columns where all values are NA
        df = df.dropna(how='all')
        df = df.dropna(axis=1, how='all')
        
        # Create a clean filename
        clean_sheet_name = "".join(c if c.isalnum() else "_" for c in sheet_name)
        csv_filename = f"{clean_sheet_name}.csv"
        csv_path = os.path.join(output_dir, csv_filename)
        
        # Save as CSV
        df.to_csv(csv_path, index=False)
        print(f"Saved {csv_path}")

if __name__ == "__main__":
    excel_file = "Honor Guard Dragon Soul loot tracker(1).xlsx"
    excel_to_csv(excel_file)
    print("Conversion complete!") 