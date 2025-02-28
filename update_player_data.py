import pandas as pd
import os
import glob

# Define player information mapping
PLAYER_INFO = {
    'Andrewd': {'class': 'Druid', 'spec': 'Restoration', 'role': 'Healer', 'token': 'Vanquisher'},
    'Corwor': {'class': 'Warlock', 'spec': 'Demonology', 'role': 'DPS', 'token': 'Conqueror'},
    'Ifbbathlete': {'class': 'Priest', 'spec': 'Discipline', 'role': 'Healer', 'token': 'Conqueror'},
    'Pepsícola': {'class': 'Warrior', 'spec': 'Arms', 'role': 'DPS', 'token': 'Protector'},
    'Rewolut': {'class': 'Rogue', 'spec': 'Combat', 'role': 'DPS', 'token': 'Vanquisher'},
    'Ricardomìlos': {'class': 'Warrior', 'spec': 'Arms', 'role': 'DPS', 'token': 'Protector'},
    'Rùskøv': {'class': 'Druid', 'spec': 'Feral', 'role': 'DPS', 'token': 'Vanquisher'},
    'Sowzz': {'class': 'Hunter', 'spec': 'Survival', 'role': 'DPS', 'token': 'Protector'},
    'albear': {'class': 'Druid', 'spec': 'Feral', 'role': 'Offtank', 'token': 'Vanquisher'},
    'bestdk': {'class': 'DK', 'spec': 'Frost', 'role': 'DPS', 'token': 'Vanquisher'},
    'borran': {'class': 'Shaman', 'spec': 'Elemental', 'role': 'DPS', 'token': 'Protector'},
    'copro': {'class': 'Mage', 'spec': 'Fire', 'role': 'DPS', 'token': 'Vanquisher'},
    'dankovich': {'class': 'Priest', 'spec': 'Discipline', 'role': 'Healer', 'token': 'Conqueror'},
    'delusive': {'class': 'Rogue', 'spec': 'Combat', 'role': 'DPS', 'token': 'Vanquisher'},
    'dreamypie': {'class': 'Paladin', 'spec': 'Holy', 'role': 'Healer', 'token': 'Conqueror'},
    'falkeblikk': {'class': 'Hunter', 'spec': 'Survival', 'role': 'DPS', 'token': 'Protector'},
    'imlegalqt': {'class': 'Shaman', 'spec': 'Enhancement', 'role': 'DPS', 'token': 'Protector'},
    'jayli': {'class': 'Mage', 'spec': 'Fire', 'role': 'DPS', 'token': 'Vanquisher'},
    'milka': {'class': 'Priest', 'spec': 'Shadow', 'role': 'DPS', 'token': 'Conqueror'},
    'moruse': {'class': 'Druid', 'spec': 'Balance', 'role': 'DPS', 'token': 'Vanquisher'},
    'nicegaff': {'class': 'Paladin', 'spec': 'Holy', 'role': 'Healer', 'token': 'Conqueror'},
    'overdeath': {'class': 'DK', 'spec': 'Blood', 'role': 'Main Tank', 'token': 'Vanquisher'},
    'ricardo': {'class': 'Warrior', 'spec': 'Arms', 'role': 'DPS', 'token': 'Protector'},
    'sanddiglett': {'class': 'Paladin', 'spec': 'Retribution', 'role': 'DPS', 'token': 'Conqueror'},
    'saokipriest': {'class': 'Priest', 'spec': 'Discipline', 'role': 'Healer', 'token': 'Conqueror'},
    'vallock': {'class': 'Warlock', 'spec': 'Affliction', 'role': 'DPS', 'token': 'Conqueror'},
    'woopstab': {'class': 'Rogue', 'spec': 'Combat', 'role': 'DPS', 'token': 'Vanquisher'},
    'Ðelusive': {'class': 'Rogue', 'spec': 'Combat', 'role': 'DPS', 'token': 'Vanquisher'},  # Special character version
}

def update_csv_files(csv_dir='csv_output'):
    """
    Update CSV files with additional player information:
    1. Add 'guildie' to participants without a player name
    2. Add class, spec, token type, and role columns
    
    Args:
        csv_dir (str): Directory containing the CSV files
    """
    # Get all CSV files in the directory
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
    
    for csv_file in csv_files:
        print(f"Processing file: {csv_file}")
        
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        # Check if this is a file with participant data
        if 'Player.1' in df.columns and 'IGN.1' in df.columns:
            # Add 'guildie' to participants without a player name
            df['Player.1'] = df['Player.1'].fillna('guildie')
            
            # Add new columns for class, spec, token, and role
            df['Class.1'] = df['IGN.1'].map(lambda ign: PLAYER_INFO.get(ign, {}).get('class', ''))
            df['Spec.1'] = df['IGN.1'].map(lambda ign: PLAYER_INFO.get(ign, {}).get('spec', ''))
            df['Token.1'] = df['IGN.1'].map(lambda ign: PLAYER_INFO.get(ign, {}).get('token', ''))
            df['Role.1'] = df['IGN.1'].map(lambda ign: PLAYER_INFO.get(ign, {}).get('role', ''))
        
        # Check if this is a file with loot data
        if 'Player' in df.columns and 'IGN' in df.columns and 'Item' in df.columns:
            # Add 'guildie' to players without a name in loot data
            df['Player'] = df['Player'].fillna('guildie')
            
            # Add new columns for class, spec, token, and role
            df['Class'] = df['IGN'].map(lambda ign: PLAYER_INFO.get(ign, {}).get('class', ''))
            df['Spec'] = df['IGN'].map(lambda ign: PLAYER_INFO.get(ign, {}).get('spec', ''))
            df['Token'] = df['IGN'].map(lambda ign: PLAYER_INFO.get(ign, {}).get('token', ''))
            df['Role'] = df['IGN'].map(lambda ign: PLAYER_INFO.get(ign, {}).get('role', ''))
        
        # Save the updated file
        df.to_csv(csv_file, index=False)
        print(f"Updated {csv_file}")

if __name__ == "__main__":
    update_csv_files()
    print("Update complete!") 