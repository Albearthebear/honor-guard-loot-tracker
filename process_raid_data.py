import pandas as pd
import os
import glob

def process_raid_data(csv_dir='csv_output', output_dir='processed_data'):
    """
    Process raid data from CSV files:
    1. Extract participants (Player.1 and IGN.1) into separate CSV files
    2. Clean up redundant columns in the loot data
    3. Create a consolidated participants file
    4. Ensure class, spec, token, and role information is preserved
    
    Args:
        csv_dir (str): Directory containing the CSV files
        output_dir (str): Directory to save processed CSV files
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get all CSV files in the directory
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
    
    # List to store all participant dataframes
    all_participants = []
    
    for csv_file in csv_files:
        print(f"Processing file: {csv_file}")
        
        # Get the base filename without extension
        base_name = os.path.basename(csv_file).split('.')[0]
        
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Check if the file has participant data (Player.1 and IGN.1 columns)
            if 'Player.1' in df.columns and 'IGN.1' in df.columns:
                # Extract participant data with all related columns
                participant_columns = [col for col in df.columns if col.endswith('.1')]
                participants = df[participant_columns].copy()
                
                # Drop rows where both Player.1 and IGN.1 are empty
                participants = participants.dropna(subset=['Player.1', 'IGN.1'], how='all')
                
                # Ensure all required columns exist
                required_columns = ['Player.1', 'IGN.1', 'Class.1', 'Spec.1', 'Token.1', 'Role.1']
                for col in required_columns:
                    if col not in participants.columns:
                        participants[col] = ''
                
                # Add to the list of all participants
                all_participants.append(participants)
                
                # Save participants to a separate CSV file
                participants_file = os.path.join(output_dir, f"{base_name}_participants.csv")
                participants.to_csv(participants_file, index=False)
                print(f"Saved participants to: {participants_file}")
                
                # Create a mapping of IGN to participant data for later use
                participant_info = {}
                for _, row in participants.iterrows():
                    if pd.notna(row['IGN.1']):
                        participant_info[row['IGN.1']] = {
                            'Class': row.get('Class.1', ''),
                            'Spec': row.get('Spec.1', ''),
                            'Token': row.get('Token.1', ''),
                            'Role': row.get('Role.1', '')
                        }
                
                # Remove participant columns from the original data
                loot_data = df.drop(participant_columns, axis=1)
                
                # Drop rows where Item is NaN
                loot_data = loot_data.dropna(subset=['Item'])
                
                # Ensure all required columns exist in loot data
                required_loot_columns = ['IGN', 'Item', 'Class', 'Spec', 'Token', 'Role']
                for col in required_loot_columns:
                    if col not in loot_data.columns:
                        loot_data[col] = ''
                
                # For each loot entry, ensure class, spec, token, and role information is present
                for index, row in loot_data.iterrows():
                    if pd.notna(row['IGN']):
                        # Only update if the fields are empty or missing in the loot data
                        # and the player is in our participant info
                        if row['IGN'] in participant_info:
                            info = participant_info[row['IGN']]
                            
                            # Only update if the loot data field is empty
                            if pd.isna(loot_data.at[index, 'Class']) or loot_data.at[index, 'Class'] == '':
                                loot_data.at[index, 'Class'] = info['Class']
                            
                            if pd.isna(loot_data.at[index, 'Spec']) or loot_data.at[index, 'Spec'] == '':
                                loot_data.at[index, 'Spec'] = info['Spec']
                            
                            if pd.isna(loot_data.at[index, 'Token']) or loot_data.at[index, 'Token'] == '':
                                loot_data.at[index, 'Token'] = info['Token']
                            
                            if pd.isna(loot_data.at[index, 'Role']) or loot_data.at[index, 'Role'] == '':
                                loot_data.at[index, 'Role'] = info['Role']
                
                # Save cleaned loot data
                loot_file = os.path.join(output_dir, f"{base_name}_loot.csv")
                loot_data.to_csv(loot_file, index=False)
                print(f"Saved loot data to: {loot_file}")
            else:
                print(f"No participant data found in {csv_file}")
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    # Create consolidated participants file if we have any participants
    if all_participants:
        try:
            # Concatenate all participant dataframes
            consolidated = pd.concat(all_participants)
            
            # Rename columns to remove the .1 suffix
            column_mapping = {col: col.replace('.1', '') for col in consolidated.columns}
            consolidated = consolidated.rename(columns=column_mapping)
            
            # Ensure all required columns exist in consolidated data
            required_columns = ['Player', 'IGN', 'Class', 'Spec', 'Token', 'Role']
            for col in required_columns:
                if col not in consolidated.columns:
                    consolidated[col] = ''
                else:
                    # Fill NaN values with empty string
                    consolidated[col] = consolidated[col].fillna('')
            
            # Drop duplicates based on IGN (in-game name)
            consolidated = consolidated.drop_duplicates(subset=['IGN'])
            
            # Sort by IGN
            consolidated = consolidated.sort_values('IGN')
            
            # Save consolidated participants
            consolidated_file = os.path.join(output_dir, "all_participants.csv")
            consolidated.to_csv(consolidated_file, index=False)
            print(f"Saved consolidated participants to: {consolidated_file}")
        except Exception as e:
            print(f"Error creating consolidated participants file: {e}")

if __name__ == "__main__":
    process_raid_data()
    print("Processing complete!") 