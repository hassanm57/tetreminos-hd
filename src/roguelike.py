# roguelike.py - Sector Protocol and Relic Progression System
# Written clearly with simple classes and dicts so any engineer can follow.

import random

# List of all available relics/augments in the game
ALL_RELICS = [
    {
        'id': 'VOLATILE_CATALYST',
        'name': 'Volatile Catalyst',
        'icon': '💥',
        'rarity': 'Rare',
        'desc': '💣 Bomb blocks have their blast radius increased to 5x5!'
    },
    {
        'id': 'SUPERCONDUCTOR',
        'name': 'Superconductor',
        'icon': '⚡',
        'rarity': 'Uncommon',
        'desc': '⚡ Lightning blocks grant +1,000 bonus score on trigger.'
    },
    {
        'id': 'FLUX_CAPACITOR',
        'name': 'Flux Capacitor',
        'icon': '🧲',
        'rarity': 'Common',
        'desc': '🧲 Magnet blocks pull from 5 rows away and award +200 score per block.'
    },
    {
        'id': 'CHRONO_OVERCLOCK',
        'name': 'Chrono Overclock',
        'icon': '🧊',
        'rarity': 'Rare',
        'desc': '🧊 Freeze blocks last 14 seconds instead of 8 seconds.'
    },
    {
        'id': 'GRAVITON_CONDENSER',
        'name': 'Graviton Condenser',
        'icon': '⚓',
        'rarity': 'Common',
        'desc': 'Hard drops cause floating blocks below to settle into empty gaps.'
    },
    {
        'id': 'RESONANCE_CASCADE',
        'name': 'Resonance Cascade',
        'icon': '🎵',
        'rarity': 'Uncommon',
        'desc': 'Each combo step awards +200 bonus score multiplied by current level.'
    },
    {
        'id': 'EMERGENCY_PURGE',
        'name': 'Emergency Purge',
        'icon': '🚨',
        'rarity': 'Rare',
        'desc': 'When blocks reach the danger zone (row 18+), bottom 3 rows are wiped once per sector.'
    }
]

# Sectors definition
SECTORS = [
    {
        'sector': 1,
        'name': 'Sector 01: Subnet Gateway',
        'lines_needed': 15,
        'hazard_desc': 'System initialization. Standard grid conditions.',
        'speed_mult': 1.0
    },
    {
        'sector': 2,
        'name': 'Sector 02: Neon Firewall',
        'lines_needed': 20,
        'hazard_desc': 'Firewall active: Higher spawn rate of Burning thermite blocks.',
        'speed_mult': 1.15
    },
    {
        'sector': 3,
        'name': 'Sector 03: Data Flow Stream',
        'lines_needed': 25,
        'hazard_desc': 'Turbulent data: Increased piece descent velocity.',
        'speed_mult': 1.35
    },
    {
        'sector': 4,
        'name': 'Sector 04: Rogue AI Node',
        'lines_needed': 30,
        'hazard_desc': 'EMP pulses: Corrupted blocks spawn periodically.',
        'speed_mult': 1.55
    },
    {
        'sector': 5,
        'name': 'Sector 05: Core Mainframe',
        'lines_needed': 35,
        'hazard_desc': 'Final Sector: Overclocked speed and maximum hazards!',
        'speed_mult': 1.8
    }
]

class SectorManager:
    """
    Manages the Rogue Mode 'Sector Protocol' run.
    Tracks lines cleared towards the current sector quota,
    unlocks the 3-relic draft screen between sectors, and tracks active relics.
    """
    def __init__(self):
        self.current_sector_index = 0
        self.sector_lines_cleared = 0
        self.acquired_relics = []
        self.emergency_purge_used_this_sector = False
        self.offered_relics = []
        self.is_drafting = False
        self.run_completed = False

    def get_current_sector(self):
        """Returns the dictionary data for the current sector."""
        if self.current_sector_index < len(SECTORS):
            return SECTORS[self.current_sector_index]
        return SECTORS[-1]

    def has_relic(self, relic_id):
        """Returns True if the player currently owns the specified relic."""
        for r in self.acquired_relics:
            if r['id'] == relic_id:
                return True
        return False

    def add_lines(self, lines):
        """
        Adds cleared lines towards sector progress.
        Returns True if the sector quota has been met and draft screen should open!
        """
        self.sector_lines_cleared += lines
        current_sector = self.get_current_sector()
        
        if self.sector_lines_cleared >= current_sector['lines_needed']:
            if self.current_sector_index < len(SECTORS) - 1:
                # Trigger relic draft screen!
                self.is_drafting = True
                self.offered_relics = self.generate_3_relic_choices()
                return True
            else:
                # Beat the final sector!
                self.run_completed = True
                return False
        return False

    def generate_3_relic_choices(self):
        """Picks 3 unique relics that the player does not already own."""
        available = [r for r in ALL_RELICS if not self.has_relic(r['id'])]
        if len(available) <= 3:
            return available
        return random.sample(available, 3)

    def select_relic(self, relic_id):
        """Player chooses one of the offered relics."""
        for r in self.offered_relics:
            if r['id'] == relic_id:
                self.acquired_relics.append(r)
                break

        # Advance to next sector
        self.current_sector_index += 1
        self.sector_lines_cleared = 0
        self.emergency_purge_used_this_sector = False
        self.is_drafting = False
        self.offered_relics = []
