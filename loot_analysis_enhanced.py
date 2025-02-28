import pandas as pd
import os
import re
from collections import defaultdict, Counter
import unicodedata

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
            'enabled': True,
            'players': ['ricardo', 'bestdk', 'borran', 'moruse', 'ooverdeath', 'albear'],
            'item_categories': {
                'madness_weapons': True,
                'other_weapons': True,
                'trinkets': True,
                'armor': True,
                'jewelry': True
            },
            'show_attendance': True,
            'show_loot_per_boss': True,
            'show_item_slots': True,
            'show_priority_calculation': True,
            'verbose_item_classification': False
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
        self.attendance_weight = 0.4         # How much attendance affects priority score
        self.item_penalty_multiplier = 40    # Base multiplier for item penalties
        self.token_penalty_reduction = 0.5   # Tokens count as 50% of a regular item for penalties
        self.raid_25_percent_bonus = 0.25    # 25% bonus for 25-man raid attendance
        
        # Initialize item categorization system
        self.initialize_item_categorization()
        
        # Track item slots received by players
        self.player_item_slots = defaultdict(lambda: defaultdict(int))
        
        # Track item types received by players
        self.player_jewelry_count = defaultdict(int)
        self.player_weapon_count = defaultdict(int)
        
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
        
        # Keywords to identify item slots
        self.slot_keywords = {
            'head': ['helm', 'hood', 'crown', 'cowl', 'headpiece'],
            'shoulder': ['shoulder', 'spaulder', 'mantle', 'amice'],
            'chest': ['chest', 'robe', 'tunic', 'hauberk', 'breastplate'],
            'wrist': ['wrist', 'bracer', 'vambrace'],
            'hands': ['glove', 'gauntlet', 'handguard', 'hand'],
            'waist': ['belt', 'waist', 'girdle', 'cord', 'sash'],
            'legs': ['leg', 'pant', 'kilt', 'legging', 'greave'],
            'feet': ['boot', 'treads', 'foot', 'sandal', 'shoe', 'sabatons'],
            'neck': ['neck', 'necklace', 'amulet', 'choker', 'collar'],
            'finger': ['ring', 'band', 'seal', 'signet', 'loop'],
            'back': ['cloak', 'cape', 'drape'],
            'ranged': ['wand', 'thrown', 'gun', 'bow', 'crossbow', 'arrow', 'bullet'],
            'off-hand': ['off-hand', 'shield', 'defender', 'bulwark', 'ward'],
            'trinket': ['trinket', 'charm', 'fetish', 'idol', 'totem', 'insignia', 'vial']
        }
        
        # Weapon types with their keywords
        self.weapon_types = {
            'one_hand_sword': ['sword', 'blade', 'souldrinker'],
            'one_hand_axe': ['axe', 'no\'kaled', 'elements of death', 'hand of morchok'],
            'one_hand_mace': ['mace', 'morningstar', 'maw of the dragonlord'],
            'two_hand_sword': ['greatsword', 'two-handed sword', 'gurthalak', 'voice of the deeps'],
            'two_hand_axe': ['greataxe', 'two-handed axe', 'experimental specimen slicer'],
            'two_hand_mace': ['hammer', 'maul', 'two-handed mace', 'ataraxis', 'cudgel of the warmaster'],
            'dagger': ['dagger', 'knife', 'kris', 'dirk', 'blade of the unmaker', 'rathrak', 'poisonous mind', 'electrowing dagger', 'scalpel of unrelenting agony'],
            'fist': ['fist', 'claw', 'knuckle'],
            'polearm': ['polearm', 'halberd', 'pike', 'kiril', 'fury of beasts'],
            'staff': ['staff', 'ti\'tahk', 'steps of time', 'lightning rod', 'spire of coagulated globules', 'visage of the destroyer'],
            'bow': ['bow', 'vishanka', 'jaws of the earth'],
            'crossbow': ['crossbow', 'horrifying horn arbalest'],
            'gun': ['gun', 'rifle', 'shotgun', 'ruinblaster shotgun'],
            'wand': ['wand', 'finger of zon\'ozz'],
            'thrown': ['thrown', 'razor saronite chip'],
            'shield': ['shield', 'blackhorn\'s mighty bulwark', 'timepiece of the bronze flight'],
            'off_hand': ['off-hand', 'held in off-hand', 'dragonfire orb', 'ledger of revolting rituals']
        }
        
        # Combine all weapon keywords for general weapon detection
        self.weapon_keywords = []
        for weapon_type, keywords in self.weapon_types.items():
            self.weapon_keywords.extend(keywords)
        
        # Jewelry keywords
        self.jewelry_keywords = []
        for slot in ['neck', 'finger', 'trinket']:
            self.jewelry_keywords.extend(self.slot_keywords[slot])
        
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
        
        # Specific item mappings for items that might be hard to categorize automatically
        self.specific_item_mappings = {
            # Madness weapons
            'vishanka, jaws of the earth': 'bow',
            'rathrak, the poisonous mind': 'dagger',
            'gurthalak, voice of the deeps': 'two_hand_sword',
            'ti\'tahk, the steps of time': 'staff',
            'kiril, fury of beasts': 'polearm',
            'souldrinker': 'one_hand_sword',
            'no\'kaled, the elements of death': 'one_hand_axe',
            'blade of the unmaker': 'dagger',
            'maw of the dragonlord': 'one_hand_mace',
            
            # Other specific items
            'hand of morchok': 'one_hand_axe',
            'vagaries of time': 'one_hand_mace',
            'razor saronite chip': 'thrown',
            'finger of zon\'ozz': 'wand',
            'horrifying horn arbalest': 'crossbow',
            'scalpel of unrelenting agony': 'dagger',
            'spire of coagulated globules': 'staff',
            'experimental specimen slicer': 'two_hand_axe',
            'electrowing dagger': 'dagger',
            'lightning rod': 'staff',
            'morningstar of heroic will': 'one_hand_mace',
            'ledger of revolting rituals': 'off_hand',
            'ataraxis, cudgel of the warmaster': 'two_hand_mace',
            'visage of the destroyer': 'staff',
            'blackhorn\'s mighty bulwark': 'shield',
            'timepiece of the bronze flight': 'shield',
            'ruinblaster shotgun': 'gun',
            'spine of the thousand cuts': 'one_hand_sword',
            'dragonfire orb': 'off_hand'
        }
        
    def normalize_name(self, name):
        """Normalize player names to handle case and special characters"""
        if pd.isna(name):
            return None
        
        # Convert to lowercase and strip whitespace
        normalized = name.lower().strip()
        
        # Manual name mapping
        if normalized in self.manual_mappings:
            normalized = self.manual_mappings[normalized]
            
        # Debug name for ricardo
        if normalized == 'ricardomìlos' or normalized == 'ricardo':
            print(f"DEBUG: normalizing {name} to {normalized}")
            
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
            print(f"    {orig} → {mapped}")
        
        print("  Auto-detected mappings:")
        for orig, mapped in self.name_mapping.items():
            print(f"    {orig} → {mapped}")
    
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
        if "Corrupted" not in item_name:
            return None, None
            
        # Extract token type
        token = None
        for token_type in ["Vanquisher", "Conqueror", "Protector"]:
            if token_type in item_name:
                token = token_type
                break
                
        if not token:
            return None, None
            
        # Extract token slot
        token_slot = 'unknown'
        if "Helm" in item_name or "Crown" in item_name:
            token_slot = 'head'
        elif "Shoulder" in item_name or "Spaulders" in item_name:
            token_slot = 'shoulder'
        elif "Chest" in item_name or "Robe" in item_name:
            token_slot = 'chest'
        elif "Gauntlet" in item_name or "Gloves" in item_name or "Hand" in item_name:
            token_slot = 'hands'
        elif "Leg" in item_name or "Kilt" in item_name or "Pants" in item_name:
            token_slot = 'legs'
            
        return token, token_slot
        
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
                        print(f"Mapped loot: {original_name} → {player_name}: {row['Item']}")
                    
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
                    
                    # Determine and track the item slot
                    item_slot = self.determine_item_slot(item_name)
                    if item_slot != 'unknown':
                        self.player_item_slots[player_name][item_slot] += 1
                        
                        # Debug slot detection for some items
                        debug_items = ['Bow', 'Vial', 'Voice of the Deeps', 'Steps of Time', 
                                      'Fury of Beasts', 'Souldrinker', 'Elements of Death', 
                                      'Unmaker', 'Dragonlord', 'Poisonous Mind', 'Jaws of the Earth']
                        debug_players = ['ricardo', 'albear', 'ooverdeath']
                        
                        if player_name in debug_players or any(keyword in item_name for keyword in debug_items):
                            print(f"  Item slot: {item_name} -> {item_slot} for {player_name}")
                    
                    # Categorize by item type (jewelry/weapon)
                    item_name_lower = item_name.lower()
                    
                    # Check if it's jewelry
                    if any(keyword in item_name_lower for keyword in self.jewelry_keywords):
                        self.player_jewelry_count[player_name] += 1
                        
                    # Check if it's a weapon
                    if any(keyword in item_name_lower for keyword in self.weapon_keywords):
                        self.player_weapon_count[player_name] += 1
    
    def calculate_attendance(self):
        """Calculate attendance percentage for each player based on boss kills"""
        attendance_percentage = {}
        
        for player, bosses_attended in self.player_boss_attendance.items():
            # Calculate raw attendance
            base_attendance = (bosses_attended / self.total_bosses) * 100
            
            # Apply 25-man bonus if applicable
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
                attendance_percentage[player] = base_attendance * (1 + (self.raid_25_percent_bonus * bonus_portion))
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
        # Debug attendance for key players
        if self.debug_config['show_attendance']:
            print("\nAttendance for key players:")
            for player in self.debug_config['players']:
                if player in attendance:
                    print(f"  {player}: {attendance[player]:.1f}%")
        
        # Print loot per boss for key players
        if self.debug_config['show_loot_per_boss']:
            print("\nLoot per boss:")
            for player in sorted(loot_per_boss.keys(), key=lambda x: loot_per_boss[x]):
                if player in loot_per_boss:
                    print(f"  {player}: {loot_per_boss[player]:.4f} ({self.player_loot_count.get(player, 0)} items / {self.player_boss_attendance.get(player, 0)} bosses)")
        
        # Priority formula that considers:
        # 1. Boss attendance (higher = better)
        # 2. Loot per boss (lower = better)
        # 3. Item slot importance (weighted by slot category)
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
                
                # Print item slots for debugging
                if self.debug_config['show_item_slots'] and player in self.debug_config['players']:
                    print(f"\nItem slots for {player}:")
                    for slot, count in self.player_item_slots[player].items():
                        print(f"  {slot}: {count} items")
                
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
                        is_token_slot = False
                        if player_token in self.token_slot_importance and slot in self.token_slot_importance[player_token]:
                            is_token_slot = True
                            token_item_penalty += weighted_token_slot_penalty
                        else:
                            regular_item_penalty += weighted_slot_penalty
                        
                        # Debug output for specific players
                        if self.debug_config['show_priority_calculation'] and player in self.debug_config['players']:
                            slot_type = "token" if is_token_slot else "regular"
                            print(f"  - {slot} penalty ({slot_type}): {count}/{bosses_attended} * {self.item_penalty_multiplier} * {slot_multiplier} = {weighted_slot_penalty:.2f}")
                
                # Calculate 25-man bonus (now handled in attendance calculation)
                raid_size_bonus = 0  # Removed flat bonus as it's now in attendance
                
                # COMPLETELY REVISED CALCULATION:
                # For regular items: attendance - regular_penalty - (token_penalty * reduction)
                # For token items: attendance - token_penalty - (regular_penalty * reduction)
                
                # Calculate final priority scores
                regular_score = attendance_score - regular_item_penalty - (token_item_penalty * self.token_penalty_reduction) + raid_size_bonus
                token_score = attendance_score - token_item_penalty - (regular_item_penalty * self.token_penalty_reduction) + raid_size_bonus
                
                # Store both scores
                regular_priority_scores[player] = regular_score
                token_priority_scores[player] = token_score
                
                # Add explanation for specific players for debugging
                if self.debug_config['show_priority_calculation'] and player in self.debug_config['players']:
                    print(f"\nPriority calculation for {player}:")
                    print(f"  Attendance: {attendance.get(player, 0):.1f}% × {self.attendance_weight} = {attendance_score:.1f}")
                    
                    # UPDATED DEBUG OUTPUT to clarify the calculation
                    print(f"  Regular item priority calculation:")
                    print(f"    - Full regular item penalty: {regular_item_penalty:.1f}")
                    print(f"    - Reduced token penalty (50%): {token_item_penalty * self.token_penalty_reduction:.1f}")
                    print(f"    - Final regular priority: {attendance_score:.1f} - {regular_item_penalty:.1f} - {token_item_penalty * self.token_penalty_reduction:.1f} = {regular_score:.1f}")
                    
                    print(f"  Token item priority calculation:")
                    print(f"    - Full token item penalty: {token_item_penalty:.1f}")
                    print(f"    - Reduced regular penalty (50%): {regular_item_penalty * self.token_penalty_reduction:.1f}")
                    print(f"    - Final token priority: {attendance_score:.1f} - {token_item_penalty:.1f} - {regular_item_penalty * self.token_penalty_reduction:.1f} = {token_score:.1f}")
        
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
        token_classes = self.get_token_class_distribution()
        
        # Print slot value multipliers
        print("\nSlot Value Categories:")
        for category, slots in [
            ("Highest Value", [slot for slot, value in self.slot_categories.items() if value >= 1.5]),
            ("Medium-High Value", [slot for slot, value in self.slot_categories.items() if 1.3 <= value < 1.5]),
            ("Medium-Low Value", [slot for slot, value in self.slot_categories.items() if 1.1 <= value < 1.3]),
            ("Lowest Value", [slot for slot, value in self.slot_categories.items() if value <= 1.1])
        ]:
            print(f"  {category}: {', '.join(slots)}")
        
        # Print token-specific slot values
        print("\nToken-Specific Slot Values:")
        for token, slots in self.token_slot_importance.items():
            print(f"  {token}: {', '.join([f'{slot} ({value})' for slot, value in slots.items()])}")
        
        # Print total items distributed
        total_items = sum(self.player_loot_count.values())
        print(f"\nTotal Items Distributed: {total_items}")
        
        # Print token distribution
        token_counts = Counter()
        for player_tokens in self.player_token_count.values():
            for token, count in player_tokens.items():
                token_counts[token] += count
        
        print("Token Distribution:")
        for token, count in token_counts.items():
            print(f"  {token}: {count}")
        
        # Get loot priority recommendations
        recommendations = self.get_loot_priority_recommendations(attendance, loot_per_boss)
        
        print("\nLOOT PRIORITY RECOMMENDATIONS:")
        print("-"*120)
        print(f"{'Player':<15} {'Class':<10} {'Spec':<12} {'Role':<8} {'Token':<10} {'Stat':<10} {'Is Healer':<8} {'Attend':<8} {'Items':<6} {'Per Boss':<8} {'Tokens':<7} {'Priority'}")
        print("-"*120)
        
        for rec in recommendations:
            print(f"{rec['IGN']:<15} {rec['Class']:<10} {rec['Spec']:<12} {rec['Role']:<8} {rec['Token']:<10} "
                  f"{rec['Stat']:<10} {rec['Is Healer']:<8} {rec['Attendance']:<8} {rec['Items Received']:<6} "
                  f"{rec['Items Per Boss']:<8} {rec['Token Items']:<7} {rec['Priority Score']}")
        
        # Token-specific recommendations
        print("\nTOKEN-SPECIFIC PRIORITY RECOMMENDATIONS (TOP 10):")
        for token in ["Vanquisher", "Conqueror", "Protector"]:
            token_players = [r for r in recommendations if r['Token'] == token]
            if token_players:
                # Sort by token priority score instead of regular priority
                token_players.sort(key=lambda x: float(x['Token Priority Score Value']), reverse=True)
                print(f"\n{token} Token Priority:")
                for i, player in enumerate(token_players[:10], 1):
                    print(f"  {i}. {player['IGN']} ({player['Class']} - {player['Spec']}) - Score: {player['Token Priority Score']}")
        
        # Stat-based priority recommendations (Top 10)
        print("\nSTAT-BASED PRIORITY RECOMMENDATIONS (TOP 10):")
        
        # Healer priority
        healer_players = [r for r in recommendations if r['Role'] == 'Healer']
        if healer_players:
            # Sort by priority score
            healer_players.sort(key=lambda x: float(x['Priority Score Value']), reverse=True)
            print("\nHealer Priority:")
            for i, player in enumerate(healer_players[:10], 1):
                print(f"  {i}. {player['IGN']} ({player['Class']} - {player['Spec']}) - Score: {player['Priority Score']}")
        
        # Intellect user priority
        intellect_players = [r for r in recommendations if r['Stat'] == 'Intellect' and r['Role'] != 'Healer']
        if intellect_players:
            # Sort by priority score
            intellect_players.sort(key=lambda x: float(x['Priority Score Value']), reverse=True)
            print("\nIntellect User Priority (Non-Healers):")
            for i, player in enumerate(intellect_players[:10], 1):
                print(f"  {i}. {player['IGN']} ({player['Class']} - {player['Spec']}) - Score: {player['Priority Score']}")
        
        # Agility user priority
        agility_players = [r for r in recommendations if r['Stat'] == 'Agility']
        if agility_players:
            # Sort by priority score
            agility_players.sort(key=lambda x: float(x['Priority Score Value']), reverse=True)
            print("\nAgility User Priority:")
            for i, player in enumerate(agility_players[:10], 1):
                print(f"  {i}. {player['IGN']} ({player['Class']} - {player['Spec']}) - Score: {player['Priority Score']}")
        
        # Strength user priority
        strength_players = [r for r in recommendations if r['Stat'] == 'Strength']
        if strength_players:
            # Sort by priority score
            strength_players.sort(key=lambda x: float(x['Priority Score Value']), reverse=True)
            print("\nStrength User Priority:")
            for i, player in enumerate(strength_players[:10], 1):
                print(f"  {i}. {player['IGN']} ({player['Class']} - {player['Spec']}) - Score: {player['Priority Score']}")
        
        # Tank priority (special case)
        tank_players = [r for r in recommendations if r['Role'] in ['Main Tank', 'Offtank']]
        if tank_players:
            # Sort by priority score
            tank_players.sort(key=lambda x: float(x['Priority Score Value']), reverse=True)
            print("\nTank Priority:")
            for i, player in enumerate(tank_players, 1):
                print(f"  {i}. {player['IGN']} ({player['Class']} - {player['Spec']}) - Score: {player['Priority Score']}")
        
        # Players with zero loot
        zero_loot_players = [r for r in recommendations if r['Items Received'] == 0]
        if zero_loot_players:
            print("\nPLAYERS WITH ZERO LOOT:")
            for player in zero_loot_players:
                print(f"  • {player['IGN']} ({player['Class']} - {player['Spec']}) - Attendance: {player['Attendance']}")
        
        print("\n" + "="*120)
        print(f"{'END OF REPORT':^120}")
        print("="*120)

    def run_analysis(self):
        """Run the complete analysis and generate recommendations"""
        print("\nDRAGON SOUL LOOT COUNCIL ANALYSIS REPORT (ENHANCED)")
        print("=" * 60)
        print(f"Raid Reset: Monday 2502, Sunday 2402")
        print(f"Total Bosses: {self.total_bosses} (3 in 10-man, 6 in 25-man)")
        
        # Debug players to show detailed information for
        debug_players = ['ricardo', 'bestdk', 'borran', 'moruse', 'ooverdeath', 'albear']
        
        # Print full bosses attended for key players
        print("\nDetailed player attendance:")
        for player in debug_players:
            if player in self.player_boss_attendance:
                bosses = self.player_boss_attendance[player]
                raid_sizes = ", ".join(self.player_raid_size[player])
                print(f"  {player}: {bosses}/{self.total_bosses} bosses in raid size {raid_sizes}")
        
        # Print item details for key players
        print("\nDetailed item distribution:")
        for player in debug_players:
            regular_items = self.player_loot_count.get(player, 0) - sum(self.player_token_count[player].values())
            token_items = sum(self.player_token_count[player].values())
            jewelry_items = self.player_jewelry_count.get(player, 0)
            weapon_items = self.player_weapon_count.get(player, 0)
            print(f"  {player}: {self.player_loot_count.get(player, 0)} total items")
            print(f"    - Regular: {regular_items} (Non-special: {regular_items - jewelry_items - weapon_items}, Jewelry: {jewelry_items}, Weapons: {weapon_items})")
            print(f"    - Tokens: {token_items} ({', '.join(f'{t}: {c}' for t, c in self.player_token_count[player].items() if c > 0)})")
            
            # Print item slots for this player
            if self.player_item_slots[player]:
                print(f"    - Item slots: {', '.join(f'{slot}: {count}' for slot, count in self.player_item_slots[player].items())}")

        print("\nPriority Calculation Parameters:")
        print(f"  Attendance Weight: {self.attendance_weight}")
        print(f"  Item Penalty Multiplier: {self.item_penalty_multiplier}")
        print(f"  Token Penalty Reduction: {self.token_penalty_reduction}")
        print(f"  25-man Raid Bonus: {self.raid_25_percent_bonus*100}%")
        
        # Print item slot categories
        print("\nItem Slot Categories:")
        for category, slots in [
            ("Highest Value (1.5)", [slot for slot, value in self.slot_categories.items() if value >= 1.5]),
            ("Medium-High Value (1.3)", [slot for slot, value in self.slot_categories.items() if 1.3 <= value < 1.5]),
            ("Medium-Low Value (1.2)", [slot for slot, value in self.slot_categories.items() if 1.1 <= value < 1.3]),
            ("Low Value (1.1)", [slot for slot, value in self.slot_categories.items() if 1.0 < value < 1.1]),
            ("Lowest Value (1.0)", [slot for slot, value in self.slot_categories.items() if value <= 1.0])
        ]:
            print(f"  {category}: {', '.join(slots)}")
            
        # Print weapon types
        print("\nWeapon Types:")
        for weapon_type in sorted(self.weapon_types.keys()):
            print(f"  {weapon_type.replace('_', ' ').title()}")
            
        # Print token slot importance
        print("\nToken Slot Importance:")
        for token, slots in self.token_slot_importance.items():
            print(f"  {token}: {', '.join(f'{slot} ({value})' for slot, value in slots.items())}")
            
        # Print specific item mappings count
        print(f"\nSpecific Item Mappings: {len(self.specific_item_mappings)} items")

    def determine_item_slot(self, item_name):
        """Determine the slot of an item based on its name"""
        if not item_name:
            return 'unknown'
            
        item_name_lower = item_name.lower()
        
        # First check specific item mappings
        if item_name_lower in self.specific_item_mappings:
            specific_type = self.specific_item_mappings[item_name_lower]
            
            # Map weapon types to the general 'weapon' category
            if specific_type in self.weapon_types:
                return 'weapon'
                
            # For other specific mappings, return the slot directly
            return specific_type
        
        # Check if it's a token
        token, token_slot = self.extract_token_info(item_name)
        if token and token_slot != 'unknown':
            return token_slot
        
        # Check if it's a trinket (special category)
        if any(keyword in item_name_lower for keyword in self.slot_keywords['trinket']):
            return 'trinket'
            
        # Check if it's a weapon
        for weapon_type, keywords in self.weapon_types.items():
            if any(keyword in item_name_lower for keyword in keywords):
                # For ranged weapons and off-hands, use their specific categories
                if weapon_type in ['bow', 'gun', 'crossbow', 'wand', 'thrown']:
                    return 'ranged'
                elif weapon_type in ['shield', 'off_hand']:
                    return 'off-hand'
                else:
                    return 'weapon'
        
        # Check each slot based on keywords
        for slot, keywords in self.slot_keywords.items():
            if any(keyword in item_name_lower for keyword in keywords):
                return slot
        
        # Default to a generic slot if we can't determine it
        return 'unknown'

    def verify_all_items_classification(self, items_list):
        """
        Verify that all items in the provided list are properly classified.
        Returns a list of items that couldn't be classified (unknown slot).
        """
        if not self.debug_config['enabled']:
            return []
            
        print("\nVERIFYING CLASSIFICATION FOR ALL ITEMS:")
        print("-" * 60)
        
        # Group items by category for better organization
        categorized_items = {
            'Madness Weapons': [],
            'Other Weapons': [],
            'Trinkets': [],
            'Armor': [],
            'Jewelry': [],
            'Tokens': [],
            'Other': []
        }
        
        # Categorize items
        for item in items_list:
            item_lower = item.lower()
            
            # Check if it's a madness weapon
            if any(madness_name in item_lower for madness_name in [
                'vishanka', 'jaws of the earth', 'rathrak', 'poisonous mind', 
                'gurthalak', 'voice of the deeps', 'ti\'tahk', 'steps of time',
                'kiril', 'fury of beasts', 'souldrinker', 'no\'kaled', 'elements of death',
                'blade of the unmaker', 'maw of the dragonlord'
            ]):
                categorized_items['Madness Weapons'].append(item)
            # Check if it's a token
            elif 'corrupted' in item_lower and any(token in item for token in ['Vanquisher', 'Conqueror', 'Protector']):
                categorized_items['Tokens'].append(item)
            # Check if it's a trinket
            elif any(keyword in item_lower for keyword in self.slot_keywords['trinket']):
                categorized_items['Trinkets'].append(item)
            # Check if it's a weapon
            elif any(keyword in item_lower for keyword in self.weapon_keywords):
                categorized_items['Other Weapons'].append(item)
            # Check if it's jewelry
            elif any(keyword in item_lower for keyword in self.jewelry_keywords):
                categorized_items['Jewelry'].append(item)
            # Check if it's armor
            elif any(keyword in item_lower for keyword in [
                'helm', 'hood', 'crown', 'shoulder', 'spaulder', 'chest', 'robe', 'wrist', 'bracer',
                'glove', 'gauntlet', 'belt', 'waist', 'leg', 'pant', 'boot', 'feet', 'treads'
            ]):
                categorized_items['Armor'].append(item)
            else:
                categorized_items['Other'].append(item)
        
        # Debug each category
        all_unknown_items = []
        for category, items in categorized_items.items():
            if items:  # Only process non-empty categories
                results = self.debug_item_classification(items, category)
                unknown_items = [r['item'] for r in results if r['slot'] == 'unknown']
                all_unknown_items.extend(unknown_items)
        
        # Print classification summary
        print("\nCLASSIFICATION SUMMARY:")
        total_items = len(items_list)
        classified_items = total_items - len(all_unknown_items)
        print(f"  Total items: {total_items}")
        print(f"  Successfully classified: {classified_items} ({classified_items/total_items*100:.1f}%)")
        print(f"  Unclassified: {len(all_unknown_items)} ({len(all_unknown_items)/total_items*100:.1f}%)")
        
        if all_unknown_items:
            print("\nUNCLASSIFIED ITEMS:")
            for item in all_unknown_items:
                print(f"  - {item}")
        else:
            print("\nSUCCESS: All items were successfully classified!")
        
        return all_unknown_items

    def verify_item_classification(self, item_name):
        """
        Verify the classification of a single item and return detailed information.
        
        Args:
            item_name: The name of the item to classify
            
        Returns:
            dict: A dictionary containing classification details
        """
        item_name_lower = item_name.lower()
        slot = self.determine_item_slot(item_name)
        
        # Check if it's in specific mappings
        in_specific_mappings = item_name_lower in self.specific_item_mappings
        
        # Check if it's a token
        token, token_slot = self.extract_token_info(item_name)
        is_token = token is not None
        
        # Check if it's a weapon
        is_weapon = False
        weapon_type = None
        for wtype, keywords in self.weapon_types.items():
            if any(keyword in item_name_lower for keyword in keywords):
                is_weapon = True
                weapon_type = wtype
                break
        
        # Check if it's jewelry
        is_jewelry = any(keyword in item_name_lower for keyword in self.jewelry_keywords)
        
        # Determine classification method
        classification_method = "unknown"
        if in_specific_mappings:
            classification_method = "specific_mapping"
        elif is_token and token_slot != 'unknown':
            classification_method = "token"
        elif is_weapon:
            classification_method = "weapon_keywords"
        elif slot != 'unknown':
            classification_method = "slot_keywords"
            
        return {
            'item': item_name,
            'slot': slot,
            'in_specific_mappings': in_specific_mappings,
            'is_token': is_token,
            'token_type': token,
            'token_slot': token_slot,
            'is_weapon': is_weapon,
            'weapon_type': weapon_type,
            'is_jewelry': is_jewelry,
            'classification_method': classification_method
        }

    def debug_item_classification(self, items_list, category_name=None):
        """
        Debug the classification of a list of items.
        
        Args:
            items_list: List of item names to classify
            category_name: Optional name of the category for display purposes
        """
        if not self.debug_config['enabled']:
            return
            
        if category_name:
            print(f"\n{category_name}:")
        
        results = []
        unknown_items = []
        
        for item in items_list:
            classification = self.verify_item_classification(item)
            results.append(classification)
            
            if classification['slot'] == 'unknown':
                unknown_items.append(item)
            
            # Print basic or verbose output based on configuration
            if self.debug_config['verbose_item_classification']:
                print(f"  {item}:")
                print(f"    Slot: {classification['slot']}")
                print(f"    Method: {classification['classification_method']}")
                if classification['is_token']:
                    print(f"    Token: {classification['token_type']} ({classification['token_slot']})")
                if classification['is_weapon']:
                    print(f"    Weapon Type: {classification['weapon_type']}")
            else:
                print(f"  {item} -> {classification['slot']}")
        
        # Print summary
        if unknown_items:
            print(f"  WARNING: {len(unknown_items)} items could not be classified:")
            for item in unknown_items:
                print(f"    - {item}")
        
        return results

    def update_specific_item_mappings(self):
        """
        Update specific item mappings with commonly unclassified items.
        This method adds mappings for items that are frequently not classified correctly.
        """
        # Add trinket mappings
        trinket_mappings = {
            'cunning of the cruel': 'trinket',
            'indomitable pride': 'trinket',
            'soulshifter vortex': 'trinket',
            'creche of the final dragon': 'trinket',
            'starcatcher compass': 'trinket',
            'eye of unmaking': 'trinket',
            'heart of unliving': 'trinket',
            'resolve of undying': 'trinket',
            'will of unbinding': 'trinket',
            'wrath of unchaining': 'trinket',
            'insignia of the corrupted mind': 'trinket',
            'seal of the seven signs': 'trinket'
        }
        
        # Add jewelry mappings
        jewelry_mappings = {
            'petrified fungal heart': 'neck',
            'curled twilight claw': 'finger',
            'ring of the riven': 'finger',
            'signet of grasping mouths': 'finger'
        }
        
        # Add armor mappings
        armor_mappings = {
            'imperfect specimens 27 and 28': 'shoulder',
            'nightblind cinch': 'waist',
            'interrogator\'s bloody footpads': 'feet',
            'mindstrainer treads': 'feet',
            'heartblood wristplates': 'wrist',
            'treads of sordid screams': 'feet',
            'bracers of looming darkness': 'wrist',
            'janglespur jackboots': 'feet',
            'shadow wing armbands': 'wrist',
            'belt of the beloved companion': 'waist',
            'goriona\'s collar': 'waist',
            'gloves of liquid smoke': 'hands',
            'molten blood footpads': 'feet',
            'belt of shattered elementium': 'waist',
            'backbreaker spaulders': 'shoulder',
            'gauntlets of the golden thorn': 'hands'
        }
        
        # Update the specific item mappings
        self.specific_item_mappings.update(trinket_mappings)
        self.specific_item_mappings.update(jewelry_mappings)
        self.specific_item_mappings.update(armor_mappings)
        
        # Print update summary if debug is enabled
        if self.debug_config['enabled']:
            print("\nUpdated specific item mappings:")
            print(f"  Added {len(trinket_mappings)} trinket mappings")
            print(f"  Added {len(jewelry_mappings)} jewelry mappings")
            print(f"  Added {len(armor_mappings)} armor mappings")
            print(f"  Total specific mappings: {len(self.specific_item_mappings)}")

if __name__ == "__main__":
    analyzer = DragonSoulLootAnalyzer()
    
    # Update specific item mappings to improve classification
    analyzer.update_specific_item_mappings()
    
    # Define item categories for testing
    item_categories = {
        'Madness Weapons': [
            "Vishanka, Jaws of the Earth", "Rathrak, the Poisonous Mind", 
            "Gurthalak, Voice of the Deeps", "Ti'tahk, the Steps of Time",
            "Kiril, Fury of Beasts", "Souldrinker", "No'Kaled, the Elements of Death",
            "Blade of the Unmaker", "Maw of the Dragonlord"
        ],
        'Other Weapons': [
            "Hand of Morchok", "Vagaries of Time", "Razor Saronite Chip",
            "Finger of Zon'ozz", "Horrifying Horn Arbalest", "Scalpel of Unrelenting Agony",
            "Spire of Coagulated Globules", "Experimental Specimen Slicer",
            "Electrowing Dagger", "Lightning Rod", "Morningstar of Heroic Will",
            "Ledger of Revolting Rituals", "Ataraxis, Cudgel of the Warmaster",
            "Visage of the Destroyer", "Blackhorn's Mighty Bulwark",
            "Timepiece of the Bronze Flight", "Ruinblaster Shotgun",
            "Spine of the Thousand Cuts", "Dragonfire Orb"
        ],
        'Trinkets': [
            "Bone-Link Fetish", "Cunning of the Cruel", "Indomitable Pride",
            "Vial of Shadows", "Windward Heart", "Seal of the Seven Signs",
            "Insignia of the Corrupted Mind", "Soulshifter Vortex",
            "Creche of the Final Dragon", "Starcatcher Compass",
            "Eye of Unmaking", "Heart of Unliving", "Resolve of Undying",
            "Will of Unbinding", "Wrath of Unchaining"
        ],
        'Armor': [
            "Mosswrought Shoulderguards", "Robe of Glowing Stone",
            "Mycosynth Wristguards", "Underdweller's Spaulders",
            "Girdle of Shattered Stone", "Sporebeard Gauntlets",
            "Brackenshell Shoulderplates", "Pillarfoot Greaves",
            "Rockhide Bracers", "Cord of the Slain Champion",
            "Belt of Flayed Skin", "Grotesquely Writhing Bracers",
            "Graveheart Bracers", "Treads of Crushed Flesh",
            "Bracers of the Banished", "Girdle of the Grotesque",
            "Treads of Dormant Dreams", "Runescriven Demon Collar",
            "Treads of Sordid Screams", "Bracers of Looming Darkness",
            "Imperfect Specimens 27 and 28", "Dragonfracture Belt",
            "Stillheart Warboots", "Janglespur Jackboots",
            "Shadow Wing Armbands", "Belt of the Beloved Companion",
            "Goriona's Collar", "Gloves of Liquid Smoke",
            "Molten Blood Footpads", "Belt of Shattered Elementium",
            "Backbreaker Spaulders", "Gauntlets of the Golden Thorn"
        ],
        'Jewelry': [
            "Petrified Fungal Heart", "Breathstealer Band", "Hardheart Ring",
            "Infinite Loop", "Seal of Primordial Shadow", "Signet of Suturing",
            "Ring of the Riven", "Signet of Grasping Mouths", "Curled Twilight Claw"
        ]
    }
    
    # Comprehensive list of Dragon Soul items
    dragon_soul_items = []
    for category, items in item_categories.items():
        dragon_soul_items.extend(items)
    
    # Add BoE items
    boe_items = [
        "Sash of Relentless Truth", "Nightblind Cinch", "Girdle of Fungal Dreams",
        "Dragoncarver Belt", "Belt of Ghostly Graces", "Girdle of Soulful Mending",
        "Waistguard of Bleeding Bone", "Waistplate of the Desecrated Future"
    ]
    dragon_soul_items.extend(boe_items)
    
    # Add additional items
    additional_items = [
        "Interrogator's Bloody Footpads", "Mindstrainer Treads", "Heartblood Wristplates"
    ]
    dragon_soul_items.extend(additional_items)
    
    print("\nDEBUG ITEM CLASSIFICATION SYSTEM")
    print("=" * 40)
    
    # Test the debug system with different configurations
    if analyzer.debug_config['enabled']:
        # Option 1: Test all items at once
        if analyzer.debug_config['item_categories']['madness_weapons']:
            analyzer.debug_item_classification(item_categories['Madness Weapons'], "Madness Weapons")
            
        if analyzer.debug_config['item_categories']['other_weapons']:
            analyzer.debug_item_classification(item_categories['Other Weapons'], "Other Weapons")
            
        if analyzer.debug_config['item_categories']['trinkets']:
            analyzer.debug_item_classification(item_categories['Trinkets'], "Trinkets")
            
        if analyzer.debug_config['item_categories']['armor']:
            analyzer.debug_item_classification(item_categories['Armor'], "Armor")
            
        if analyzer.debug_config['item_categories']['jewelry']:
            analyzer.debug_item_classification(item_categories['Jewelry'], "Jewelry")
        
        # Option 2: Verify all items at once
        print("\nTesting comprehensive verification:")
        analyzer.verify_all_items_classification(dragon_soul_items)
    
    # Run the full analysis
    print("\n")
    analyzer.analyze_and_print_report() 