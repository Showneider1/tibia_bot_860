"""
Endereços de memória Tibia 8.60 - TibiaAPI Oficial.
Fonte: https://github.com/ianobermiller/tibiaapi/blob/master/tibiaapi/Addresses/Versions/Version860.cs
"""

from src.core.value_objects.address import MemoryAddress

# Nome real do processo detectado via diagnose_memory.py / Cheat Engine
PROCESS_NAME = "Not Open.exe"

# Base: Player.Experience = 0x63FE8C
PLAYER_BASE_EXP = MemoryAddress(0x63FE8C)

PLAYER = {
    "experience":     PLAYER_BASE_EXP,                      # 0x63FE8C
    "id":             PLAYER_BASE_EXP.with_offset(12),      # 0x63FE98
    "health":         PLAYER_BASE_EXP.with_offset(8),       # 0x63FE94
    "health_max":     PLAYER_BASE_EXP.with_offset(4),       # 0x63FE90
    "level":          PLAYER_BASE_EXP.with_offset(-4),      # 0x63FE88
    "magic_level":    PLAYER_BASE_EXP.with_offset(-8),      # 0x63FE84
    "level_percent":  PLAYER_BASE_EXP.with_offset(-12),     # 0x63FE80
    "magic_percent":  PLAYER_BASE_EXP.with_offset(-16),     # 0x63FE7C
    "mana":           PLAYER_BASE_EXP.with_offset(-20),     # 0x63FE78
    "mana_max":       PLAYER_BASE_EXP.with_offset(-24),     # 0x63FE74
    "soul":           PLAYER_BASE_EXP.with_offset(-28),     # 0x63FE70
    "stamina":        PLAYER_BASE_EXP.with_offset(-32),     # 0x63FE6C
    "capacity":       PLAYER_BASE_EXP.with_offset(-36),     # 0x63FE68
    "name":           PLAYER_BASE_EXP.with_offset(-50),     # 0x63FE5E
    "flags":          PLAYER_BASE_EXP.with_offset(-108),    # 0x63FE20
    # Vocation: byte imediatamente após flags (flags+1)
    # Tibia 8.60: 1=Sorcerer,2=Druid,3=Paladin,4=Knight,5=MS,6=ED,7=RP,8=EK
    "vocation":       PLAYER_BASE_EXP.with_offset(-107),    # 0x63FE21
    # Endereços de skills
    "fist_percent":   MemoryAddress(0x63FE24),
}

# Battle List
BATTLE_LIST = {
    "start":         MemoryAddress(0x63FEF8),
    "step":          0xA8,
    "max_creatures": 250,
}

# Creature offsets (dentro da battle list)
CREATURE = {
    "id":         0,
    "name":       4,
    "x":          36,
    "y":          40,
    "z":          44,
    "hp_bar":     136,
    "walking":    76,
    "visible":    144,
    "walk_speed": 140,
    "direction":  80,
}

# Login
LOGIN = {
    "account":  MemoryAddress(0x79CF04),
    "password": MemoryAddress(0x79CEE4),
}

# Map Pointer (para pegar posição real do player)
MAP_POINTER = MemoryAddress(0x654118)

# Vocações mapeadas pelo byte lido de 'vocation' (0x63FE21)
# Tibia 8.60 encoding: 1-4 promovable, 5-8 promoted
VOCATIONS = {
    0: "None",
    1: "Sorcerer",
    2: "Druid",
    3: "Paladin",
    4: "Knight",
    5: "Master Sorcerer",
    6: "Elder Druid",
    7: "Royal Paladin",
    8: "Elite Knight",
}
