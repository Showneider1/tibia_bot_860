"""
Endereços de memória Tibia 8.60 - TibiaAPI Oficial.
Fonte: https://github.com/ianobermiller/tibiaapi/blob/master/tibiaapi/Addresses/Versions/Version860.cs
"""

from src.core.value_objects.address import MemoryAddress

# Nome exato do processo que identificámos
PROCESS_NAME = "Not Open.exe"

# Base: Player.Experience = 0x63FE8C
PLAYER_BASE_EXP = MemoryAddress(0x63FE8C)

PLAYER = {
    "experience": PLAYER_BASE_EXP,                     # 0x63FE8C
    "id": PLAYER_BASE_EXP.with_offset(12),             # 0x63FE98 (Experience + 12)
    "health": PLAYER_BASE_EXP.with_offset(8),          # 0x63FE94 (Experience + 8)
    "health_max": PLAYER_BASE_EXP.with_offset(4),      # 0x63FE90 (Experience + 4)
    "level": PLAYER_BASE_EXP.with_offset(-4),          # 0x63FE88 (Experience - 4)
    "magic_level": PLAYER_BASE_EXP.with_offset(-8),    # 0x63FE84 (Experience - 8)
    "level_percent": PLAYER_BASE_EXP.with_offset(-12), # 0x63FE80 (Experience - 12)
    "magic_percent": PLAYER_BASE_EXP.with_offset(-16), # 0x63FE7C (Experience - 16)
    "mana":          PLAYER_BASE_EXP.with_offset(-20),   # 0x63FE78 (Experience - 20)
    "mana_max":      PLAYER_BASE_EXP.with_offset(-24),   # 0x63FE74 (Experience - 24)
    "soul":          PLAYER_BASE_EXP.with_offset(-28),   # 0x63FE70 (Experience - 28)
    "stamina":       PLAYER_BASE_EXP.with_offset(-32),   # 0x63FE6C (Experience - 32)
    "capacity":      PLAYER_BASE_EXP.with_offset(-36),   # 0x63FE68 (Experience - 36)
    "flags":         PLAYER_BASE_EXP.with_offset(-108),  # 0x63FE20 (Experience - 108)

    
    # === NOVOS ENDEREÇOS REAIS DE POSIÇÃO ===
    "pos_x": MemoryAddress(0x640958),
    "pos_y": MemoryAddress(0x640954),
    "pos_z": MemoryAddress(0x640950),
    # ========================================
    
    # Endereços de skills
    "fist_percent": MemoryAddress(0x63FE24),
}

# Battle List
BATTLE_LIST = {
    "start": MemoryAddress(0x63FEF8),
    "step": 0xA8,
    "max_creatures": 250,
}

# Creature offsets (dentro da battle list)
CREATURE = {
    "id": 0,
    "name": 4,
    "x": 36,
    "y": 40,
    "z": 44,
    "hp_bar": 136,
    "walking": 76,
    "visible": 144,
    "walk_speed": 140,
    "direction": 80,
}

# Login
LOGIN = {
    "account": MemoryAddress(0x79CF04),
    "password": MemoryAddress(0x79CEE4),
}

# Map Pointer (para pegar posição real do player)
MAP_POINTER = MemoryAddress(0x654118)

# Vocações (index extraído de Player.Flags ou outro campo)
VOCATIONS = {
    0: "None",
    1: "Knight",
    2: "Paladin",
    3: "Sorcerer",
    4: "Druid",
    5: "Elite Knight",
    6: "Royal Paladin",
    7: "Master Sorcerer",
    8: "Elder Druid",
}