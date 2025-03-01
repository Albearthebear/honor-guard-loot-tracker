import pandas as pd
import os
from collections import defaultdict, Counter
import unicodedata
import csv
from datetime import datetime

class DragonSoulLootAnalyzer:
    """
    World of Warcraft Dragon Soul Raid Loot Analyzer - Enhanced Version
    
    This tool analyzes loot distribution across Dragon Soul raids to provide
    fair and balanced recommendations for future loot distribution, with
    separate priority lists for different stat users and item types.
    """
    
    def __init__(self, data_dir="processed_data"):
        self.data_dir = data_dir
        self.all_participants = None
        self.loot_data = []
        self.raid_participants = []
        self.player_loot_count = defaultdict(int)
        self.player_token_count = defaultdict(lambda: defaultdict(int))
        self.player_info = {}
        
        # For handling name variations
        self.name_mapping = {}
        
        # Manual mappings for known variations
        self.manual_mappings = {
            'saoki': 'saokipriest',
            'ruskov': 'rùskøv',
            'pepsi': 'pepsícola',
            'delusive': 'ðelusive',
            'ricardo': 'ricardomìlos',
            'overdeath': 'ooverdeath',
            'borrann': 'borran'
        }
        
        # PUG identifiers to filter out
        self.pug_identifiers = ['-pug', '-good pug']
        
        # Explicit list of additional players to exclude (PUGs and others)
        self.exclude_players = [
            # Add specific names of players to exclude here
            'Ifbbathlete', 'Andrewd', 'Rewolut', 'Corwor', 'anotherpug'
        ]
        
        # Debug configuration
        self.debug_config = {
            'enabled': False
        }
        
        # Dragon Soul has 8 bosses total
        self.total_bosses = 8
        
        # Mapping of file patterns to bosses covered
        self.file_to_bosses = {
            "25man_58": 5,        # First 5 bosses in 25-man
            "10man_war_spine": 2, # Warmaster Blackhorn and Spine of Deathwing (bosses 6-7)
            "10man_madness": 1    # Madness of Deathwing (boss 8)
        }
        
        # Store boss participation for each player (out of 8 possible bosses)
        self.player_boss_attendance = defaultdict(int)
        
        # Store which raid size each player participated in
        self.player_raid_size = defaultdict(set)
        
        # Class to primary stat mapping
        self.class_to_primary_stat = {
            'DK': 'Strength',
            'Druid': {
                'Balance': 'Intellect',
                'Feral': 'Agility',
                'Restoration': 'Intellect'
            },
            'Hunter': 'Agility',
            'Mage': 'Intellect',
            'Paladin': {
                'Holy': 'Intellect',
                'Protection': 'Strength',
                'Retribution': 'Strength'
            },
            'Priest': 'Intellect',
            'Rogue': 'Agility',
            'Shaman': {
                'Elemental': 'Intellect',
                'Enhancement': 'Agility',
                'Restoration': 'Intellect'
            },
            'Warlock': 'Intellect',
            'Warrior': 'Strength'
        }
        
        # Store which players are healers
        self.healers = set()
        
        # Priority calculation weights - TWEAKABLE VARIABLES
        self.attendance_weight = 0.55     # How much attendance affects priority score
        self.item_penalty_multiplier = 55    # Base multiplier for item penalties
        self.token_penalty_reduction = 0.75   # Tokens count as 50% of a regular item for penalties
        self.raid_25_percent_bonus = 0   # 25% bonus for 25-man raid attendance
        
        # Initialize item categorization system
        self.initialize_item_categorization()
        
        # Track item slots received by players
        self.player_item_slots = defaultdict(lambda: defaultdict(int))
        
    def initialize_item_categorization(self):
        """Initialize a comprehensive item categorization system based on Dragon Soul loot"""
        
        # Item slot categories with their importance weights
        self.slot_categories = {
            # Highest value slots (1.5)
            'head': 1.5,       # Helms, hoods, crowns
            'chest': 1.5,      # Robes, chestpieces
            'legs': 1.5,       # Pants, leggings, kilts
            'weapon': 1.5,     # All weapons
            'trinket': 1.5,    # Trinkets
            
            # Medium-high value slots (1.3)
            'shoulder': 1.3,   # Shoulders, spaulders
            'hands': 1.3,      # Gloves, gauntlets
            
            # Medium-low value slots (1.2)
            'waist': 1.2,      # Belts, girdles
            'feet': 1.2,       # Boots, treads
            
            # Low value slots (1.1)
            'wrist': 1.1,      # Bracers, wristguards
            
            # Lowest value slots (1.0)
            'neck': 1.0,       # Necklaces, amulets
            'finger': 1.0,     # Rings
            'back': 1.2,       # Cloaks, capes
            'ranged': 1.0,     # Ranged weapons, wands, thrown
            'off-hand': 1.2,   # Off-hand items, shields
        }
        
        # Token slot importance by token type
        self.token_slot_importance = {
            'Vanquisher': {  # DKs, Druids, Mages, Rogues
                'head': 1.5, 
                'shoulder': 1.3,
                'chest': 1.5,
                'hands': 1.3,
                'legs': 1.5
            },
            'Conqueror': {   # Paladins, Priests, Warlocks
                'head': 1.5,
                'shoulder': 1.3,
                'chest': 1.5,
                'hands': 1.3,
                'legs': 1.5
            },
            'Protector': {   # Hunters, Shamans, Warriors
                'head': 1.5,
                'shoulder': 1.3,
                'chest': 1.5,
                'hands': 1.3,
                'legs': 1.5
            }
        }

        # Manual mapping for token items
        self.token_mapping = {
            'crown of the corrupted protector': ('Protector', 'head'),
            'shoulders of the corrupted protector': ('Protector', 'shoulder'),
            'chest of the corrupted protector': ('Protector', 'chest'),
            'gauntlets of the corrupted protector': ('Protector', 'hands'),
            'leggings of the corrupted protector': ('Protector', 'legs'),
            
            'crown of the corrupted conqueror': ('Conqueror', 'head'),
            'shoulders of the corrupted conqueror': ('Conqueror', 'shoulder'),
            'chest of the corrupted conqueror': ('Conqueror', 'chest'),
            'gauntlets of the corrupted conqueror': ('Conqueror', 'hands'),
            'leggings of the corrupted conqueror': ('Conqueror', 'legs'),
            
            'crown of the corrupted vanquisher': ('Vanquisher', 'head'),
            'shoulders of the corrupted vanquisher': ('Vanquisher', 'shoulder'),
            'chest of the corrupted vanquisher': ('Vanquisher', 'chest'),
            'gauntlets of the corrupted vanquisher': ('Vanquisher', 'hands'),
            'leggings of the corrupted vanquisher': ('Vanquisher', 'legs'),
        }
        
        # Initialize item data from loot tables CSV
        self.load_loot_tables()
        
    def load_loot_tables(self):
        """
        Load item data from the loot_tables.csv file to improve item classification.
        This creates a mapping of item names to their slots and types.
        """
        self.loot_table_items = {}  # Maps item name to (slot, type)
        self.token_items = {}       # Maps token name to slot
        
        # Path to the loot tables CSV
        loot_tables_path = "loot_tables.csv"
        
        if not os.path.exists(loot_tables_path):
            print(f"Warning: Loot tables file not found at {loot_tables_path}")
            return
            
        try:
            # Read the CSV file
            with open(loot_tables_path, 'r') as f:
                lines = f.readlines()
            
            print(f"Read {len(lines)} lines from loot_tables.csv")
            
            # Skip header line
            current_boss = None
            current_difficulty = None
            
            for line in lines[1:]:  # Skip header
                parts = line.strip().split(',')
                
                # Skip empty lines
                if not line.strip():
                    continue
                    
                # Check if this is a heading line
                if len(parts) == 1:
                    current_boss = parts[0]
                    continue
                    
                # Check if this is a difficulty line
                if len(parts) == 2 and parts[1] and not parts[0]:
                    current_difficulty = parts[1]
                    continue
                    
                # Extract slot, item name, and type
                slot = parts[2].strip() if len(parts) > 2 and parts[2] else ''
                item_name = parts[3].strip() if len(parts) > 3 and parts[3] else ''
                item_type = parts[4].strip() if len(parts) > 4 and parts[4] else ''
                
                if item_name and slot:
                    # Clean up item name (some have duplicated names)
                    if item_name.count(item_name.split()[0]) > 1:
                        item_name = ' '.join(item_name.split()[:len(item_name.split())//2])
                    
                    # Store in our mapping
                    self.loot_table_items[item_name.lower()] = (slot.lower(), item_type)
                    
                    # Also store without the "- Item - Cataclysm Classic" suffix
                    clean_name = item_name.lower()
                    if " - item - cataclysm classic" in clean_name:
                        clean_name = clean_name.replace(" - item - cataclysm classic", "").strip()
                        self.loot_table_items[clean_name] = (slot.lower(), item_type)
                    
                    # Check if this is a token item using our manual mapping
                    if clean_name in self.token_mapping:
                        token_type, token_slot = self.token_mapping[clean_name]
                        self.token_items[clean_name] = token_slot
                        print(f"Added token item: {item_name} -> {token_type} {token_slot}")
            
            print(f"Loaded {len(self.loot_table_items)} items from loot tables")
            print(f"Identified {len(self.token_items)} token items")
            
        except Exception as e:
            print(f"Error loading loot tables: {e}")
            import traceback
            traceback.print_exc()
        
    def normalize_name(self, name):
        """Normalize player name to handle case differences and special characters"""
        if not name:
            return name
            
        # Convert to lowercase
        normalized = name.lower()
        
        # Apply manual mappings if available
        if normalized in self.manual_mappings:
            normalized = self.manual_mappings[normalized]
            
        # If we have a mapping for this name, use the canonical version
        if normalized in self.name_mapping:
            normalized = self.name_mapping[normalized]
            
        return normalized
    
    def is_pug(self, player_name):
        """Check if a player is a PUG based on their name or exclusion list"""
        if pd.isna(player_name) or player_name is None:
            return True
        
        # Check if in explicit exclusion list
        normalized_name = player_name.lower().strip()
        if normalized_name in [name.lower() for name in self.exclude_players]:
            print(f"Excluding player from explicit list: {player_name}")
            return True
        
        # Check if matches PUG identifiers
        return any(identifier.lower() in player_name.lower() for identifier in self.pug_identifiers)
    
    def get_column_name(self, row, base_names):
        """Helper function to find column names with or without .1 suffix"""
        if isinstance(base_names, str):
            base_names = [base_names]
            
        for base_name in base_names:
            for col in [base_name, f"{base_name}.1"]:
                if col in row.index:
                    return col
        return None
    
    def extract_player_info(self, row):
        """Extract player information from a DataFrame row"""
        # Get column names
        ign_col = self.get_column_name(row, 'IGN')
        if not ign_col or pd.isna(row[ign_col]):
            return None, None
            
        # Skip PUGs
        if self.is_pug(row[ign_col]):
            return None, None
            
        # Normalize player name
        player_name = self.normalize_name(row[ign_col])
        if not player_name:
            return None, None
            
        # Get other column values
        class_col = self.get_column_name(row, 'Class')
        spec_col = self.get_column_name(row, 'Spec')
        token_col = self.get_column_name(row, 'Token')
        role_col = self.get_column_name(row, 'Role')
        player_col = self.get_column_name(row, 'Player')
        
        # Extract values with fallbacks
        player_class = row.get(class_col) if class_col else None
        player_spec = row.get(spec_col) if spec_col else None
        player_token = row.get(token_col) if token_col else None
        player_role = row.get(role_col) if role_col else None
        player_real_name = row.get(player_col) if player_col else player_name
        
        # Determine primary stat
        primary_stat = self.get_player_primary_stat(player_class, player_spec) if player_class and not pd.isna(player_class) else 'Unknown'
        
        # Create player info dictionary
        player_info = {
            'Player': player_real_name,
            'Class': player_class if player_class and not pd.isna(player_class) else 'Unknown',
            'Spec': player_spec if player_spec and not pd.isna(player_spec) else 'Unknown',
            'Token': player_token if player_token and not pd.isna(player_token) else 'Unknown',
            'Role': player_role if player_role and not pd.isna(player_role) else 'Unknown',
            'Original_IGN': row[ign_col],
            'Primary_Stat': primary_stat
        }
        
        return player_name, player_info
    
    def identify_name_variations(self):
        """Find potential name variations in the data"""
        # Get all names from loot data
        loot_names = set()
        for _, loot_df in self.loot_data:
            for _, row in loot_df.iterrows():
                ign_col = self.get_column_name(row, 'IGN')
                if ign_col and not pd.isna(row[ign_col]):
                    loot_names.add(row[ign_col].lower().strip())
        
        # Get all names from participant data
        participant_names = set()
        for _, participants_df in self.raid_participants:
            for _, row in participants_df.iterrows():
                ign_col = self.get_column_name(row, 'IGN')
                if ign_col and not pd.isna(row[ign_col]):
                    participant_names.add(row[ign_col].lower().strip())
        
        # Auto-detect additional mappings
        for loot_name in loot_names:
            # Skip if already in manual mappings
            if loot_name in self.manual_mappings.keys():
                continue
                
            # Try to find close matches
            if loot_name not in participant_names:
                # Try to find a closest match (this is a simple approach)
                for part_name in participant_names:
                    # If the name starts the same (like 'saoki' vs 'saokipriest')
                    if loot_name.startswith(part_name) or part_name.startswith(loot_name):
                        self.name_mapping[loot_name] = part_name
                        break
                    # Handle special characters by comparing without them
                    norm_loot = ''.join(c for c in unicodedata.normalize('NFD', loot_name) if unicodedata.category(c) != 'Mn')
                    norm_part = ''.join(c for c in unicodedata.normalize('NFD', part_name) if unicodedata.category(c) != 'Mn')
                    if norm_loot == norm_part:
                        self.name_mapping[loot_name] = part_name
                        break
        
        print("Name mappings identified:")
        print("  Manual mappings:")
        for orig, mapped in self.manual_mappings.items():
            print(f"    {orig} -> {mapped}")
        
        print("  Auto-detected mappings:")
        for orig, mapped in self.name_mapping.items():
            print(f"    {orig} -> {mapped}")
    
    def get_player_primary_stat(self, player_class, player_spec):
        """Determine the primary stat for a player based on class and spec"""
        if player_class in self.class_to_primary_stat:
            stat_info = self.class_to_primary_stat[player_class]
            
            if isinstance(stat_info, dict):
                # For classes with spec-dependent stats
                if player_spec in stat_info:
                    return stat_info[player_spec]
                else:
                    # Default to the first stat if spec not found
                    return next(iter(stat_info.values()))
            else:
                # For classes with a single primary stat
                return stat_info
        
        return 'Unknown'
        
    def extract_token_info(self, item_name):
        """Extract token type and slot from an item name"""
        if not item_name:
            return None, None
            
        item_name_lower = item_name.lower()
        
        # Remove the "- Item - Cataclysm Classic" suffix if present
        if " - item - cataclysm classic" in item_name_lower:
            item_name_lower = item_name_lower.replace(" - item - cataclysm classic", "").strip()
        
        # Check if the item is in our manual token mapping
        if item_name_lower in self.token_mapping:
            token_type, token_slot = self.token_mapping[item_name_lower]
            print(f"Found token item: {item_name} -> {token_type} {token_slot}")
            return token_type, token_slot
            
        return None, None
        
    def load_data(self):
        """Load all CSV data files from the data directory"""
        print("Loading data from:", self.data_dir)
        
        # Load all participants data
        all_participants_path = os.path.join(self.data_dir, "all_participants.csv")
        if os.path.exists(all_participants_path):
            self.all_participants = pd.read_csv(all_participants_path)
            
            # Create player info dictionary for ALL known players
            for _, row in self.all_participants.iterrows():
                player_name, player_info = self.extract_player_info(row)
                if player_name and player_info:
                    self.player_info[player_name] = player_info
                    
                    # Track healers
                    if player_info['Role'] == 'Healer':
                        self.healers.add(player_name)
            
            # Add manual player info for ooverdeath
            if 'ooverdeath' not in self.player_info:
                self.player_info['ooverdeath'] = {
                    'Player': 'over',
                    'Class': 'DK',
                    'Spec': 'Blood',
                    'Token': 'Vanquisher',
                    'Role': 'Main Tank',
                    'Original_IGN': 'overdeath',
                    'Primary_Stat': 'Strength'
                }
                print("Added missing player info for ooverdeath manually")
        
        # First pass to load participant data
        for filename in os.listdir(self.data_dir):
            if filename.endswith("_participants.csv"):
                file_path = os.path.join(self.data_dir, filename)
                participants_df = pd.read_csv(file_path)
                self.raid_participants.append((filename, participants_df))
                
                # Determine how many bosses this file represents
                bosses_killed = 0
                for pattern, count in self.file_to_bosses.items():
                    if pattern in filename:
                        bosses_killed = count
                        break
                
                # Determine raid size (10 vs 25)
                raid_size = "25" if "25man" in filename else "10"
                
                # Update player boss attendance and raid size participation
                for _, row in participants_df.iterrows():
                    player_name, _ = self.extract_player_info(row)
                    if player_name:
                        self.player_boss_attendance[player_name] += bosses_killed
                        self.player_raid_size[player_name].add(raid_size)
        
        # Now identify potential name variations
        self.identify_name_variations()
        
        # Now load and process loot data with name mapping
        for filename in os.listdir(self.data_dir):
            if filename.endswith("_loot.csv"):
                file_path = os.path.join(self.data_dir, filename)
                loot_df = pd.read_csv(file_path)
                self.loot_data.append((filename, loot_df))
                
                # Debug loot data - simplified
                if filename == "25man_58_loot.csv":  # Only show for the main loot file
                    print(f"\nProcessing loot from {filename}: {len(loot_df)} items")
                
                # Count loot per player
                for _, row in loot_df.iterrows():
                    # Extract player info
                    player_name, player_info = self.extract_player_info(row)
                    if not player_name:
                        continue
                        
                    # Update player_loot_count
                    self.player_loot_count[player_name] += 1
                    
                    # For debugging
                    original_name = row[self.get_column_name(row, 'IGN')]
                    if player_name != original_name.lower().strip():
                        print(f"Mapped loot: {original_name} -> {player_name}: {row['Item']}")
                    
                    # Update player_info if not already set
                    if player_name not in self.player_info:
                        self.player_info[player_name] = player_info
                        print(f"Added missing player info from loot data: {player_name} - {player_info['Class']} {player_info['Spec']}")
                    # Update player info if some fields are missing
                    elif self.player_info[player_name].get('Class') in [None, "Unknown"]:
                        self.player_info[player_name].update(player_info)
                        print(f"Updated player info from loot data: {player_name} - {player_info['Class']} {player_info['Spec']}")
                    
                    # Track healers
                    if player_info['Role'] == 'Healer':
                        self.healers.add(player_name)
                    
                    # Process item information
                    item_name = row['Item']
                    
                    # Check if this is a token item
                    token, token_slot = self.extract_token_info(item_name)
                    if token:
                        self.player_token_count[player_name][token] += 1
                        
                        # Track token slot
                        if token_slot != 'unknown':
                            self.player_item_slots[player_name][token_slot] += 1
                            print(f"  Token slot: {item_name} -> {token_slot}")
                    
                    # This prevents double-counting token items
                    if not token:
                        item_slot = self.determine_item_slot(item_name)
                        if item_slot != 'unknown':
                            self.player_item_slots[player_name][item_slot] += 1
                    
    
    def calculate_attendance(self):
        """Calculate attendance percentage for each player based on boss kills"""
        attendance_percentage = {}
        
        for player, bosses_attended in self.player_boss_attendance.items():
            # Calculate raw attendance
            base_attendance = (bosses_attended / self.total_bosses) * 100
            
            # Apply 25-man bonus if applicable
            if "25" in self.player_raid_size.get(player, set()):
                # Track 25-man bosses where player was present
                player_25man_bosses = 0
                total_25man_bosses = 0
                
                # First count total 25-man bosses
                for filename, _ in self.raid_participants:
                    if "25man" in filename:
                        for pattern, count in self.file_to_bosses.items():
                            if pattern in filename:
                                total_25man_bosses += count
                                break
                
                # Then count which ones player attended
                for filename, participants_df in self.raid_participants:
                    if "25man" in filename:
                        for _, row in participants_df.iterrows():
                            player_name, _ = self.extract_player_info(row)
                            if player_name == player:
                                # Count bosses for this raid
                                for pattern, count in self.file_to_bosses.items():
                                    if pattern in filename:
                                        player_25man_bosses += count
                                        break
                                break
                
                # Apply bonus proportionally to player's 25-man attendance
                if total_25man_bosses > 0:
                    bonus_portion = player_25man_bosses / total_25man_bosses
                    attendance_percentage[player] = base_attendance * (1 + (self.raid_25_percent_bonus * bonus_portion))
                else:
                    attendance_percentage[player] = base_attendance
            else:
                attendance_percentage[player] = base_attendance
            
        return attendance_percentage
    
    def calculate_loot_per_boss(self):
        """Calculate loot received per boss attended for each player"""
        loot_per_boss = {}
        
        for player, loot_count in self.player_loot_count.items():
            bosses_attended = self.player_boss_attendance.get(player, 0)
            if bosses_attended > 0:
                loot_per_boss[player] = loot_count / bosses_attended
            else:
                loot_per_boss[player] = 0
                
        return loot_per_boss
    
    def get_token_class_distribution(self):
        """Get distribution of classes per token type"""
        token_classes = defaultdict(list)
        
        for player, info in self.player_info.items():
            if 'Token' in info and info['Token']:
                token_classes[info['Token']].append({
                    'Player': player,
                    'Class': info.get('Class', 'Unknown'),
                    'Spec': info.get('Spec', 'Unknown'),
                    'Role': info.get('Role', 'Unknown')
                })
                
        return token_classes
    
    def get_loot_priority_recommendations(self, attendance, loot_per_boss):
        """Generate loot priority recommendations based on attendance and loot per boss"""

        regular_priority_scores = {}
        token_priority_scores = {}
        
        # Include ALL players we know about (not just those with loot)
        all_known_players = set(self.player_info.keys())
        
        # Handle overdeath/ooverdeath name conflict - prefer ooverdeath
        if 'ooverdeath' in all_known_players and 'overdeath' in all_known_players:
            all_known_players.remove('overdeath')
            print("Removed 'overdeath' from known players as 'ooverdeath' is present")
        
        for player in all_known_players:
            if player in self.player_boss_attendance and not self.is_pug(player):
                # Base priority comes from attendance
                attendance_score = attendance.get(player, 0) * self.attendance_weight
                
                # Count bosses attended with 25-man scaling
                bosses_attended = max(1, self.player_boss_attendance.get(player, 1))
                
                # Get player's token type
                player_token = self.player_info.get(player, {}).get('Token', 'Unknown')
                
                # Calculate penalties for regular items and token items separately
                regular_item_penalty = 0
                token_item_penalty = 0
                
                # Calculate penalties for each slot type
                for slot, count in self.player_item_slots[player].items():
                    if count > 0:
                        # Get the appropriate multiplier for this slot from slot_categories
                        slot_multiplier = self.slot_categories.get(slot, 1.0)
                        
                        # For token slots, check token-specific importance
                        if player_token in self.token_slot_importance and slot in self.token_slot_importance[player_token]:
                            token_slot_multiplier = self.token_slot_importance[player_token][slot]
                        else:
                            token_slot_multiplier = slot_multiplier
                        
                        # Calculate base penalty for this slot
                        base_slot_penalty = (count / bosses_attended) * self.item_penalty_multiplier
                        
                        # Apply slot weighting
                        weighted_slot_penalty = base_slot_penalty * slot_multiplier
                        weighted_token_slot_penalty = base_slot_penalty * token_slot_multiplier
                        
                        # Add to appropriate penalty category
                        # Check if this is a token slot
                        if player_token in self.token_slot_importance and slot in self.token_slot_importance[player_token]:
                            token_item_penalty += weighted_token_slot_penalty
                        else:
                            regular_item_penalty += weighted_slot_penalty
                
                # Calculate raid size bonus
                raid_size_bonus = 0
                if "25" in self.player_raid_size.get(player, set()):
                    # Count how many bosses were done in 25-man
                    twenty_five_man_bosses = 0
                    for filename, participants_df in self.raid_participants:
                        if "25man" in filename:
                            # Check if player was in this raid
                            player_in_raid = False
                            for _, row in participants_df.iterrows():
                                player_name, _ = self.extract_player_info(row)
                                if player_name == player:
                                    player_in_raid = True
                                    break
                                    
                            if player_in_raid:
                                # Count bosses
                                for pattern, count in self.file_to_bosses.items():
                                    if pattern in filename:
                                        twenty_five_man_bosses += count
                                        break
                    
                    # Apply bonus proportionally to 25-man attendance
                    bonus_portion = twenty_five_man_bosses / self.total_bosses
                    raid_size_bonus = attendance_score * (self.raid_25_percent_bonus * bonus_portion)
                
                # Calculate final priority scores
                regular_score = attendance_score - regular_item_penalty - (token_item_penalty * self.token_penalty_reduction) + raid_size_bonus
                token_score = attendance_score - token_item_penalty - (regular_item_penalty * self.token_penalty_reduction) + raid_size_bonus
                
                # Store both scores
                regular_priority_scores[player] = regular_score
                token_priority_scores[player] = token_score
        
        # Sort by regular priority score (descending)
        sorted_players = sorted(regular_priority_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Generate recommendations
        recommendations = []
        
        for player, score in sorted_players:
            if player in self.player_info:
                info = self.player_info[player]
                token_type = info.get('Token', 'Unknown')
                raid_sizes = ", ".join(sorted(self.player_raid_size.get(player, ["N/A"])))
                
                # Get primary stat for this player
                player_class = info.get('Class', 'Unknown')
                player_spec = info.get('Spec', 'Unknown')
                primary_stat = self.get_player_primary_stat(player_class, player_spec)
                
                # Check if player is a healer
                is_healer = player in self.healers
                
                # Use original IGN for display
                display_name = info.get('Original_IGN', player)
                
                recommendations.append({
                    'Player': player,
                    'IGN': display_name,
                    'Class': player_class,
                    'Spec': player_spec,
                    'Role': info.get('Role', 'Unknown'),
                    'Token': token_type,
                    'Stat': primary_stat,
                    'Is Healer': is_healer,
                    'Attendance': f"{attendance.get(player, 0):.1f}%",
                    'Attendance Value': attendance.get(player, 0),
                    'Bosses': self.player_boss_attendance.get(player, 0),
                    'Raid Sizes': raid_sizes,
                    'Items Received': self.player_loot_count.get(player, 0),
                    'Items Per Boss': f"{loot_per_boss.get(player, 0):.2f}",
                    'Priority Score': f"{score:.1f}",
                    'Priority Score Value': score,
                    'Token Priority Score': f"{token_priority_scores.get(player, 0):.1f}",
                    'Token Priority Score Value': token_priority_scores.get(player, 0),
                    'Token Items': sum(self.player_token_count[player].values())
                })
        
        return recommendations
    
    def analyze_and_print_report(self):
        """Analyze loot data and print a comprehensive report"""
        # Load data
        self.load_data()
        
        # Check if we have data
        if not self.player_loot_count:
            print("No loot data found. Please check your data directory.")
            return
        
        # Calculate attendance
        attendance = self.calculate_attendance()
        
        # Calculate loot per boss
        loot_per_boss = self.calculate_loot_per_boss()
        
        # Get token class distribution
        self.get_token_class_distribution()
        
        # Get loot priority recommendations
        recommendations = self.get_loot_priority_recommendations(attendance, loot_per_boss)
        
        # Export detailed analysis to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"loot_analysis_report_{timestamp}.csv"
        self.export_to_csv(recommendations, csv_filename)
        
        # Print summary information
        print("\nSUMMARY INFORMATION:")
        print("-"*80)
        
        # Print total items distributed
        total_items = sum(self.player_loot_count.values())
        print(f"Total Items Distributed: {total_items}")
        
        # Print token distribution
        token_counts = Counter()
        for player_tokens in self.player_token_count.values():
            for token, count in player_tokens.items():
                token_counts[token] += count
        
        print("\nToken Distribution:")
        for token, count in token_counts.items():
            print(f"  {token}: {count}")
        
        # Print top 5 priority players
        print("\nTop 5 Priority Players:")
        sorted_players = sorted(recommendations, key=lambda x: float(x['Priority Score Value']), reverse=True)
        for i, player in enumerate(sorted_players[:5], 1):
            print(f"  {i}. {player['IGN']} ({player['Class']} - {player['Spec']}) - Score: {player['Priority Score']}")
        
        print("\nDetailed analysis has been exported to:", csv_filename)
        print("The CSV file contains complete information including:")
        print("- Player details (Name, Class, Spec, Role)")
        print("- Raid participation metrics")
        print("- Loot distribution")
        print("- Priority scores and rankings")
        print("- Personalized recommendations")
        
        print("\n" + "="*80)
        print(f"{'END OF REPORT':^80}")
        print("="*80)

    def determine_item_slot(self, item_name):
        """
        Determine the slot for an item based on its name.
        Priority order:
        1. Check in loot_table_items from CSV
        2. Check if it's a token item
        3. Try to determine from item name patterns
        4. Return 'unknown' if not found
        """
        if not item_name:
            return 'unknown'
            
        item_name_lower = item_name.lower()
        
        # Remove the "- Item - Cataclysm Classic" suffix if present
        if " - item - cataclysm classic" in item_name_lower:
            item_name_lower = item_name_lower.replace(" - item - cataclysm classic", "").strip()
        
        # 1. Check in loot tables from CSV
        if hasattr(self, 'loot_table_items') and item_name_lower in self.loot_table_items:
            slot, _ = self.loot_table_items[item_name_lower]
            return slot
            
        # 2. Check if it's a token item
        token, token_slot = self.extract_token_info(item_name)
        if token and token_slot != 'unknown':
            return token_slot
            
        
        # 3. Try to determine from item name patterns
        # Common slot keywords
        slot_keywords = {
            'head': ['helm', 'hood', 'crown', 'cowl', 'headpiece', 'faceguard', 'headguard', 'mask'],
            'neck': ['necklace', 'amulet', 'choker', 'pendant', 'chain'],
            'shoulder': ['shoulder', 'spaulders', 'mantle', 'shoulderguards', 'pauldrons'],
            'back': ['cloak', 'cape', 'drape', 'shroud'],
            'chest': ['chest', 'robe', 'tunic', 'breastplate', 'hauberk', 'vestment'],
            'wrist': ['bracers', 'wristguards', 'wristbands', 'vambraces'],
            'hands': ['gloves', 'gauntlets', 'handguards', 'grips', 'fists'],
            'waist': ['belt', 'girdle', 'waistguard', 'waistband', 'cinch', 'cord'],
            'legs': ['leggings', 'pants', 'legguards', 'legplates', 'kilt', 'greaves'],
            'feet': ['boots', 'treads', 'sabatons', 'stompers', 'greaves', 'footguards'],
            'finger': ['ring', 'band', 'seal', 'signet', 'loop'],
            'trinket': ['trinket', 'charm', 'insignia', 'heart', 'eye', 'fang', 'vial', 'orb'],
            'weapon': ['sword', 'axe', 'mace', 'staff', 'dagger', 'blade', 'hammer', 'fist', 'scythe', 'glaive', 'spear', 'polearm'],
            'ranged': ['bow', 'gun', 'crossbow', 'wand', 'thrown', 'rifle', 'launcher'],
            'off-hand': ['shield', 'offhand', 'tome', 'totem', 'idol', 'orb', 'defender']
        }
        
        # Check for slot keywords in the item name
        for slot, keywords in slot_keywords.items():
            if any(keyword in item_name_lower for keyword in keywords):
                return slot
        
        # 4. If we get here, we couldn't determine the slot
        print(f"  WARNING: Could not determine slot for item: {item_name}")
        return 'unknown'

    def export_to_csv(self, recommendations, filename="loot_analysis_report.csv"):
        """
        Export the loot analysis data to a CSV file with enhanced metrics and rankings.
        """
        # Calculate various rankings
        overall_rank = {rec['Player']: idx + 1 for idx, rec in enumerate(sorted(
            recommendations, 
            key=lambda x: float(x['Priority Score Value']), 
            reverse=True
        ))}

        # Calculate token rankings
        token_rank = {}
        for token in ['Vanquisher', 'Conqueror', 'Protector']:
            token_players = [r for r in recommendations if r['Token'] == token]
            token_players.sort(key=lambda x: float(x['Token Priority Score Value']), reverse=True)
            for idx, player in enumerate(token_players):
                token_rank[player['Player']] = idx + 1

        # Calculate stat rankings
        stat_rank = {}
        for stat in ['Intellect', 'Agility', 'Strength']:
            stat_players = [r for r in recommendations if r['Stat'] == stat]
            stat_players.sort(key=lambda x: float(x['Priority Score Value']), reverse=True)
            for idx, player in enumerate(stat_players):
                stat_rank[player['Player']] = idx + 1

        # Calculate role rankings
        role_rank = {}
        for role in ['Healer', 'DPS', 'Main Tank', 'Offtank']:
            role_players = [r for r in recommendations if r['Role'] == role]
            role_players.sort(key=lambda x: float(x['Priority Score Value']), reverse=True)
            for idx, player in enumerate(role_players):
                role_rank[player['Player']] = idx + 1

        # Prepare CSV headers
        headers = [
            'Player Name',
            'Class',
            'Spec',
            'Role',
            'Token Type',
            'Primary Stat',
            'Is Healer',
            'Overall Rank',
            'Token Rank',
            'Stat Rank',
            'Role Rank',
            'Attendance %',
            'Bosses Attended',
            'Raid Sizes',
            'Total Items',
            'Items Per Boss',
            'Token Items',
            'Priority Score',
            'Token Priority Score',
            'Item Slots Distribution',
            'Recommendation'
        ]

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            for rec in recommendations:
                # Get item slots distribution
                slots_dist = []
                for slot, count in self.player_item_slots[rec['Player']].items():
                    if count > 0:
                        slots_dist.append(f"{slot}:{count}")

                # Generate recommendation based on scores and rankings
                recommendation = self.generate_recommendation(
                    rec, 
                    overall_rank[rec['Player']], 
                    token_rank.get(rec['Player'], 0)
                )

                # Prepare row data
                row = {
                    'Player Name': rec['IGN'],
                    'Class': rec['Class'],
                    'Spec': rec['Spec'],
                    'Role': rec['Role'],
                    'Token Type': rec['Token'],
                    'Primary Stat': rec['Stat'],
                    'Is Healer': 'Yes' if rec['Is Healer'] else 'No',
                    'Overall Rank': overall_rank[rec['Player']],
                    'Token Rank': token_rank.get(rec['Player'], 'N/A'),
                    'Stat Rank': stat_rank.get(rec['Player'], 'N/A'),
                    'Role Rank': role_rank.get(rec['Player'], 'N/A'),
                    'Attendance %': rec['Attendance'],
                    'Bosses Attended': rec['Bosses'],
                    'Raid Sizes': rec['Raid Sizes'],
                    'Total Items': rec['Items Received'],
                    'Items Per Boss': rec['Items Per Boss'],
                    'Token Items': rec['Token Items'],
                    'Priority Score': rec['Priority Score'],
                    'Token Priority Score': rec['Token Priority Score'],
                    'Item Slots Distribution': ', '.join(slots_dist),
                    'Recommendation': recommendation
                }
                writer.writerow(row)

        print(f"\nDetailed analysis exported to {filename}")

    def generate_recommendation(self, player_data, overall_rank, token_rank):
        """Generate a recommendation string based on player data and rankings"""
        recommendations = []
        
        # High priority recommendations
        if overall_rank <= 3:
            recommendations.append("HIGH PRIORITY for next suitable item")
        elif overall_rank <= 5:
            recommendations.append("Priority candidate for loot")

        # Token-specific recommendations
        if token_rank <= 2:
            recommendations.append(f"HIGH PRIORITY for {player_data['Token']} tokens")
        
        # Attendance-based recommendations
        attendance = float(player_data['Attendance'].rstrip('%'))
        if attendance >= 87.5:
            recommendations.append("Excellent attendance")

        # Items per boss recommendations
        items_per_boss = float(player_data['Items Per Boss'])
        if items_per_boss < 0.2:
            recommendations.append("Due for loot")
        elif items_per_boss > 0.8:
            recommendations.append("Recently received multiple items")

        return " | ".join(recommendations) if recommendations else "Standard priority"

if __name__ == "__main__":
    analyzer = DragonSoulLootAnalyzer()
    
    # Run the full analysis
    print("\n")
    analyzer.analyze_and_print_report() 