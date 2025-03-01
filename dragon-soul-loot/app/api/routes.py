from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

# Import our loot analyzer adapter
from loot_analyzer_adapter import loot_analyzer_adapter

# Import WebSocket broadcasting functions
from .websocket import broadcast_raid_status, broadcast_loot_assignment, broadcast_priorities

router = APIRouter(prefix="/api", tags=["loot"])

# In-memory storage for active raid session
active_raid_session = {
    "active": False,
    "start_time": None,
    "current_boss": None,
    "participants": [],
    "loot_assignments": []
}

@router.get("/priorities")
async def get_priorities(
    background_tasks: BackgroundTasks,
    token_type: Optional[str] = Query(None, description="Filter by token type (Vanquisher, Conqueror, Protector)"),
    stat: Optional[str] = Query(None, description="Filter by primary stat (Strength, Agility, Intellect)"),
    role: Optional[str] = Query(None, description="Filter by role (DPS, Healer, Tank)")
):
    """Get current loot priorities with optional filtering"""
    try:
        # Get recommendations from adapter
        recommendations = loot_analyzer_adapter.get_loot_priority_recommendations()
        
        # Apply filters if provided
        filtered_recommendations = recommendations
        if token_type:
            filtered_recommendations = [r for r in filtered_recommendations if r['Token'].lower() == token_type.lower()]
        if stat:
            filtered_recommendations = [r for r in filtered_recommendations if r['Stat'].lower() == stat.lower()]
        if role:
            filtered_recommendations = [r for r in filtered_recommendations if role.lower() in r['Role'].lower()]
        
        # Broadcast updated priorities
        background_tasks.add_task(broadcast_priorities, filtered_recommendations)
        
        return {
            "status": "success",
            "data": filtered_recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating priorities: {str(e)}")

@router.get("/players")
async def get_players():
    """Get all players with their information"""
    try:
        # Get player info from adapter
        player_info = loot_analyzer_adapter.get_player_info()
            
        players = []
        for player_name, info in player_info.items():
            players.append({
                "name": player_name,
                "display_name": info.get('Original_IGN', player_name),
                "class": info.get('Class', 'Unknown'),
                "spec": info.get('Spec', 'Unknown'),
                "role": info.get('Role', 'Unknown'),
                "token": info.get('Token', 'Unknown'),
                "primary_stat": info.get('Primary_Stat', 'Unknown')
            })
            
        return {
            "status": "success",
            "data": players
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving players: {str(e)}")

@router.get("/items")
async def get_items(
    slot: Optional[str] = Query(None, description="Filter by item slot"),
    token: Optional[bool] = Query(None, description="Filter for token items only")
):
    """Get all items from the loot table with optional filtering"""
    try:
        # Get loot history from adapter
        loot_history = loot_analyzer_adapter.get_loot_history()
        
        # Extract unique items
        unique_items = {}
        for loot in loot_history:
            item_name = loot.get('item', '')
            item_type = loot.get('item_type', '')
            item_slot = loot.get('item_slot', '')
            
            if not item_name:
                continue
                
            # Create a unique key for the item
            item_key = item_name.lower()
            
            # Only add if not already in unique_items
            if item_key not in unique_items:
                unique_items[item_key] = {
                    "name": item_name,
                    "slot": item_slot,
                    "type": item_type
                }
                
                # Add token type if applicable
                if item_type == 'token':
                    token_info = loot_analyzer_adapter.loot_analyzer.extract_token_info(item_name)
                    if token_info:
                        token_type, _ = token_info
                        unique_items[item_key]["token_type"] = token_type
        
        # Convert to list
        items = list(unique_items.values())
        
        # Apply filters
        if token is not None:
            items = [item for item in items if (item['type'] == 'token') == token]
            
        if slot:
            items = [item for item in items if item['slot'].lower() == slot.lower()]
            
        return {
            "status": "success",
            "data": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving items: {str(e)}")

@router.post("/raid/start")
async def start_raid(
    background_tasks: BackgroundTasks,
    boss_name: str,
    participants: List[str]
):
    """Start a new raid session"""
    global active_raid_session
    
    try:
        # Check if there's already an active raid
        if active_raid_session["active"]:
            return {
                "status": "error",
                "message": "There is already an active raid session. End it first."
            }
            
        # Start new raid session
        active_raid_session = {
            "active": True,
            "start_time": datetime.now().isoformat(),
            "current_boss": boss_name,
            "participants": participants,
            "loot_assignments": []
        }
        
        # Broadcast raid status update
        background_tasks.add_task(broadcast_raid_status, active_raid_session)
        
        return {
            "status": "success",
            "message": f"Raid started on {boss_name} with {len(participants)} participants",
            "data": active_raid_session
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting raid: {str(e)}")

@router.post("/raid/end")
async def end_raid(background_tasks: BackgroundTasks):
    """End the current raid session and save data"""
    global active_raid_session
    
    try:
        # Check if there's an active raid
        if not active_raid_session["active"]:
            return {
                "status": "error",
                "message": "There is no active raid session."
            }
            
        # Save raid data
        raid_data = active_raid_session.copy()
        raid_data["end_time"] = datetime.now().isoformat()
        
        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raid_session_{timestamp}.json"
        
        # Ensure the data directory exists
        os.makedirs("data/raid_logs", exist_ok=True)
        
        # Save to file
        with open(f"data/raid_logs/{filename}", "w") as f:
            json.dump(raid_data, f, indent=2)
            
        # Reset active raid
        active_raid_session = {
            "active": False,
            "start_time": None,
            "current_boss": None,
            "participants": [],
            "loot_assignments": []
        }
        
        # Broadcast raid status update
        background_tasks.add_task(broadcast_raid_status, active_raid_session)
        
        return {
            "status": "success",
            "message": f"Raid ended and data saved to {filename}",
            "data": raid_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending raid: {str(e)}")

@router.post("/loot/assign")
async def assign_loot(
    background_tasks: BackgroundTasks,
    item_name: str,
    player_name: str,
    boss_name: Optional[str] = None
):
    """Assign a loot item to a player"""
    global active_raid_session
    
    try:
        # Check if there's an active raid
        if not active_raid_session["active"]:
            return {
                "status": "error",
                "message": "There is no active raid session."
            }
            
        # Get current boss if not specified
        current_boss = boss_name if boss_name else active_raid_session["current_boss"]
        
        # Create loot assignment
        loot_assignment = {
            "item": item_name,
            "player": player_name,
            "boss": current_boss,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to active raid
        active_raid_session["loot_assignments"].append(loot_assignment)
        
        # Broadcast loot assignment
        background_tasks.add_task(broadcast_loot_assignment, loot_assignment)
        
        # TODO: Update loot data in analyzer (future enhancement)
        
        return {
            "status": "success",
            "message": f"Item {item_name} assigned to {player_name}",
            "data": loot_assignment
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning loot: {str(e)}")

@router.get("/raid/status")
async def get_raid_status():
    """Get the status of the current raid session"""
    return {
        "status": "success",
        "data": active_raid_session
    }

@router.put("/raid/boss")
async def update_current_boss(
    background_tasks: BackgroundTasks,
    boss_name: str
):
    """Update the current boss in the active raid session"""
    global active_raid_session
    
    try:
        # Check if there's an active raid
        if not active_raid_session["active"]:
            return {
                "status": "error",
                "message": "There is no active raid session."
            }
            
        # Update boss
        active_raid_session["current_boss"] = boss_name
        
        # Broadcast raid status update
        background_tasks.add_task(broadcast_raid_status, active_raid_session)
        
        return {
            "status": "success",
            "message": f"Current boss updated to {boss_name}",
            "data": active_raid_session
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating boss: {str(e)}")

@router.get("/stats")
async def get_loot_stats():
    """Get overall loot statistics"""
    try:
        # Get stats from adapter
        stats = loot_analyzer_adapter.get_loot_stats()
                
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

@router.get("/history")
async def get_loot_history(
    player: Optional[str] = Query(None, description="Filter by player name"),
    item_type: Optional[str] = Query(None, description="Filter by item type (token, gear)"),
    raid_type: Optional[str] = Query(None, description="Filter by raid type (10man, 25man)")
):
    """Get loot history with optional filtering"""
    try:
        # Get loot history from adapter
        loot_history = loot_analyzer_adapter.get_loot_history()
        
        # Apply filters
        if player:
            loot_history = [loot for loot in loot_history if player.lower() in loot.get('player', '').lower()]
            
        if item_type:
            loot_history = [loot for loot in loot_history if loot.get('item_type', '').lower() == item_type.lower()]
            
        if raid_type:
            loot_history = [loot for loot in loot_history if raid_type.lower() in loot.get('raid_type', '').lower()]
            
        return {
            "status": "success",
            "data": loot_history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving loot history: {str(e)}")

@router.get("/sessions")
async def get_raid_sessions(
    raid_type: Optional[str] = Query(None, description="Filter by raid type (10man, 25man)"),
    boss: Optional[str] = Query(None, description="Filter by boss name"),
    date: Optional[str] = Query(None, description="Filter by date")
):
    """Get raid sessions with optional filtering"""
    try:
        # Get raid sessions from adapter
        raid_sessions = loot_analyzer_adapter.get_raid_sessions()
        
        # Apply filters
        if raid_type:
            raid_sessions = [session for session in raid_sessions if raid_type.lower() in session.get('raid_type', '').lower()]
            
        if boss:
            raid_sessions = [session for session in raid_sessions if boss.lower() in session.get('boss', '').lower()]
            
        if date:
            raid_sessions = [session for session in raid_sessions if date.lower() in session.get('date', '').lower()]
            
        return {
            "status": "success",
            "data": raid_sessions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving raid sessions: {str(e)}")

@router.post("/process-data")
async def process_data():
    """Process CSV data files and generate JSON data files"""
    try:
        from process_data import main as process_data_main
        process_data_main()
        
        # Reload data in adapter
        loot_analyzer_adapter.load_data()
        
        return {
            "status": "success",
            "message": "Data processing completed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}") 