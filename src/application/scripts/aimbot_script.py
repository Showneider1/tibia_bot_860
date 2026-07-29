import time
from typing import Dict, Any, List, Optional
from .base_script import BaseScript
from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.ai.combat.combat_ai import CombatAI
from src.core.constants.addresses_860 import TARGET
from src.infrastructure.memory.memory_writer import MemoryWriter
from src.infrastructure.memory.memory_reader import MemoryReader
from src.infrastructure.injection.keyboard_injector import KeyboardInjector

_HOTKEYS = frozenset({"F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12"})

class AimbotScript(BaseScript):
    def __init__(self):
        super().__init__("AimBot")
        self.priority = 50
        self.config = {
            "enabled": False,
            "max_distance": 7,
            "attack_hotkey": "F1",
            "min_hp_to_attack": 30,
            "cooldown": 0.3,
            "target_blacklist": ["Training Assistant"],
            "target_whitelist": [],
            "target_priorities": [],
            "targeting_mode": "highest_xp",
            "prefer_low_hp_for_kill": True,
            "low_hp_threshold": 25,
            "enable_combo_attacks": True,
            "combo_spells": [
                {"spell": "exori gran", "cooldown": 4.0, "mana_cost": 120, "max_distance": 1},
                {"spell": "exori hur", "cooldown": 6.0, "mana_cost": 40, "max_distance": 3},
            ],
            "xp_values": {
                "Dragon": 700,
                "Dragon Lord": 1100,
                "Demon": 6000,
                "Rotworm": 40,
                "Cyclops": 150,
                "Cyclops Smith": 275,
                "Cyclops Drone": 255,
                "Giant Spider": 650,
                "Vampire": 305,
                "Necromancer": 580,
                "Priestess": 420,
            },
            "loot_values": {
                "Dragon": 100,
                "Dragon Lord": 200,
                "Demon": 500,
                "Rotworm": 5,
                "Cyclops": 30,
                "Giant Spider": 80,
            },
            "enable_anti_lure": True,
            "max_follow_distance": 10,
            "use_combat_ai": True,
            "use_memory_injection": True,
            "viewport_offset_x": 0,
            "viewport_offset_y": 0,
            "battle_list_x": 470,
            "battle_list_y_start": 42,
            "battle_list_slot_height": 16,
        }
        self._last_attack_time = 0
        self._combat_ai: Optional[CombatAI] = None
        self._current_target: Optional[Creature] = None
        self._last_combo_time = 0
        self._combo_cooldowns: Dict[str, float] = {}
        self._name_to_priority: Dict[str, dict] = {}
        self._name_cache_time = 0.0

    def _rebuild_name_cache(self):
        priorities = self.config.get("target_priorities", [])
        self._name_to_priority = {
            p.get("name", "").strip().lower(): p
            for p in priorities if p.get("name")
        }
        self._name_cache_time = time.time()

    def _priority_for_creature(self, name: str) -> Optional[dict]:
        key = name.strip().lower()
        if not self._name_to_priority or time.time() - self._name_cache_time > 2.0:
            self._rebuild_name_cache()
        return self._name_to_priority.get(key)

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        creatures: List[Creature] = context.get("creatures", [])
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine or not creatures:
            return False

        if self.config.get("use_combat_ai") and not self._combat_ai:
            vocation = bot_engine.config.get("player_vocation", "Druid")
            self._combat_ai = CombatAI(vocation)
            self._log.info(f"Combat AI inicializado para {vocation}")

        valid_creatures = self._filter_creatures(creatures, player)
        if not valid_creatures:
            self._current_target = None
            return False

        if self.config["enable_anti_lure"]:
            valid_creatures = [
                c for c in valid_creatures
                if player.position.distance_chebyshev(c.position) <= self.config["max_follow_distance"]
            ]
            if not valid_creatures:
                return False

        if self._combat_ai:
            decision = self._combat_ai.decide_action(player, valid_creatures)
            if decision == "flee":
                self._log.warning(f"CombatAI decidiu fugir (HP: {player.hp_percent()}%)")
                self._current_target = None
                return False
            elif decision == "use_skill":
                skill = self._combat_ai.get_next_skill(player)
                if skill:
                    self._log.info(f"CombatAI: usando {skill.name}")
                    bot_engine.cast_spell(skill.words or skill.name)
                    self._combat_ai.mark_skill_used(skill.name)
                    self._last_attack_time = time.time()
                    return True
            elif decision == "idle":
                return False

        target = self._select_target(player, valid_creatures)
        if not target:
            return False

        self._current_target = target

        pri = self._priority_for_creature(target.name)
        creature_mode = pri.get("mode", "Attack") if pri else "Attack"
        if pri:
            spell_range = pri.get("distance", 1)
        else:
            spell_range = self.config["max_distance"]

        distance = player.position.distance_chebyshev(target.position)

        if creature_mode == "Follow" and distance > spell_range:
            try:
                walker = getattr(bot_engine, "walker", None)
                if walker:
                    walker.walk_to(player.position, target.position)
                return True
            except Exception as e:
                self._log.error(f"Erro ao seguir {target.name}: {e}")
                return False

        if distance > spell_range:
            return False

        if time.time() - self._last_attack_time < self.config["cooldown"]:
            if self.config["enable_combo_attacks"] and self._current_target:
                return self._try_combo_attack(player, self._current_target, bot_engine)
            return False

        if player.hp_percent() < self.config["min_hp_to_attack"]:
            return False

        success = self._attack_target(player, target, bot_engine)
        if success:
            self._last_attack_time = time.time()
            hp_pct = (target.stats.health / target.stats.max_health * 100) if target.stats.max_health > 0 else 0
            self._log.info(f"Atacando: {target.name} (HP: {hp_pct:.0f}%)")

            if self.config["enable_combo_attacks"]:
                self._try_combo_attack(player, target, bot_engine)

            return True

        return False

    def _filter_creatures(self, creatures: List[Creature], player: Player) -> List[Creature]:
        filtered = []
        has_priorities = bool(self.config.get("target_priorities"))

        for creature in creatures:
            if creature.id == player.id:
                continue
            if creature.name in self.config["target_blacklist"]:
                continue
            if self.config["target_whitelist"]:
                if creature.name not in self.config["target_whitelist"]:
                    continue

            if creature.stats.health <= 0:
                continue

            pri = self._priority_for_creature(creature.name) if has_priorities else None

            if has_priorities and pri is None:
                continue

            distance = player.position.distance_chebyshev(creature.position)
            max_dist = pri.get("distance", self.config["max_distance"]) if pri else self.config["max_distance"]
            if distance > min(max_dist, self.config["max_distance"]):
                continue

            if pri:
                creature_hp_pct = (creature.stats.health / creature.stats.max_health * 100) if creature.stats.max_health > 0 else 0
                if creature_hp_pct > pri.get("hp_pct", 100):
                    continue

            filtered.append(creature)

        return filtered

    def _select_target(self, player: Player, creatures: List[Creature]) -> Optional[Creature]:
        if not creatures:
            return None

        mode = self.config["targeting_mode"]

        if self._current_target and self._current_target in creatures:
            current_distance = player.position.distance_chebyshev(self._current_target.position)
            if (self._current_target.stats.health > 0 and
                current_distance <= self.config["max_distance"]):
                if self.config["prefer_low_hp_for_kill"]:
                    low_hp_target = self._find_low_hp_target(creatures)
                    if low_hp_target and low_hp_target != self._current_target:
                        return low_hp_target
                return self._current_target

        if mode == "highest_xp":
            return self._select_highest_xp(creatures)
        elif mode == "lowest_hp":
            return self._select_lowest_hp(creatures)
        elif mode == "closest":
            return self._select_closest(player, creatures)
        elif mode == "highest_threat":
            if self._combat_ai:
                return self._combat_ai.get_target(player, creatures)
            return self._select_highest_threat(player, creatures)
        else:
            return creatures[0]

    def _select_highest_xp(self, creatures: List[Creature]) -> Optional[Creature]:
        xp_values = self.config.get("xp_values", {})
        if not xp_values:
            return max(creatures, key=lambda c: c.stats.max_health)
        return max(creatures, key=lambda c: xp_values.get(c.name, c.stats.max_health))

    def _select_lowest_hp(self, creatures: List[Creature]) -> Optional[Creature]:
        return min(creatures, key=lambda c: c.stats.health)

    def _find_low_hp_target(self, creatures: List[Creature]) -> Optional[Creature]:
        threshold = self.config["low_hp_threshold"]
        low_hp_creatures = [c for c in creatures if c.stats.health <= threshold]
        if not low_hp_creatures:
            return None
        return min(low_hp_creatures, key=lambda c: c.stats.health)

    def _select_closest(self, player: Player, creatures: List[Creature]) -> Optional[Creature]:
        return min(creatures, key=lambda c: player.position.distance_chebyshev(c.position))

    def _select_highest_threat(self, player: Player, creatures: List[Creature]) -> Optional[Creature]:
        def threat_score(c):
            distance = player.position.distance_chebyshev(c.position)
            distance_score = max(0, 10 - distance)
            hp_score = c.stats.health / 10
            return distance_score + hp_score
        return max(creatures, key=threat_score)

    def _get_attack_hotkey(self, target: Creature) -> str:
        pri = self._priority_for_creature(target.name)
        spell_or_key = pri.get("spell") if pri else None
        if spell_or_key and spell_or_key.upper() in _HOTKEYS:
            return spell_or_key
        return self.config["attack_hotkey"]

    def _target_via_memory(self, creature: Creature, bot_engine) -> bool:
        try:
            mw: MemoryWriter = bot_engine.memory_writer
            mr: MemoryReader = bot_engine.memory_reader
            ok1 = mw.write_int(TARGET["target_id"], creature.id)
            ok2 = mw.write_bytes(TARGET["target_mode"], b'\x01')
            if ok1 and ok2:
                # Verify: read back the target ID (force fresh read, no cache)
                read_id = mr.read_uint(TARGET["target_id"], use_cache=False)
                if read_id == creature.id:
                    self._log.debug(f"Memory target OK: {creature.name} (ID={creature.id})")
                    return True
                else:
                    self._log.warning(f"Memory verify falhou: escreveu {creature.id}, leu {read_id}")
                    return False
            self._log.warning(f"Memory target write retornou ok1={ok1} ok2={ok2} para {creature.name}")
            return False
        except Exception as e:
            self._log.warning(f"Memory target exception: {e}")
            return False

    def _target_via_battle_list_memory(self, creature: Creature, bot_engine) -> bool:
        slot = creature.battle_slot
        if slot < 0:
            return False
        try:
            mw: MemoryWriter = bot_engine.memory_writer
            mr: MemoryReader = bot_engine.memory_reader
            ok1 = mw.write_int(TARGET["target_battlelist_id"], slot + 1)
            ok2 = mw.write_bytes(TARGET["target_battlelist_type"], b'\x01')
            if ok1 and ok2:
                read_slot = mr.read_uint(TARGET["target_battlelist_id"], use_cache=False)
                if read_slot == slot + 1:
                    self._log.debug(f"Memory battle list target: {creature.name} slot={slot}")
                    return True
                self._log.warning(f"Memory BL verify falhou: escreveu slot={slot+1}, leu {read_slot}")
                return False
            self._log.warning(f"Memory BL write retornou ok1={ok1} ok2={ok2}")
            return False
        except Exception as e:
            self._log.warning(f"Memory BL exception: {e}")
            return False

    def _target_via_tile_click(self, creature: Creature, player: Player, injector: KeyboardInjector) -> bool:
        ox = self.config.get("viewport_offset_x", 0)
        oy = self.config.get("viewport_offset_y", 0)
        return injector.click_tile(creature.position.x, creature.position.y,
                                   player.position.x, player.position.y, ox, oy)

    def _target_by_battle_slot(self, creature: Creature, injector) -> bool:
        slot = creature.battle_slot
        if slot < 0:
            return False
        bx = self.config.get("battle_list_x", 470)
        by_start = self.config.get("battle_list_y_start", 42)
        bh = self.config.get("battle_list_slot_height", 16)
        sy = by_start + slot * bh + bh // 2
        return injector.send_mouse_click(bx, sy)

    def _attack_target(self, player: Player, target: Creature, bot_engine) -> bool:
        hotkey = self._get_attack_hotkey(target)
        injector: KeyboardInjector = bot_engine.injector

        # 1) Memory injection — target ID direto (mais rapido e confiavel)
        if self.config.get("use_memory_injection", True):
            if self._target_via_memory(target, bot_engine):
                injector.send_hotkey(hotkey)
                return True
            # 1b) Fallback via battle list index na memoria
            if self._target_via_battle_list_memory(target, bot_engine):
                injector.send_hotkey(hotkey)
                return True
            self._log.warning("Memory injection falhou — tentando metodos alternativos")
        else:
            self._log.debug("Memory injection desligado via config")

        # 2) Tile click (isometrico, universal)
        if self._target_via_tile_click(target, player, injector):
            time.sleep(0.050)
            injector.send_hotkey(hotkey)
            return True
        self._log.warning("Tile click falhou — tentando battle list")

        # 3) Battle list slot click (fallback final)
        if self._target_by_battle_slot(target, injector):
            time.sleep(0.050)
            injector.send_hotkey(hotkey)
            return True

        self._log.error(f"Todas as formas de targeting falharam para {target.name}")
        return False

    def _try_combo_attack(self, player: Player, target: Creature, bot_engine) -> bool:
        if not self.config["enable_combo_attacks"]:
            return False

        combo_spells = self.config.get("combo_spells", [])
        if not combo_spells:
            return False

        current_time = time.time()
        injector = bot_engine.injector

        for combo in combo_spells:
            spell_name = combo["spell"]
            cooldown = combo.get("cooldown", 0)
            mana_cost = combo.get("mana_cost", 0)
            max_distance = combo.get("max_distance", 1)

            last_use = self._combo_cooldowns.get(spell_name, 0)
            if current_time - last_use < cooldown:
                continue

            if player.stats.mana < mana_cost:
                continue

            distance = player.position.distance_chebyshev(target.position)
            if distance > max_distance:
                continue

            if self.config.get("use_memory_injection", True):
                if not self._target_via_memory(target, bot_engine):
                    if not self._target_via_battle_list_memory(target, bot_engine):
                        if not self._target_via_tile_click(target, player, injector):
                            if not self._target_by_battle_slot(target, injector):
                                continue
            else:
                if not self._target_via_tile_click(target, player, injector):
                    if not self._target_by_battle_slot(target, injector):
                        continue
            time.sleep(0.050)

            if spell_name.upper() in _HOTKEYS:
                injector.send_hotkey(spell_name)
            else:
                bot_engine.cast_spell(spell_name)
            self._combo_cooldowns[spell_name] = current_time
            self._log.info(f"Combo: {spell_name} em {target.name}")
            return True

        return False

    def clear_target(self) -> None:
        self._current_target = None

    def get_current_target(self) -> Optional[Creature]:
        return self._current_target
