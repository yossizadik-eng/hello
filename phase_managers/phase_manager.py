
import re
from collections import Counter
from types import SimpleNamespace

import tkinter as tk
import constants
from models import card
from phase_managers import draw_phase_manager as draw_phase_manager
from models.special_cards import monster_effects
#from special_cards import BEAST_FANGS , BOOK_OF_SECRET_ARTS ,CAPTURE_JAR,DARK_ENERGY , DARK_HOLE, FISSURE, FOREST , GRAVEDIGGER_GHOUL, HINOTAMA, LEGENDARY_SWORD, MOUNTAIN, POLYMERIZATION, POWER_OF_KAISHIN, RAIGEKI, RED_MEDICINE, REMOVE_TRAP, SOGEN, SPARKS, TRAP_HOLE, TWO_PRONGED, UMI, VIOLET_CRYSTAL, WASTELAND, YAMI

from models.special_cards import spell_cards   
from game_engine.combat import resolve_battle

EXODIA_PIECES = {
    "exodia the forbidden one",
    "right arm of the forbidden one",
    "left arm of the forbidden one",
    "right leg of the forbidden one",
    "left leg of the forbidden one",
}

    # 1. Draw Phase: The turn begins here. It is the automated resource-gathering step.
    # The Main Rule: The active player draws exactly 1 card from the top of their Main Deck.  
    # Card Restrictions: Only Fast Effects (Trap cards and Quick-Play Spells) can be activated here. You cannot summon monsters or play normal Spells.

    # 2. Main Phase 1 (MP1)This is the primary strategic sandbox where you build your board presence. 
    # The active player can perform any of the following actions in any order:
    # Normal Summon or Set: Once per turn, you can play a Level 1–4 monster face-up in Attack Position (Summon) or face-down in Defense Position (Set). 
    # Higher-level monsters require Tributes.  
# Special Summon: You can perform an unlimited number of Special Summons (Fusion, Synchro, Xyz, Link, or Card Effects), 
    # as long as you meet the material requirements.Activate Spells & Traps: You can activate any Spell card type or Set Spells/Traps face-down to use later.  
    # Change Battle Positions: You can manually flip a monster from Attack to Defense (or vice versa). 
    # Restrictions: You cannot change a monster's position if it was summoned this turn, or if it already attacked.  '

# 3. Battle Phase (BP)This is where monsters fight. Note: You are never forced to enter a Battle Phase; 
# you can skip it entirely and jump straight from MP1 to the End Phase.  
# The Turn-1 Exception: The player going first cannot have a Battle Phase on Turn 1.  
# The Sub-Steps: The Battle Phase breaks down internally into 4 micro-steps:
# Start Step: Announce you are entering combat.  
# Battle Step: Select your face-up Attack Position monster and declare its target 
# (an opponent's monster, or a direct attack if their field is empty).
# Damage Step: Compare stats ($ATK$ vs $ATK$ or $ATK$ vs $DEF$), inflict Life Point damage, and send the loser to the Graveyard.
# End Step: Announce you are finishing combat.  

# 4. Main Phase 2 (MP2)This phase only occurs if you entered the Battle Phase. 
# It acts as your post-combat adjustment phase to set up defenses for your opponent's upcoming turn.'
# The Main Rule: You can perform all the exact same actions as Main Phase 1 (setting traps, special summoning, etc.).
# The Multi-Phase Lockout: Restrictions carry over across phases. 
# For example, if you already used your single Normal Summon or changed a monster's position in Main Phase 1, 
# you cannot do it again in Main Phase 2.  

# 5. End Phase  The turn cleanup wrapper.
# The Main Rule: The active player passes priority to the opponent, signaling their turn is over. 
# Any card text stating "Until the end of this turn..." ceases to apply.  
# The Hand Size Limit: If the active player has more than 6 cards in their hand at this exact moment, 
# they must manually discard down to exactly 6 cards.  
# Once the End Phase closes, the state loops back to the Draw Phase for the other player.  

# ---- summoning rules ----
# summon monster - up to level 4 once per turn, face up attack or face down defense
# summon monster - level 5 or higher, once per turn, face up attack or face down defense, but you need to tribute 1 or more monsters
# summon monster - level 7 or higher, once per turn, face up attack or face down defense, but you need to tribute 2 or more monsters
# special summon monster - as many times as you want, but you need to meet the requirements 

class PhaseManager:     
    def __init__(self, board):
        self.board = board
        self.step = constants.step.TURN_START.value
        self.special_card_selected = None
        self.special_card_step = None
        self.tributes = 0
        self.pending_fusion_spell = None
        self.fusion_materials = []
        self.chain_resolving = False
        self.pending_monster_effect = None

    def can_move_to_phase(self, player, phase_button):
        success , message = self.phase_button_is_valid(player, phase_button)
        if success:
            player.turn_phase = phase_button  
            self.step = constants.step.TURN_START.value                             
            return True, None
        else:
            return False , message
            
    def phase_button_is_valid(self, player, phase_button):
    # [Draw Phase] ➔ [Main Phase 1]
    #                                       │
    #                     ┌─────────────────┴─────────────────┐
    #                     ▼                                   ▼
    #              [Battle Phase]                       [End Phase]
    #                     │
    #                     ▼
    #              [Main Phase 2]
    #                     │
    #                     ▼
    #                [End Phase]                             
        if player.turn_phase == constants.phase.DRAW and phase_button != constants.phase.MAIN1:
            return False, "Invalid phase transition: Must go from Draw Phase to Main Phase 1."
        elif player.turn_phase == constants.phase.MAIN1 and phase_button not in [constants.phase.BATTLE, constants.phase.MAIN2, constants.phase.END]:
            return False, "Invalid phase transition: Must go from Main Phase 1 to either Battle Phase, Main2 or End Phase."     
        elif player.turn_phase == constants.phase.BATTLE and phase_button not in [constants.phase.MAIN2, constants.phase.END]:
            return False, "Invalid phase transition: Must go from Battle Phase to Main Phase 2 or End Phase."
        elif player.turn_phase == constants.phase.MAIN2 and phase_button != constants.phase.END:
            return False, "Invalid phase transition: Must go from Main Phase 2 to End Phase."
        else:
            return True, None
                        
    def right_click(self, player, card):
        if card in player.hand:
            if self._try_activate_exodia(player, card):
                return True
            if card.current_position == constants.possition.ATTACK:
                card.set_position(constants.possition.DEFENSE)
                card.summon = False
                card.is_face_up = False
            else:
                card.set_position(constants.possition.ATTACK)
                card.summon = True
                card.is_face_up = True
            return True

        if not self.allow_change_position(player, card):
            return False

        if not card.is_face_up:
            card.set_position(constants.possition.ATTACK)
            card.summon = True
            card.is_face_up = True
            self.activate_flip_effect(card, player)
        elif card.current_position == constants.possition.ATTACK:
            card.set_position(constants.possition.DEFENSE)
        else:
            card.set_position(constants.possition.ATTACK)
        card.has_changed_position_this_turn = True
        return True

    def _try_activate_exodia(self, player, card):
        if card.name.casefold() != "exodia the forbidden one":
            return False
        held_pieces = {
            held_card.name.casefold()
            for held_card in player.hand
            if held_card.name.casefold() in EXODIA_PIECES
        }
        if held_pieces != EXODIA_PIECES:
            return False

        confirm = getattr(self.board, "ask_yes_no", None)
        if confirm is None or not confirm(
            "Exodia",
            "Would you like to activate Exodia?",
        ):
            return True

        winner_callback = getattr(self.board, "show_winner", None)
        if winner_callback is not None:
            winner_callback(self.board.opposite_player)
        return True
                
    def allow_change_position(self, player, card):
        return (
            player is self.board.current_player
            and card in player.battle_cards
            and player.turn_phase in (constants.phase.MAIN1, constants.phase.MAIN2)
            and not card.summoned_this_turn
            and not card.has_changed_position_this_turn
            and card not in player.is_attacking
        )
        
    def hand_card_clicked(self, card):
        if self.pending_fusion_spell is not None:
            self.select_fusion_material(card)
            return
        if card.name == constants.special_card_effects.POLYMERIZATION:
            self.start_fusion_summon(card)
            return
        # if a special card is already selected, then we want to activate it on the card that was just clicked
        if not self.special_card_selected == None :         
            self.handle_special_card(card)                
        else:
        # if no special card is selected, then we want to move the card to the battle zone or special card zone depending on the type of the card
            if constants.card_types.MONSTER in card.type:
                if self.board.current_player.turn_phase == constants.phase.DRAW and (card.current_position == constants.possition.ATTACK or card.summon): 
                        self.board.show_popup(f"{self.board.current_player.name} can not summon at DRAW phase !")  
                elif self.board.current_player.has_summoned_this_turn:                
                    self.board.show_popup(f"{self.board.current_player.name} has already summoned this turn !")  
                else:            
                    self.move_from_hand_to_battle(card)
            else: 
                if self.activate_player_spell_from_hand(card):
                    return
                if constants.race.FIELD in card.race:
                    self.activate_field_spell(card)
                    return
                spell_class = spell_cards.CARD_REGISTRY.get(card.name)
                spell = spell_class(original_card=card) if spell_class else None
                if spell is not None and spell.trigger is not None:
                    self.board.show_popup(
                        "Set this Trap with a right-click; it activates when its trigger occurs."
                    )
                    return
                if spell is not None and card.name in spell_cards.CARD_REGISTRY:
                    if not self._can_activate_manual_spell(card):
                        self.board.show_popup(
                            "This Spell cannot be activated during the current phase."
                        )
                        return
                    self.special_card_selected = card
                    self.step = constants.step.SPECIAL_CARD_SELECED
                    self.handle_special_card(card)
                else:
                    self.move_from_hand_to_special(card)

    def activate_player_spell_from_hand(self, card):
        card_class = spell_cards.CARD_REGISTRY.get(card.name)
        if card_class is None:
            return False

        spell = card_class(original_card=card)
        if spell.spell_level != constants.spell_level.PLAYER:
            return False

        if self.board.current_player.turn_phase not in (
            constants.phase.MAIN1,
            constants.phase.MAIN2,
        ):
            self.board.show_popup(
                "This Life Point spell can only be activated in Main Phase 1 or Main Phase 2."
            )
            return True

        self.resolve_chain(
            lambda: spell.activate(self.board, None),
            self.board.current_player,
            constants.events.SPELL_ACTIVATED,
            initial_label=spell.name,
        )
        return True

    def _can_activate_manual_spell(self, card):
        phase = self.board.current_player.turn_phase
        return phase in (constants.phase.MAIN1, constants.phase.MAIN2) or (
            phase == constants.phase.DRAW
            and constants.race.QUICK_SPELL in card.race
        )

    def special_card_clicked(self, card):
        if self.pending_fusion_spell is not None:
            self.select_fusion_material(card)
            return
        if card.name == constants.special_card_effects.POLYMERIZATION:
            self.start_fusion_summon(card)
            return
        if constants.race.FIELD in card.race:
            self.activate_field_spell(card)
            return
        card_class = spell_cards.CARD_REGISTRY.get(card.name)
        if card_class and card_class(original_card=card).trigger:
            self.board.show_popup("This trap activates only when its trigger condition is met.")
            return
        if card.can_be_selected == True:
            if not self._can_activate_manual_spell(card):
                self.board.show_popup(
                    "This Spell cannot be activated during the current phase."
                )
                return
            self.step = constants.step.SPECIAL_CARD_SELECED
            self.special_card_selected = card
            self.handle_special_card(card)
        else:
            self.board.display_ok_message("not allowed", "you can not select this spell now")
               
    def move_from_hand_to_battle(self, card):
        if self.board.current_player.has_summoned_this_turn:
            self.board.display_ok_message("not allowed", "you already summoned a monster this turn")
            return 
        if self.board.current_player.has_set_this_turn:
            self.board.display_ok_message("not allowed", "you already set a monster this turn")
            return
        if card.level < 5:
            self.move_to_battle(card)            
        else:
            self.tribute_summon(card)

    def move_to_battle(self, card):
        self.board.current_player.hand.remove(card)
        self.board.current_player.battle_cards.append(card)
        self.board.current_player.has_summoned_this_turn = True
        card.summoned_this_turn = True
        card.can_be_selected = False
        if card.summon:
            card.is_face_up = True
        self.apply_active_field_spells_to_card(card)
        self.check_trap_triggers(constants.events.ON_SUMMON, card)
    
    def tribute_summon(self, card):
        self.tribute_allowed = False
        if card.level > 4 and card.level < 7:
            if len(self.board.current_player.battle_cards) == 0:
                self.board.display_ok_message("not allowed", "You don't have a monster to tribute")
            else:
                self.board.display_ok_message("offer tribute", "You need to tribute a monster")
                self.tribute_allowed = True
                self.tributes = 1
                self.board.current_player.tribute_monster = card
        else:
            if len(self.board.current_player.battle_cards) < 2:
                self.board.display_ok_message("not allowed", "You don't have 2 monsters to tribute")
            else:
                self.tribute_allowed = True
                self.tributes = 2   
                self.board.display_ok_message("offer tribute", "You need to tribute 2 monsters")
                self.board.current_player.tribute_monster = card
            
    def move_from_hand_to_special(self, card):
        if constants.race.FIELD in card.race:
            self.activate_field_spell(card)
            return
        if self.allow_use_spell(card):
            self.board.current_player.hand.remove(card)
            self.board.current_player.special_cards.append(card)
            card.is_face_up = False
            card.can_be_selected = False
        else:
            self.board.show_popup(constants.messages.SPELL_NOT_ALLOWED)                             

    def set_hand_spell_or_trap(self, card):
        player = self.board.current_player
        if constants.card_types.MONSTER in card.type:
            return False
        if player.turn_phase not in (constants.phase.MAIN1, constants.phase.MAIN2):
            self.board.show_popup("Spells and Traps can only be set in a Main Phase.")
            return True
        existing_non_field_cards = sum(
            constants.race.FIELD not in special_card.race
            for special_card in player.special_cards
        )
        if (
            constants.race.FIELD not in card.race
            and existing_non_field_cards >= 5
        ):
            self.board.show_popup("Your Spell/Trap zone is full.")
            return True

        player.hand.remove(card)
        player.special_cards.append(card)
        card.position = constants.possition.DEFENSE
        card.summon = False
        card.is_face_up = False
        card.can_be_selected = True
        return True

    def allow_use_spell(self, card):
        if (self.board.current_player.turn_phase == (constants.phase.DRAW ) and constants.race.QUICK_SPELL in card.race) \
            or not (self.board.current_player.turn_phase == (constants.phase.DRAW)): 
            return True
        return False
        
    def battle_card_clicked(self, card):    
        if self.pending_fusion_spell is not None:
            self.select_fusion_material(card)
            return
        if not self.special_card_selected == None :
            self.handle_special_card(card)  
        if self.tributes > 0:
            self.tribute_monster(card)            
        else:
            if self.board.current_player.turn_phase == constants.phase.BATTLE:
                if (
                    card in self.board.current_player.battle_cards
                    and card.current_position == constants.possition.ATTACK
                    and card.is_face_up
                ):
                    if card in self.board.current_player.is_attacking:
                        self.board.show_popup("This monster has already attacked this turn.")
                        return
                    if self.board.attacking_card == None:
                        self.board.attacking_card = card
                        self.board.attacking_card.selected = True
                        card.action = constants.battle_action.ATTACKING
                    else:
                        self.board.display_ok_message("battle monsters","you already selected a monster to attack, please select opponent monster")
                if card in self.board.opposite_player.battle_cards:
                    if self.board.attacked_card == None:
                        self.board.attacked_card = card
                        self.board.attacked_card.selected = True
                if (
                    self.board.attacking_card is not None
                    and not self.board.opposite_player.battle_cards
                ):
                    self.resolve_battle()
                elif self.board.attacking_card is not None and self.board.attacked_card is not None:
                    self.resolve_battle()
            else:
                self.board.display_ok_message("not battle phase", "please wait for battle phase to select monster")


    def resolve_battle(self):
        attacker = self.board.attacking_card
        defender = self.board.attacked_card
        if attacker is None:
            return

        flipped_defender = defender is not None and not defender.is_face_up
        defender_owner = None
        if flipped_defender:
            defender_owner = next(
                (
                    owner
                    for owner in (
                        self.board.current_player,
                        self.board.opposite_player,
                    )
                    if defender in owner.battle_cards
                ),
                None,
            )
            defender.is_face_up = True

        resolve_battle(self.board, attacker, defender)
        if flipped_defender:
            self.activate_flip_effect(defender, defender_owner)
        self.board.current_player.is_attacking.append(attacker)
        attacker.selected = False
        attacker.action = None
        if defender is not None:
            defender.selected = False
        self.board.attacking_card = None
        self.board.attacked_card = None

    def activate_flip_effect(self, monster, owner=None):
        effect_class = monster_effects.FLIP_EFFECT_REGISTRY.get(monster.name)
        if effect_class is None:
            return False

        effect_owner = owner or next(
            (
                player
                for player in (
                    self.board.current_player,
                    self.board.opposite_player,
                )
                if monster in player.battle_cards or monster in player.graveyard
            ),
            self.board.current_player,
        )
        targets = effect_class.get_valid_targets(self._board_for_player(effect_owner))
        if not targets:
            return False

        prompt_target = getattr(self.board, "prompt_card_target", None)
        if prompt_target is not None:
            self.pending_monster_effect = {
                "effect_class": effect_class,
                "monster": monster,
                "owner": effect_owner,
                "targets": targets,
            }
            prompt_target(
                effect_owner,
                targets,
                f"Click on the {effect_class.target_label} you wish to "
                f"{effect_class.action_label.lower()}.",
            )
            return True

        chooser = getattr(self.board, "choose_monster_effect_target", None)
        if chooser is None:
            chooser = getattr(self.board, "choose_chain_target", None)
        if chooser is None and len(targets) == 1:
            target = targets[0]
        elif chooser is None:
            self.board.show_popup(
                f"Choose a target to resolve {monster.name}'s flip effect."
            )
            return False
        else:
            target = chooser(effect_owner, targets, monster.name)
        if target not in targets:
            return False

        self.resolve_chain(
            lambda: effect_class.activate(self.board, target),
            effect_owner,
            constants.events.MONSTER_FLIPPED,
            monster,
            initial_label=f"{monster.name}: {effect_class.action_label.lower()} {target.name}",
        )
        return True

    def select_monster_effect_target(self, target):
        pending = self.pending_monster_effect
        if pending is None or target not in pending["targets"]:
            return False

        self.pending_monster_effect = None
        clear_prompt = getattr(self.board, "clear_card_target_prompt", None)
        if clear_prompt is not None:
            clear_prompt()
        effect_class = pending["effect_class"]
        monster = pending["monster"]
        owner = pending["owner"]
        self.resolve_chain(
            lambda: effect_class.activate(self.board, target),
            owner,
            constants.events.MONSTER_FLIPPED,
            monster,
            initial_label=(
                f"{monster.name}: {effect_class.action_label.lower()} {target.name}"
            ),
        )
        return True
                        
    def set_new_life_points(self, life_points_player, life_points_change):
        life_points_player.life_points = max(
            0, life_points_player.life_points - life_points_change
        )

    def tribute_monster(self, card):
        self.tributes -= 1
        self.board.current_player.monsters_to_tribute.append(card)
        card.selected = True      
        if self.tributes == 0:
            if len(self.board.current_player.monsters_to_tribute) == 2:
                constants.destroy_card(self.board, self.board.current_player.monsters_to_tribute[1])            
            constants.destroy_card(self.board, self.board.current_player.monsters_to_tribute[0])                
            self.board.current_player.monsters_to_tribute.clear()
            summoned_card = self.board.current_player.tribute_monster
            self.board.current_player.battle_cards.append(summoned_card)
            self.board.current_player.hand.remove(summoned_card)
            self.board.current_player.has_summoned_this_turn = True
            summoned_card.summoned_this_turn = True
            summoned_card.can_be_selected = False
            if summoned_card.summon:
                summoned_card.is_face_up = True
            self.apply_active_field_spells_to_card(summoned_card)
            self.board.current_player.tribute_monster = None
            self.check_trap_triggers(constants.events.ON_SUMMON, summoned_card)

    def activate_field_spell(self, card):
        player = self.board.current_player
        if player.turn_phase not in (constants.phase.MAIN1, constants.phase.MAIN2):
            self.board.show_popup("Field Spells can only be activated in Main Phase 1 or Main Phase 2.")
            return False

        spell_class = spell_cards.CARD_REGISTRY.get(card.name)
        if spell_class is None:
            self.board.show_popup(f"No effect is registered for {card.name}.")
            return False
        if getattr(card, "_active_spell", None) is not None:
            return True

        existing_field_cards = [
            field_card
            for field_card in player.special_cards
            if constants.race.FIELD in field_card.race
        ]
        if card in player.hand and len(player.special_cards) - len(existing_field_cards) >= 5:
            self.board.show_popup("Your Spell/Trap zone is full.")
            return False

        active_spell = spell_class(original_card=card)
        self.resolve_chain(
            lambda: self._resolve_field_spell_activation(
                player, card, existing_field_cards, active_spell
            ),
            player,
            constants.events.SPELL_ACTIVATED,
            initial_label=active_spell.name,
        )
        return True

    def _resolve_field_spell_activation(self, player, card, previous_cards, spell):
        if card.name == constants.special_card_effects.YAMI:
            previous_cards = list(previous_cards)
            for owner in (self.board.p1, self.board.p2):
                for field_card in owner.special_cards:
                    if (
                        field_card.name == constants.special_card_effects.YAMI
                        and field_card is not card
                        and all(field_card is not previous for previous in previous_cards)
                    ):
                        previous_cards.append(field_card)

        for old_card in previous_cards:
            old_spell = getattr(old_card, "_active_spell", None)
            if old_spell is not None:
                old_spell.deactivate(None)
            constants.destroy_card(self.board, old_card)

        if card in player.hand:
            player.hand.remove(card)
            player.special_cards.append(card)
        card.is_face_up = True
        card.can_be_selected = False
        spell.get_valid_targets(self.board)
        for owner in (self.board.p1, self.board.p2):
            for monster in list(owner.battle_cards):
                if spell.target_filter is not None and spell.target_filter(monster):
                    spell.activate_spell_on_card(monster)
        card._active_spell = spell

    def apply_active_field_spells_to_card(self, monster):
        for owner in (self.board.p1, self.board.p2):
            for field_card in owner.special_cards:
                if constants.race.FIELD not in field_card.race:
                    continue
                active_spell = getattr(field_card, "_active_spell", None)
                if (
                    active_spell is not None
                    and active_spell.target_filter is not None
                    and active_spell.target_filter(monster)
                ):
                    active_spell.activate_spell_on_card(monster)

    def start_fusion_summon(self, polymerization):
        player = self.board.current_player
        if player.turn_phase not in (constants.phase.MAIN1, constants.phase.MAIN2):
            self.board.show_popup("Polymerization can only be activated in a Main Phase.")
            return False
        if polymerization not in player.hand and polymerization not in player.special_cards:
            self.board.show_popup("Polymerization must be in your hand or Spell/Trap zone.")
            return False
        if len(player.battle_cards) >= 5:
            self.board.show_popup("Your monster zone is full.")
            return False
        if len(self._fusion_material_candidates(player)) < 2:
            self.board.show_popup("You need at least 2 monsters in your hand or on your field.")
            return False
        if not player.extra_deck:
            self.board.show_popup("Your Extra Deck has no Fusion Monsters.")
            return False

        self.pending_fusion_spell = polymerization
        self.fusion_materials = []
        polymerization.selected = True
        self.board.show_popup("Select 2 different monsters from your hand or field.")
        return True

    @staticmethod
    def _fusion_material_candidates(player):
        return [
            card
            for card in player.hand + player.battle_cards
            if constants.card_types.MONSTER in card.type
        ]

    @staticmethod
    def _required_fusion_materials(fusion_card):
        description = fusion_card.description or ""
        quoted_names = re.findall(r'"([^"]+)"', description)
        if len(quoted_names) >= 2:
            return quoted_names[:2]

        recipe = re.search(
            r"fusion\s+of\s+(.+?)(?:[.!]|$)",
            description,
            flags=re.IGNORECASE,
        )
        if recipe is None:
            return None
        materials = re.split(r"\s+and\s+", recipe.group(1), maxsplit=1)
        if len(materials) != 2:
            return None
        return [
            re.sub(r"^\s*\d+\s+", "", material).strip(' "\'')
            for material in materials
        ]

    def select_fusion_material(self, card):
        player = self.board.current_player
        if card not in self._fusion_material_candidates(player):
            self.board.show_popup("Choose a monster from your hand or field as material.")
            return False
        if card in self.fusion_materials:
            self.board.show_popup("Select two different monsters.")
            return False

        card.selected = True
        self.fusion_materials.append(card)
        if len(self.fusion_materials) < 2:
            self.board.show_popup("Select one more monster as Fusion Material.")
            return True

        material_names = Counter(material.name.casefold() for material in self.fusion_materials)
        valid_fusions = []
        for fusion_card in player.extra_deck:
            required = self._required_fusion_materials(fusion_card)
            if required is not None and not (
                Counter(name.casefold() for name in required) - material_names
            ):
                valid_fusions.append(fusion_card)
        if not valid_fusions:
            self.board.show_popup(
                "Those monsters do not match a Fusion Monster's listed materials."
            )
            self._clear_fusion_materials()
            return False

        fusion_card = self.board.choose_fusion_monster(valid_fusions)
        if fusion_card is None:
            self._clear_fusion_materials()
            self.cancel_fusion_summon()
            return False

        return self.complete_fusion_summon(fusion_card)

    def complete_fusion_summon(self, fusion_card):
        player = self.board.current_player
        if fusion_card not in player.extra_deck or len(player.battle_cards) >= 5:
            self.cancel_fusion_summon()
            return False

        materials = list(self.fusion_materials)
        polymerization = self.pending_fusion_spell
        for material in materials:
            constants.destroy_card(self.board, material)
        constants.destroy_card(self.board, polymerization)
        player.extra_deck.remove(fusion_card)
        fusion_card.position = constants.possition.ATTACK
        fusion_card.is_face_up = True
        fusion_card.summon = True
        fusion_card.summoned_this_turn = True
        fusion_card.can_be_selected = False
        player.battle_cards.append(fusion_card)
        self.apply_active_field_spells_to_card(fusion_card)
        self._clear_fusion_materials()
        self.pending_fusion_spell = None
        self.check_trap_triggers(constants.events.ON_SUMMON, fusion_card)
        return True

    def _clear_fusion_materials(self):
        for material in self.fusion_materials:
            material.selected = False
        self.fusion_materials.clear()

    def cancel_fusion_summon(self):
        self._clear_fusion_materials()
        if self.pending_fusion_spell is not None:
            self.pending_fusion_spell.selected = False
        self.pending_fusion_spell = None


            
    def handle_special_card(self, card):  
        card_name = self.special_card_selected.name 
        card_class = spell_cards.CARD_REGISTRY.get(card_name)
        if card_class:
            match self.step:
                case  constants.step.SPECIAL_CARD_SELECED:   
                    self.special_card = card_class(original_card=card)                       
                    if self.special_card.get_valid_targets(self.board) :
                        if self.special_card.require_card_selection:
                            self.step = constants.step.WAIT_FOR_BATTLE_CARD
                            card.is_face_up = True
                            self.board.display_ok_message("select card", "Choose a highlighted target to activate the spell.")
                        else:
                            self.activate_special_card(self.board, None)
                            if getattr(self.special_card.original_card, 'marked_for_graveyard', False):
                                constants.destroy_card(self.board, self.special_card.original_card)
                            self.special_card_selected = None
                    else:
                        self.board.show_popup(constants.messages.NO_CARDS_FOR_EFFECT)                             
                        self.step = constants.step.SPECIAL_CARD_ENDED
                        self.special_card_selected = None
                case constants.step.WAIT_FOR_BATTLE_CARD:
                    self.activate_special_card(self.board, card)   
                    if getattr(self.special_card.original_card, 'marked_for_graveyard', False):
                        constants.destroy_card(self.board, self.special_card.original_card)                     
        else:
            self.board.show_popup("Unknown card effect")          

    def activate_special_card(self, board, card):
        spell = self.special_card
        activating_player = board.current_player
        spell.original_card.is_face_up = True
        spell.original_card.can_be_selected = False
        self.resolve_chain(
            lambda: spell.activate(board, card),
            activating_player,
            constants.events.SPELL_ACTIVATED,
            initial_label=spell.name,
        )
        self.step = constants.step.SPECIAL_CARD_ENDED
        self.special_card_selected = None    

    def check_trap_triggers(self, event_type, summoned_card):
        if (
            event_type != constants.events.ON_SUMMON
            or not summoned_card.summon
            or not summoned_card.is_face_up
        ):
            return
        self.resolve_chain(
            lambda: None,
            self.board.current_player,
            event_type,
            summoned_card,
        )
        self._move_marked_cards_to_graveyard()

    def check_opponenet_quick_spell(self):
        self.resolve_chain(
            lambda: None,
            self.board.current_player,
            constants.events.DRAW,
        )

    def _board_for_player(self, player):
        other_player = (
            self.board.opposite_player
            if player is self.board.current_player
            else self.board.current_player
        )
        return SimpleNamespace(
            current_player=player,
            opposite_player=other_player,
        )

    def _chain_response_candidates(self, player, event_type, event_card, excluded):
        candidates = []
        view = self._board_for_player(player)
        for card in list(player.special_cards):
            if id(card) in excluded or not getattr(card, "can_be_selected", True):
                continue
            card_class = spell_cards.CARD_REGISTRY.get(card.name)
            if card_class is None:
                continue
            spell = card_class(original_card=card)

            if spell.trigger is not None:
                if (
                    card.is_face_up
                    or spell.trigger != event_type
                    or event_card is None
                    or (
                        spell.trigger_opponent_only
                        and event_card not in view.opposite_player.battle_cards
                    )
                    or spell.trigger_condition is None
                    or spell.target_filter is None
                    or not spell.target_filter(event_card)
                    or not spell.trigger_condition(event_card)
                ):
                    continue
                target = event_card
            elif (
                constants.card_types.SPELL in card.type
                and constants.race.QUICK_SPELL in card.race
            ):
                if not spell.get_valid_targets(view):
                    continue
                target = None
            else:
                continue

            candidates.append(
                {
                    "card": card,
                    "spell": spell,
                    "target": target,
                    "board": view,
                    "owner": player,
                    "label": spell.name,
                }
            )
        return candidates

    def resolve_chain(
        self,
        initial_effect,
        initial_player,
        event_type,
        event_card=None,
        initial_label=None,
    ):
        if self.chain_resolving:
            initial_effect()
            return

        links = [
            {
                "effect": initial_effect,
                "owner": initial_player,
                "card": None,
                "label": initial_label or str(event_type),
            }
        ]
        excluded_cards = set()
        priority_player = (
            self.board.opposite_player
            if initial_player is self.board.current_player
            else self.board.current_player
        )
        consecutive_passes = 0

        while consecutive_passes < 2:
            candidates = self._chain_response_candidates(
                priority_player, event_type, event_card, excluded_cards
            )
            if not candidates:
                consecutive_passes += 1
                priority_player = (
                    self.board.opposite_player
                    if priority_player is self.board.current_player
                    else self.board.current_player
                )
                continue

            chooser = getattr(self.board, "choose_chain_response", None)
            selected = (
                chooser(
                    priority_player,
                    candidates,
                    [link["label"] for link in links],
                )
                if chooser is not None
                else self._ask_for_chain_response(priority_player, candidates)
            )
            if selected is None:
                consecutive_passes += 1
                priority_player = (
                    self.board.opposite_player
                    if priority_player is self.board.current_player
                    else self.board.current_player
                )
                continue

            selected_link = next(
                candidate for candidate in candidates
                if candidate["card"] is selected
            )
            if (
                selected_link["spell"].require_card_selection
                and selected_link["spell"].trigger is None
            ):
                selected_link["target"] = self.board.choose_chain_target(
                    priority_player,
                    selected_link["spell"].valid_cards,
                    selected_link["spell"].name,
                )
                if selected_link["target"] is None:
                    consecutive_passes += 1
                    priority_player = (
                        self.board.opposite_player
                        if priority_player is self.board.current_player
                        else self.board.current_player
                    )
                    continue
            selected_link["card"].is_face_up = True
            selected_link["card"].can_be_selected = False
            excluded_cards.add(id(selected_link["card"]))
            links.append(
                {
                    "effect": lambda link=selected_link: link["spell"].activate(
                        link["board"], link["target"]
                    ),
                    "owner": priority_player,
                    "card": selected_link["card"],
                    "label": selected_link["label"],
                }
            )
            consecutive_passes = 0
            priority_player = (
                self.board.opposite_player
                if priority_player is self.board.current_player
                else self.board.current_player
            )

        self.chain_resolving = True
        try:
            for link in reversed(links):
                logger = getattr(self.board, "log_effect_resolution", None)
                if logger is not None:
                    logger(
                        f"{link['owner'].name}: resolving "
                        f"{link['card'].name if link['card'] is not None else link['label']}"
                    )
                link["effect"]()
        finally:
            self.chain_resolving = False
        self._move_marked_cards_to_graveyard()

    def _ask_for_chain_response(self, player, candidates):
        for candidate in candidates:
            if self.board.ask_yes_no(
                "Chain Response",
                f"{player.name}, activate {candidate['label']}?",
            ):
                return candidate["card"]
        return None

    def _move_marked_cards_to_graveyard(self):
        for owner in (self.board.current_player, self.board.opposite_player):
            for card in list(owner.special_cards):
                if getattr(card, "marked_for_graveyard", False):
                    constants.destroy_card(self.board, card)

    def get_special_card(self, card, summoned_card):
        if card.name in spell_cards.CARD_REGISTRY:
        # This creates the class instance automatically
            return spell_cards.CARD_REGISTRY[card.name](original_card=card) 
        return card

    
             

            
            

                    
