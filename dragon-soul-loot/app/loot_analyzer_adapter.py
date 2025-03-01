import os
import json
from typing import Dict, List, Any, Optional
from loot_analysis_enhanced import DragonSoulLootAnalyzer

class LootAnalyzerAdapter:
    """
    Adapter class to integrate processed JSON data with the DragonSoulLootAnalyzer
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the adapter
        
        Args:
            data_dir: Directory containing processed JSON data
        """
        self.data_dir = data_dir
        self.loot_analyzer = DragonSoulLootAnalyzer(data_dir=data_dir)
        
        # Paths to JSON files
        self.player_info_path = os.path.join(data_dir, "player_info.json")
        self.loot_history_path = os.path.join(data_dir, "loot_history.json")
        self.raid_sessions_path = os.path.join(data_dir, "raid_sessions.json")
        
        # Check if JSON files exist
        self._check_data_files()
        
    def _check_data_files(self):
        """Check if required JSON files exist"""
        missing_files = []
        
        if not os.path.exists(self.player_info_path):
            missing_files.append("player_info.json")
        
        if not os.path.exists(self.loot_history_path):
            missing_files.append("loot_history.json")
        
        if not os.path.exists(self.raid_sessions_path):
            missing_files.append("raid_sessions.json")
        
        if missing_files:
            print(f"Warning: The following data files are missing: {', '.join(missing_files)}")
            print("Run the data processor first to generate these files.")
    
    def load_data(self):
        """Load data from JSON files into the loot analyzer"""
        # Load player info
        if os.path.exists(self.player_info_path):
            with open(self.player_info_path, 'r', encoding='utf-8') as f:
                self.loot_analyzer.player_info = json.load(f)
        
        # Load loot history and process it
        if os.path.exists(self.loot_history_path):
            with open(self.loot_history_path, 'r', encoding='utf-8') as f:
                loot_history = json.load(f)
                
                # Process loot history
                for loot in loot_history:
                    player_name = loot.get('player', '')
                    item_name = loot.get('item', '')
                    item_type = loot.get('item_type', '')
                    item_slot = loot.get('item_slot', '')
                    
                    if player_name and item_name:
                        # Update player loot count
                        self.loot_analyzer.player_loot_count[player_name] += 1
                        
                        # Update player item slots
                        if item_slot != 'unknown':
                            self.loot_analyzer.player_item_slots[player_name][item_slot] += 1
                        
                        # Update token counts if applicable
                        if item_type == 'token':
                            # Extract token type from item name
                            token_info = self.loot_analyzer.extract_token_info(item_name)
                            if token_info:
                                token_type, _ = token_info
                                self.loot_analyzer.player_token_count[player_name][token_type] += 1
        
        # Load raid sessions and process them
        if os.path.exists(self.raid_sessions_path):
            with open(self.raid_sessions_path, 'r', encoding='utf-8') as f:
                raid_sessions = json.load(f)
                
                # Process raid sessions for attendance
                for session in raid_sessions:
                    raid_type = session.get('raid_type', '')
                    boss = session.get('boss', '')
                    participants = session.get('participants', [])
                    
                    # Determine number of bosses in this session
                    bosses_count = 0
                    if '25man_58' in raid_type:
                        bosses_count = 5
                    elif '10man_war_spine' in raid_type:
                        bosses_count = 2
                    elif '10man_madness' in raid_type:
                        bosses_count = 1
                    else:
                        # Default to 1 if unknown
                        bosses_count = 1
                    
                    # Update player boss attendance
                    for player in participants:
                        self.loot_analyzer.player_boss_attendance[player] += bosses_count
                        
                        # Update player raid size
                        if '25man' in raid_type:
                            self.loot_analyzer.player_raid_size[player].add('25')
                        elif '10man' in raid_type:
                            self.loot_analyzer.player_raid_size[player].add('10')
    
    def get_loot_priority_recommendations(self):
        """Get loot priority recommendations"""
        # Ensure data is loaded
        if not self.loot_analyzer.player_info:
            self.load_data()
        
        # Calculate attendance and loot per boss
        attendance = self.loot_analyzer.calculate_attendance()
        loot_per_boss = self.loot_analyzer.calculate_loot_per_boss()
        
        # Get recommendations
        return self.loot_analyzer.get_loot_priority_recommendations(attendance, loot_per_boss)
    
    def get_player_info(self):
        """Get player information"""
        # Ensure data is loaded
        if not self.loot_analyzer.player_info:
            self.load_data()
        
        return self.loot_analyzer.player_info
    
    def get_loot_history(self):
        """Get loot history"""
        if os.path.exists(self.loot_history_path):
            with open(self.loot_history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def get_raid_sessions(self):
        """Get raid sessions"""
        if os.path.exists(self.raid_sessions_path):
            with open(self.raid_sessions_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def get_loot_stats(self):
        """Get loot statistics"""
        # Ensure data is loaded
        if not self.loot_analyzer.player_loot_count:
            self.load_data()
        
        # Calculate basic stats
        total_items = sum(self.loot_analyzer.player_loot_count.values())
        
        # Token distribution
        token_counts = {}
        for player_tokens in self.loot_analyzer.player_token_count.values():
            for token, count in player_tokens.items():
                if token not in token_counts:
                    token_counts[token] = 0
                token_counts[token] += count
        
        # Slot distribution
        slot_counts = {}
        for player, slots in self.loot_analyzer.player_item_slots.items():
            for slot, count in slots.items():
                if slot not in slot_counts:
                    slot_counts[slot] = 0
                slot_counts[slot] += count
        
        return {
            "total_items": total_items,
            "token_distribution": token_counts,
            "slot_distribution": slot_counts
        }

# Create a singleton instance
loot_analyzer_adapter = LootAnalyzerAdapter() 