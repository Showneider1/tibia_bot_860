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
    # FIXME: capacity (-36 = 0x63FE68) overlap com buffer de name (-50 = 0x63FE5A, 32 bytes)
    # 0x63FE68 cai no byte 14 do nome. Requer CE para achar endereço real de capacity.
    "capacity":       PLAYER_BASE_EXP.with_offset(-36),     # 0x63FE68 (PROVAVELMENTE ERRADO)
    "name":           PLAYER_BASE_EXP.with_offset(-50),     # 0x63FE5A
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

# === NOVOS ENDEREÇOS PARA FUNCIONALIDADES AVANÇADAS ===

# Containers (Bags, Corpses, etc.) - para loot system
CONTAINER = {
    "start":              MemoryAddress(0x64CD10),
    "step_container":     492,
    "step_slot":          12,
    "max_containers":     16,
    "max_stack":          100,
    "distance_is_open":   0,
    "distance_id":        4,
    "distance_name":      16,
    "distance_volume":    48,
    "distance_amount":    56,
    "distance_item_id":   60,
    "distance_item_count": 64,
}

# Map/Tiles (para leitura de items no chão)
MAP = {
    "map_pointer":            MemoryAddress(0x654118),
    "step_tile":              168,
    "step_tile_object":       12,
    "distance_tile_object_count": 0,
    "distance_tile_objects":  4,
    "distance_object_id":     0,
    "distance_object_data":   4,
    "distance_object_data_ex": 8,
    "max_tile_objects":       10,
    "max_x":                  18,
    "max_y":                  14,
    "max_z":                  8,
    "max_tiles":              2016,
    "z_axis_default":         7,
}

# Hotkeys (para auto-use de potions/food)
HOTKEY = {
    "send_automatically_start": MemoryAddress(0x799EE0),
    "send_automatically_step":  0x01,
    "text_start":              MemoryAddress(0x799F08),
    "text_step":               0x100,
    "object_start":            MemoryAddress(0x799E50),
    "object_step":             0x04,
    "object_use_type_start":   MemoryAddress(0x799D30),
    "object_use_type_step":    0x04,
    "max_hotkeys":             36,
}

# Player Slots (equipamentos)
PLAYER_SLOTS = {
    "slot_head":     MemoryAddress(0x64CC98),
    "slot_neck":     MemoryAddress(0x64CC98 + 12),   # Head + 12
    "slot_backpack": MemoryAddress(0x64CC98 + 24),   # Head + 24
    "slot_armor":    MemoryAddress(0x64CC98 + 36),   # Head + 36
    "slot_right":    MemoryAddress(0x64CC98 + 48),   # Head + 48
    "slot_left":     MemoryAddress(0x64CC98 + 60),   # Head + 60
    "slot_legs":     MemoryAddress(0x64CC98 + 72),   # Head + 72
    "slot_feet":     MemoryAddress(0x64CC98 + 84),   # Head + 84
    "slot_ring":     MemoryAddress(0x64CC98 + 96),   # Head + 96
    "slot_ammo":     MemoryAddress(0x64CC98 + 108),  # Head + 108
    "max_slots":     10,
    "distance_slot_count": 4,
}

# Additional Player addresses (targeting, etc.)
# BUG-I FIX: go_to_x/y/z - ordem dos offsets corrigida.
# TibiaAPI 8.60 armazena os campos na ordem: GoToX (+72), GoToY (+76), GoToZ (+80)
# relativo à base 0x63FE8C (Experience).
# A versão anterior tinha X com offset +80 e Z com +72, invertendo as coordenadas
# X e Z na leitura de memória e fazendo o pathfinder calcular rotas erradas.
PLAYER_EXTRA = {
    "current_tile_to_go":    MemoryAddress(0x63FEA0),
    "tiles_to_go":           MemoryAddress(0x63FEA4),
    "go_to_x":               MemoryAddress(0x63FE8C + 72),  # Experience + 72 = 0x63FED4
    "go_to_y":               MemoryAddress(0x63FE8C + 76),  # Experience + 76 = 0x63FED8
    "go_to_z":               MemoryAddress(0x63FE8C + 80),  # Experience + 80 = 0x63FEDC
    "player_z":              MemoryAddress(0x64F600),
    "attack_count":          MemoryAddress(0x63DA40),       # Attack counter (incrementa a cada ataque)
    "follow_count":          MemoryAddress(0x63DA60),       # Follow counter (AttackCount + 0x20)
}

# Targeting via memory injection (ElfBot-style / TibiaAPI)
# Baseados no TibiaAPI 8.60: Player.TargetId = Player.RedSquare = 0x63FE64
# Writing to these addresses selects a target and triggers auto-attack,
# no PostMessage/input injection needed.
TARGET = {
    "target_id":             MemoryAddress(0x63FE64),  # Player.TargetId (creature ID)
    "target_mode":           MemoryAddress(0x63FE67),  # Player.TargetType: 0=none, 1=attack, 2=follow
    "target_battlelist_id":   MemoryAddress(0x63FE5C),  # Player.TargetBattlelistId (slot+1, 0=none)
    "target_battlelist_type": MemoryAddress(0x63FE5F),  # Player.TargetBattlelistType: 0=none, 1=attack, 2=follow
    "attack_count":          MemoryAddress(0x63DA40),  # Player.AttackCount (auto-increment)
    "follow_count":          MemoryAddress(0x63DA60),  # Player.FollowCount (auto-increment)
}

# VIP List (para detecção de players)
VIP = {
    "start":           MemoryAddress(0x63DBB8),
    "step_players":    0x2C,
    "max_players":     200,
    "distance_id":     0,
    "distance_name":   4,
    "distance_status": 34,
    "distance_icon":   40,
}

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
