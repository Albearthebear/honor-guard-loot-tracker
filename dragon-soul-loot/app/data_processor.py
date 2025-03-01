import os
import csv
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

class DataProcessor:
    """
    Processes CSV data files for the Dragon Soul Loot Manager
    """
    
    def __init__(self, data_dir: str = "data", processed_data_dir: str = "processed_data"):
        """
        Initialize the data processor
        
        Args:
            data_dir: Directory for processed JSON data
            processed_data_dir: Directory containing CSV files
        """
        self.data_dir = data_dir
        self.processed_data_dir = processed_data_dir
        self.player_info = {}
        self.loot_history = []
        self.raid_sessions = []
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
    def process_all_data(self):
        """Process all CSV files and generate JSON data files"""
        self._process_player_data()
        self._process_loot_data()
        self._generate_raid_sessions()
        self._save_processed_data()
        
    def _process_player_data(self):
        """Process player data from participants CSV files"""
        # Start with all_participants.csv if it exists
        all_participants_path = os.path.join(self.processed_data_dir, "all_participants.csv")
        
        if os.path.exists(all_participants_path):
            with open(all_participants_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    player_name = row.get('IGN', '').strip()
                    if not player_name:
                        continue
                        
                    # Normalize player name (lowercase for matching)
                    normalized_name = player_name.lower()
                    
                    # Store player info
                    self.player_info[normalized_name] = {
                        'Original_IGN': player_name,
                        'Class': row.get('Class', 'Unknown'),
                        'Spec': row.get('Spec', 'Unknown'),
                        'Token': row.get('Token', 'Unknown'),
                        'Role': row.get('Role', 'Unknown'),
                        'Note': row.get('Player', ''),  # Using the Player column as a note (contains guild status)
                        'Primary_Stat': self._determine_primary_stat(row.get('Class', ''), row.get('Spec', ''))
                    }
        
        # Process other participant files to catch any missing players
        for filename in os.listdir(self.processed_data_dir):
            if 'participants' in filename.lower() and filename.lower().endswith('.csv') and filename != 'all_participants.csv':
                file_path = os.path.join(self.processed_data_dir, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        player_name = row.get('IGN', '').strip()
                        if not player_name:
                            continue
                            
                        # Normalize player name
                        normalized_name = player_name.lower()
                        
                        # Only add if not already in player_info
                        if normalized_name not in self.player_info:
                            self.player_info[normalized_name] = {
                                'Original_IGN': player_name,
                                'Class': row.get('Class', 'Unknown'),
                                'Spec': row.get('Spec', 'Unknown'),
                                'Token': row.get('Token', 'Unknown'),
                                'Role': row.get('Role', 'Unknown'),
                                'Note': row.get('Player', ''),
                                'Primary_Stat': self._determine_primary_stat(row.get('Class', ''), row.get('Spec', ''))
                            }
    
    def _process_loot_data(self):
        """Process loot data from loot CSV files"""
        for filename in os.listdir(self.processed_data_dir):
            if 'loot' in filename.lower() and filename.lower().endswith('.csv'):
                file_path = os.path.join(self.processed_data_dir, filename)
                
                # Extract raid info from filename
                raid_info = self._extract_raid_info_from_filename(filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        player_name = row.get('IGN', '').strip()
                        item_name = row.get('Item', '').strip()
                        
                        if not player_name or not item_name:
                            continue
                            
                        # Normalize player name
                        normalized_name = player_name.lower()
                        
                        # Clean up item name (remove " - Item - Cataclysm Classic" suffix)
                        clean_item_name = item_name.replace(' - Item - Cataclysm Classic', '').strip()
                        
                        # Determine item type and slot
                        item_type, item_slot = self._determine_item_type_and_slot(clean_item_name)
                        
                        # Create loot entry
                        loot_entry = {
                            'player': normalized_name,
                            'item': clean_item_name,
                            'item_type': item_type,
                            'item_slot': item_slot,
                            'raid_type': raid_info.get('raid_type', 'Unknown'),
                            'boss': raid_info.get('boss', 'Unknown'),
                            'date': raid_info.get('date', 'Unknown'),
                            'note': f"{row.get('Note 1', '')} {row.get('Note 2', '')}".strip()
                        }
                        
                        self.loot_history.append(loot_entry)
                        
                        # Update player info if missing
                        if normalized_name not in self.player_info:
                            self.player_info[normalized_name] = {
                                'Original_IGN': player_name,
                                'Class': row.get('Class', 'Unknown'),
                                'Spec': row.get('Spec', 'Unknown'),
                                'Token': row.get('Token', 'Unknown'),
                                'Role': row.get('Role', 'Unknown'),
                                'Primary_Stat': self._determine_primary_stat(row.get('Class', ''), row.get('Spec', ''))
                            }
    
    def _generate_raid_sessions(self):
        """Generate raid sessions from the processed data"""
        # Group loot by raid info
        raid_groups = {}
        
        for loot in self.loot_history:
            raid_key = f"{loot['raid_type']}_{loot['boss']}_{loot['date']}"
            
            if raid_key not in raid_groups:
                raid_groups[raid_key] = {
                    'raid_type': loot['raid_type'],
                    'boss': loot['boss'],
                    'date': loot['date'],
                    'loot': []
                }
                
            raid_groups[raid_key]['loot'].append({
                'player': loot['player'],
                'item': loot['item'],
                'item_type': loot['item_type'],
                'item_slot': loot['item_slot'],
                'note': loot['note']
            })
        
        # Convert to list and add participants
        for raid_key, raid_data in raid_groups.items():
            # Find matching participant file
            participant_filename = None
            raid_type = raid_data['raid_type']
            boss = raid_data['boss']
            date = raid_data['date']
            
            for filename in os.listdir(self.processed_data_dir):
                if ('participants' in filename.lower() and 
                    raid_type.lower() in filename.lower() and 
                    (boss.lower() in filename.lower() or boss == 'Unknown') and
                    (date.lower() in filename.lower() or date == 'Unknown')):
                    participant_filename = filename
                    break
            
            # Add participants if file found
            participants = []
            if participant_filename:
                file_path = os.path.join(self.processed_data_dir, participant_filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        player_name = row.get('IGN', '').strip()
                        if player_name:
                            participants.append(player_name.lower())
            
            # Create raid session
            raid_session = {
                'raid_type': raid_data['raid_type'],
                'boss': raid_data['boss'],
                'date': raid_data['date'],
                'participants': participants,
                'loot_assignments': raid_data['loot']
            }
            
            self.raid_sessions.append(raid_session)
    
    def _save_processed_data(self):
        """Save processed data to JSON files"""
        # Save player info
        player_info_path = os.path.join(self.data_dir, 'player_info.json')
        with open(player_info_path, 'w', encoding='utf-8') as f:
            json.dump(self.player_info, f, indent=2)
        
        # Save loot history
        loot_history_path = os.path.join(self.data_dir, 'loot_history.json')
        with open(loot_history_path, 'w', encoding='utf-8') as f:
            json.dump(self.loot_history, f, indent=2)
        
        # Save raid sessions
        raid_sessions_path = os.path.join(self.data_dir, 'raid_sessions.json')
        with open(raid_sessions_path, 'w', encoding='utf-8') as f:
            json.dump(self.raid_sessions, f, indent=2)
    
    def _determine_primary_stat(self, class_name: str, spec: str) -> str:
        """Determine primary stat based on class and spec"""
        # Default mappings
        strength_classes = ['Warrior', 'Paladin', 'Death Knight', 'DK']
        agility_classes = ['Rogue', 'Hunter', 'Druid', 'Shaman']
        intellect_classes = ['Mage', 'Warlock', 'Priest', 'Shaman', 'Druid', 'Paladin']
        
        # Spec overrides
        if class_name == 'Druid':
            if spec in ['Feral', 'Guardian']:
                return 'Agility'
            else:  # Balance, Restoration
                return 'Intellect'
        elif class_name == 'Shaman':
            if spec == 'Enhancement':
                return 'Agility'
            else:  # Elemental, Restoration
                return 'Intellect'
        elif class_name == 'Paladin':
            if spec in ['Holy', 'Protection']:
                return 'Intellect'
            else:  # Retribution
                return 'Strength'
        
        # Default class-based determination
        if class_name in strength_classes:
            return 'Strength'
        elif class_name in agility_classes:
            return 'Agility'
        elif class_name in intellect_classes:
            return 'Intellect'
        
        return 'Unknown'
    
    def _determine_item_type_and_slot(self, item_name: str) -> tuple:
        """Determine item type and slot based on item name"""
        # Check for tokens
        if 'Corrupted Vanquisher' in item_name:
            return 'token', self._determine_token_slot(item_name)
        elif 'Corrupted Conqueror' in item_name:
            return 'token', self._determine_token_slot(item_name)
        elif 'Corrupted Protector' in item_name:
            return 'token', self._determine_token_slot(item_name)
        
        # Common item slots
        slot_keywords = {
            'Head': ['Crown', 'Helm', 'Hood', 'Faceguard'],
            'Neck': ['Necklace', 'Choker', 'Pendant', 'Amulet'],
            'Shoulder': ['Shoulderguards', 'Spaulders', 'Mantle', 'Shoulders'],
            'Back': ['Cloak', 'Cape', 'Drape'],
            'Chest': ['Chestplate', 'Robe', 'Tunic', 'Hauberk', 'Vest', 'Chest'],
            'Wrist': ['Bracers', 'Wristguards', 'Wristplates'],
            'Hands': ['Gloves', 'Gauntlets', 'Handguards', 'Grips'],
            'Waist': ['Belt', 'Girdle', 'Waistguard'],
            'Legs': ['Leggings', 'Legplates', 'Legguards', 'Greaves'],
            'Feet': ['Boots', 'Treads', 'Sabatons', 'Stompers'],
            'Finger': ['Ring', 'Band', 'Seal', 'Loop'],
            'Trinket': ['Trinket', 'Charm', 'Orb', 'Heart', 'Insignia', 'Eye'],
            'Weapon': ['Sword', 'Axe', 'Mace', 'Staff', 'Dagger', 'Bow', 'Gun', 'Wand', 'Fist', 'Glaive', 'Spear', 'Morningstar'],
            'Shield': ['Shield', 'Bulwark', 'Aegis'],
            'Relic': ['Idol', 'Totem', 'Libram', 'Sigil']
        }
        
        # Check for slot keywords in item name
        for slot, keywords in slot_keywords.items():
            for keyword in keywords:
                if keyword in item_name:
                    return 'gear', slot
        
        # Default
        return 'unknown', 'unknown'
    
    def _determine_token_slot(self, item_name: str) -> str:
        """Determine slot for token items"""
        if 'Head' in item_name:
            return 'Head'
        elif 'Chest' in item_name:
            return 'Chest'
        elif 'Hands' in item_name or 'Gauntlets' in item_name:
            return 'Hands'
        elif 'Legs' in item_name or 'Leggings' in item_name:
            return 'Legs'
        elif 'Shoulder' in item_name:
            return 'Shoulder'
        
        return 'unknown'
    
    def _extract_raid_info_from_filename(self, filename: str) -> Dict[str, str]:
        """Extract raid information from filename"""
        # Example: 25man_58___sunday_2402_loot.csv
        # or: 10man_war_spine___sunday_2402_loot.csv
        
        result = {
            'raid_type': 'Unknown',
            'boss': 'Unknown',
            'date': 'Unknown'
        }
        
        # Remove file extension
        base_name = filename.replace('.csv', '')
        
        # Split by underscores
        parts = base_name.split('_')
        
        # Extract raid type (10man or 25man)
        if parts and ('10man' in parts[0] or '25man' in parts[0]):
            result['raid_type'] = parts[0]
        
        # Extract boss name if present
        if len(parts) > 1:
            if 'war' in parts[1] and 'spine' in parts[2]:
                result['boss'] = 'Warmaster Blackhorn & Spine of Deathwing'
            elif 'madness' in parts[1]:
                result['boss'] = 'Madness of Deathwing'
            elif '58' in parts[1]:
                result['boss'] = 'Morchok to Ultraxion'
        
        # Extract date
        for i, part in enumerate(parts):
            if part in ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']:
                if i+1 < len(parts):
                    result['date'] = f"{part}_{parts[i+1]}"
                    break
        
        return result

# Function to run the data processor
def process_csv_data():
    """Process CSV data files and generate JSON data files"""
    processor = DataProcessor()
    processor.process_all_data()
    return "Data processing completed successfully"

if __name__ == "__main__":
    process_csv_data() 