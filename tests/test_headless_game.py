import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import constants
from board import GameEngine
from game_engine.combat import resolve_battle
from game_engine.simulate import simulate_game
from models.card import Card
from models.player import Player
from models.special_cards import spell_cards
from models.special_cards import monster_effects
from phase_managers.phase_manager import PhaseManager


class HeadlessGameTests(unittest.TestCase):
    def setUp(self):
        self.attacker_owner = Player("attacker", [], constants.player_is_1)
        self.defender_owner = Player("defender", [], constants.player_is_2)
        self.board = SimpleNamespace(
            current_player=self.attacker_owner,
            opposite_player=self.defender_owner,
            p1=self.attacker_owner,
            p2=self.defender_owner,
            attacking_card=None,
            attacked_card=None,
            show_popup=Mock(),
        )

    @staticmethod
    def monster(name, attack, defense, position=constants.possition.ATTACK):
        monster = Card(
            {
                "name": name,
                "type": constants.card_types.MONSTER,
                "attribute": "earth",
                "level": 4,
                "spell speed": None,
                "atk": attack,
                "def": defense,
                "race": constants.race.WARRIOR,
                "card_images": [{"image_url": ""}],
                "desc": "",
            }
        )
        monster.set_position(position)
        return monster

    def test_life_point_effect_is_not_reapplied_when_read(self):
        player = self.attacker_owner
        player.effect_on_card["bonus"] = {"life_points": 500}

        self.assertEqual(player.life_points, 8500)
        self.assertEqual(player.life_points, 8500)

    def test_graveyard_monsters_excludes_destroyed_spells(self):
        monster = SimpleNamespace(type="normal monster")
        spell = SimpleNamespace(type="spell card")
        self.attacker_owner.graveyard.extend([monster, spell])

        self.assertEqual(self.attacker_owner.graveyard_monsters, [monster])

    def test_graveyard_spell_traps_lists_used_spells_and_traps(self):
        monster = SimpleNamespace(type="normal monster")
        spell = SimpleNamespace(type="spell card")
        trap = SimpleNamespace(type="trap card")
        self.attacker_owner.graveyard.extend([monster, spell, trap])

        self.assertEqual(self.attacker_owner.graveyard_spell_traps, [spell, trap])
        self.assertEqual(
            GameEngine.graveyard_summary(self.attacker_owner),
            "Graveyard\nMonsters: 1 | Spells/Traps: 2",
        )

    def test_start_banner_names_starting_player_and_schedules_two_second_hide(self):
        engine = GameEngine.__new__(GameEngine)
        engine.current_player = SimpleNamespace(name="Starter")
        engine.canvas_width = 1000
        engine.canvas_height = 800
        engine.board_canvas = Mock()
        engine.master = Mock()

        engine.show_start_banner()

        texts = [
            call.kwargs.get("text")
            for call in engine.board_canvas.create_text.call_args_list
        ]
        self.assertIn("Starter is starting", texts)
        engine.master.after.assert_called_once()
        self.assertEqual(engine.master.after.call_args.args[0], 2000)
        engine.master.after.call_args.args[1]()
        engine.board_canvas.delete.assert_called_once_with("start_banner")

    def test_revive_keeps_monster_in_graveyard_when_field_is_full(self):
        monster = SimpleNamespace(type=constants.card_types.MONSTER)
        self.attacker_owner.battle_cards.extend([object() for _ in range(5)])
        self.attacker_owner.graveyard.append(monster)

        revived = self.attacker_owner.revive_card_from_graveyard()

        self.assertFalse(revived)
        self.assertEqual(self.attacker_owner.graveyard, [monster])

    def test_revive_moves_monster_when_field_has_space(self):
        monster = SimpleNamespace(type=constants.card_types.MONSTER)
        self.attacker_owner.graveyard.append(monster)

        revived = self.attacker_owner.revive_card_from_graveyard()

        self.assertTrue(revived)
        self.assertEqual(self.attacker_owner.battle_cards, [monster])
        self.assertEqual(self.attacker_owner.graveyard, [])

    def test_attack_position_battle_destroys_loser_and_deals_difference(self):
        attacker = self.monster("attacker", 1800, 1000)
        defender = self.monster("defender", 1200, 900)
        self.attacker_owner.battle_cards.append(attacker)
        self.defender_owner.battle_cards.append(defender)

        result = resolve_battle(self.board, attacker, defender)

        self.assertEqual(result.outcome, "defender_destroyed")
        self.assertEqual(self.defender_owner.life_points, 7400)
        self.assertEqual(self.defender_owner.graveyard, [defender])

    def test_defense_position_battle_does_not_deal_life_damage(self):
        attacker = self.monster("attacker", 1800, 1000)
        defender = self.monster(
            "defender", 1200, 2000, constants.possition.DEFENSE
        )
        self.attacker_owner.battle_cards.append(attacker)
        self.defender_owner.battle_cards.append(defender)

        result = resolve_battle(self.board, attacker, defender)

        self.assertEqual(result.outcome, "stalemate")
        self.assertEqual(self.attacker_owner.life_points, 8000)
        self.assertEqual(self.defender_owner.life_points, 8000)
        self.assertIn(defender, self.defender_owner.battle_cards)

    def test_defense_position_battle_destroys_weaker_defender_without_damage(self):
        attacker = self.monster("attacker", 2100, 1000)
        defender = self.monster(
            "defender", 1200, 2000, constants.possition.DEFENSE
        )
        self.attacker_owner.battle_cards.append(attacker)
        self.defender_owner.battle_cards.append(defender)

        result = resolve_battle(self.board, attacker, defender)

        self.assertEqual(result.outcome, "defender_destroyed")
        self.assertEqual(self.attacker_owner.life_points, 8000)
        self.assertEqual(self.defender_owner.life_points, 8000)
        self.assertEqual(self.defender_owner.graveyard, [defender])

    def test_weaker_attacker_is_destroyed_and_takes_attack_difference(self):
        attacker = self.monster("attacker", 1000, 900)
        defender = self.monster("defender", 1800, 1400)
        self.attacker_owner.battle_cards.append(attacker)
        self.defender_owner.battle_cards.append(defender)

        result = resolve_battle(self.board, attacker, defender)

        self.assertEqual(result.outcome, "attacker_destroyed")
        self.assertEqual(result.damage_to_attacker, 800)
        self.assertEqual(self.attacker_owner.life_points, 7200)
        self.assertEqual(self.attacker_owner.graveyard, [attacker])

    def test_man_eater_bug_destroys_selected_monster_when_manually_flipped(self):
        bug = self.monster("man-eater bug", 450, 600, constants.possition.DEFENSE)
        bug.type = "effect monster"
        bug.is_face_up = False
        bug.summoned_this_turn = False
        target = self.monster("target", 1200, 1000)
        self.attacker_owner.battle_cards.extend([bug, target])
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        self.board.choose_monster_effect_target = Mock(return_value=target)
        manager = PhaseManager(self.board)

        changed = manager.right_click(self.attacker_owner, bug)

        self.assertTrue(changed)
        self.assertTrue(bug.is_face_up)
        self.assertEqual(self.attacker_owner.graveyard, [target])
        self.assertIn(bug, self.attacker_owner.battle_cards)
        self.board.choose_monster_effect_target.assert_called_once()

    def test_man_eater_prompts_to_click_target_without_revealing_hidden_card_name(self):
        bug = self.monster("man-eater bug", 450, 600, constants.possition.DEFENSE)
        bug.type = "effect monster"
        bug.is_face_up = False
        bug.summoned_this_turn = False
        hidden_target = self.monster("secret target", 1200, 1000)
        hidden_target.is_face_up = False
        self.attacker_owner.battle_cards.extend([bug, hidden_target])
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        self.board.prompt_card_target = Mock()
        self.board.clear_card_target_prompt = Mock()
        manager = PhaseManager(self.board)

        manager.right_click(self.attacker_owner, bug)

        prompt = self.board.prompt_card_target.call_args.args[2]
        self.assertEqual(prompt, "Click on the monster you wish to destroy.")
        self.assertNotIn(hidden_target.name, prompt)
        self.assertIsNotNone(manager.pending_monster_effect)
        self.assertTrue(manager.select_monster_effect_target(hidden_target))
        self.assertIn(hidden_target, self.attacker_owner.graveyard)
        self.board.clear_card_target_prompt.assert_called_once()

    def test_man_eater_bug_flip_effect_resolves_after_being_attacked(self):
        attacker = self.monster("attacker", 1800, 1000)
        bug = self.monster("man-eater bug", 450, 600, constants.possition.DEFENSE)
        bug.type = "effect monster"
        bug.is_face_up = False
        target = self.monster("target", 1200, 1000)
        self.attacker_owner.battle_cards.extend([attacker, target])
        self.defender_owner.battle_cards.append(bug)
        self.board.attacking_card = attacker
        self.board.attacked_card = bug
        self.board.choose_monster_effect_target = Mock(return_value=target)
        manager = PhaseManager(self.board)

        manager.resolve_battle()

        self.assertTrue(bug.is_face_up)
        self.assertIn(bug, self.defender_owner.graveyard)
        self.assertIn(target, self.attacker_owner.graveyard)
        self.board.choose_monster_effect_target.assert_called_once()

    def test_hane_hane_returns_selected_monster_to_its_owner_hand(self):
        hane = self.monster("hane-hane", 450, 500, constants.possition.DEFENSE)
        hane.type = "effect monster"
        hane.is_face_up = False
        hane.summoned_this_turn = False
        target = self.monster("target", 1200, 1000)
        self.defender_owner.battle_cards.append(target)
        self.attacker_owner.battle_cards.append(hane)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        self.board.choose_monster_effect_target = Mock(return_value=target)
        manager = PhaseManager(self.board)

        manager.right_click(self.attacker_owner, hane)

        self.assertIn(target, self.defender_owner.hand)
        self.assertNotIn(target, self.defender_owner.battle_cards)

    def test_old_vindictive_magician_can_only_destroy_opponent_monsters(self):
        magician = self.monster(
            "old vindictive magician", 450, 600, constants.possition.DEFENSE
        )
        magician.type = "effect monster"
        magician.is_face_up = False
        magician.summoned_this_turn = False
        own_monster = self.monster("own monster", 700, 700)
        opposing_monster = self.monster("opposing monster", 900, 900)
        self.attacker_owner.battle_cards.extend([magician, own_monster])
        self.defender_owner.battle_cards.append(opposing_monster)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        self.board.choose_monster_effect_target = Mock(return_value=opposing_monster)
        manager = PhaseManager(self.board)

        manager.right_click(self.attacker_owner, magician)

        self.assertIn(own_monster, self.attacker_owner.battle_cards)
        self.assertIn(opposing_monster, self.defender_owner.graveyard)

    def test_reaper_of_the_cards_flip_effect_destroys_clicked_trap(self):
        reaper = self.monster(
            "reaper of the cards", 1380, 1930, constants.possition.DEFENSE
        )
        reaper.type = "effect monster"
        reaper.is_face_up = False
        reaper.summoned_this_turn = False
        hidden_trap = self.effect_card(
            "hidden trap",
            "normal",
            constants.card_types.TRAP,
        )
        hidden_trap.is_face_up = False
        self.attacker_owner.battle_cards.append(reaper)
        self.defender_owner.special_cards.append(hidden_trap)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        self.board.prompt_card_target = Mock()
        self.board.clear_card_target_prompt = Mock()
        manager = PhaseManager(self.board)

        manager.right_click(self.attacker_owner, reaper)

        self.assertEqual(
            self.board.prompt_card_target.call_args.args[2],
            "Click on the Trap you wish to destroy.",
        )
        self.assertTrue(manager.select_monster_effect_target(hidden_trap))
        self.assertIn(hidden_trap, self.defender_owner.graveyard)

    def test_fissure_activates_immediately_from_hand(self):
        own_lowest = self.monster("own lowest", 100, 500)
        weakest_opponent = self.monster("weakest opponent", 500, 500)
        stronger_opponent = self.monster("stronger opponent", 1200, 900)
        self.attacker_owner.battle_cards.append(own_lowest)
        self.defender_owner.battle_cards.extend(
            [stronger_opponent, weakest_opponent]
        )
        fissure = self.effect_card("fissure", "normal")
        self.attacker_owner.hand.append(fissure)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        manager = PhaseManager(self.board)

        manager.hand_card_clicked(fissure)

        self.assertIn(weakest_opponent, self.defender_owner.graveyard)
        self.assertIn(own_lowest, self.attacker_owner.battle_cards)
        self.assertIn(stronger_opponent, self.defender_owner.battle_cards)
        self.assertIn(fissure, self.attacker_owner.graveyard)

    def test_trap_can_be_set_and_triggered_during_the_same_turn(self):
        trap = self.effect_card(
            constants.special_card_effects.TRAP_HOLE,
            "normal",
            constants.card_types.TRAP,
        )
        self.attacker_owner.hand.append(trap)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        manager = PhaseManager(self.board)

        manager.set_hand_spell_or_trap(trap)
        summoned = self.monster("summoned", 1500, 1000)
        summoned.summon = True
        summoned.is_face_up = True
        self.defender_owner.battle_cards.append(summoned)
        candidates = manager._chain_response_candidates(
            self.attacker_owner,
            constants.events.ON_SUMMON,
            summoned,
            set(),
        )

        self.assertIn(trap, self.attacker_owner.special_cards)
        self.assertFalse(trap.is_face_up)
        self.assertTrue(trap.can_be_selected)
        self.assertEqual([candidate["card"] for candidate in candidates], [trap])

        self.defender_owner.battle_cards.remove(summoned)
        self.attacker_owner.battle_cards.append(summoned)
        own_summon_candidates = manager._chain_response_candidates(
            self.attacker_owner,
            constants.events.ON_SUMMON,
            summoned,
            set(),
        )
        self.assertEqual(own_summon_candidates, [])

    def test_end_turn_with_seven_cards_requires_discarding_one_from_hand(self):
        engine = GameEngine.__new__(GameEngine)
        engine.current_player = self.attacker_owner
        engine.opposite_player = self.defender_owner
        engine.p1 = self.attacker_owner
        engine.p2 = self.defender_owner
        engine.game_over = False
        engine.canvas_width = 1000
        engine.canvas_height = 800
        engine.board_canvas = Mock()
        engine.action_prompt_id = None
        engine.pending_hand_discard = False
        engine.phase_text_id = "phase"
        engine.change_current_player = Mock()
        engine.refresh_board = Mock()
        engine.show_popup = Mock()
        engine.phase_manager = PhaseManager(engine)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        self.attacker_owner.hand.extend(
            [self.monster(f"hand card {index}", 100, 100) for index in range(7)]
        )

        engine.phase_button_clicked(constants.phase.END)

        self.assertTrue(engine.pending_hand_discard)
        self.assertEqual(self.attacker_owner.turn_phase, constants.phase.MAIN1)
        self.assertIn(
            "destroy one card from your hand",
            engine.board_canvas.create_text.call_args.kwargs["text"],
        )

        discarded = self.attacker_owner.hand[0]
        self.assertTrue(engine.complete_hand_discard(discarded))
        self.assertEqual(len(self.attacker_owner.hand), 6)
        self.assertIn(discarded, self.attacker_owner.graveyard)
        engine.change_current_player.assert_called_once()
        engine.refresh_board.assert_called_once()

    def test_right_clicking_own_set_card_reveals_it_and_no_declines_activation(self):
        engine = GameEngine.__new__(GameEngine)
        engine.current_player = self.attacker_owner
        engine.refresh_board = Mock()
        engine.ask_yes_no = Mock(return_value=False)
        engine.phase_manager = Mock()
        set_spell = self.effect_card("set spell", "normal")
        self.attacker_owner.special_cards.append(set_spell)

        handled = engine.activate_face_down_special(set_spell)

        self.assertTrue(handled)
        self.assertTrue(set_spell.is_face_up)
        engine.ask_yes_no.assert_called_once_with(
            "Activate card?",
            "Activate set spell?",
        )
        engine.phase_manager.special_card_clicked.assert_not_called()
        engine.refresh_board.assert_called_once()

    def test_right_clicking_own_set_card_can_confirm_activation(self):
        engine = GameEngine.__new__(GameEngine)
        engine.current_player = self.attacker_owner
        engine.refresh_board = Mock()
        engine.ask_yes_no = Mock(return_value=True)
        engine.phase_manager = Mock()
        set_spell = self.effect_card("set spell", "normal")
        self.attacker_owner.special_cards.append(set_spell)

        engine.activate_face_down_special(set_spell)

        engine.phase_manager.special_card_clicked.assert_called_once_with(set_spell)
        self.assertEqual(engine.refresh_board.call_count, 2)

    def test_set_spell_can_be_activated_immediately_with_left_click(self):
        weakest = self.monster("weakest", 500, 500)
        stronger = self.monster("stronger", 1200, 900)
        self.defender_owner.battle_cards.extend([stronger, weakest])
        fissure = self.effect_card("fissure", "normal")
        self.attacker_owner.hand.append(fissure)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        manager = PhaseManager(self.board)

        manager.set_hand_spell_or_trap(fissure)
        manager.special_card_clicked(fissure)

        self.assertIn(weakest, self.defender_owner.graveyard)
        self.assertIn(fissure, self.attacker_owner.graveyard)
        self.assertNotIn(fissure, self.attacker_owner.special_cards)

    def test_spell_target_highlighting_draws_only_valid_battlefield_targets(self):
        engine = GameEngine.__new__(GameEngine)
        target = self.monster("valid target", 1000, 900)
        target.x_position = 40
        target.y_position = 80
        self.attacker_owner.battle_cards.append(target)
        engine.current_player = self.attacker_owner
        engine.opposite_player = self.defender_owner
        engine.board_canvas = Mock()
        engine.phase_manager = SimpleNamespace(
            step=constants.step.WAIT_FOR_BATTLE_CARD,
            special_card=SimpleNamespace(valid_cards=[target]),
        )

        engine.draw_spell_target_highlights()

        engine.board_canvas.create_rectangle.assert_called_once()
        self.assertEqual(
            engine.board_canvas.create_rectangle.call_args.kwargs["outline"],
            "#00ff00",
        )

    def test_type_modifier_is_available_only_with_matching_battlefield_monster(self):
        engine = GameEngine.__new__(GameEngine)
        engine.current_player = self.attacker_owner
        engine.opposite_player = self.defender_owner
        engine.attacker = None
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        wasteland = self.effect_card(
            constants.special_card_effects.WASTELAND, constants.race.FIELD
        )
        self.attacker_owner.hand.append(wasteland)

        self.assertFalse(engine._spell_has_available_battlefield_target(wasteland))

        dinosaur = self.monster("dinosaur", 1000, 900)
        dinosaur.race = constants.race.DINOSAUR
        self.defender_owner.battle_cards.append(dinosaur)

        self.assertTrue(engine._spell_has_available_battlefield_target(wasteland))
        engine.board_canvas = Mock()
        engine.display_card_in_focus = Mock()
        wasteland.x_position = 20
        wasteland.y_position = 30

        engine.handle_card_hover(None, wasteland)

        self.assertTrue(
            any(
                call.kwargs.get("text") == "Available!"
                for call in engine.board_canvas.create_text.call_args_list
            )
        )

    def test_chain_resolution_writes_to_effect_log_when_available(self):
        messages = []
        self.board.log_effect_resolution = messages.append
        manager = PhaseManager(self.board)

        manager.resolve_chain(
            lambda: None,
            self.attacker_owner,
            constants.events.SPELL_ACTIVATED,
            initial_label="Fissure",
        )

        self.assertEqual(messages, ["attacker: resolving Fissure"])

    def test_direct_attack_deals_damage_to_opponent(self):
        attacker = self.monster("attacker", 1700, 900)

        result = resolve_battle(self.board, attacker)

        self.assertEqual(result.outcome, "direct_attack")
        self.assertEqual(result.damage_to_defender, 1700)
        self.assertEqual(self.defender_owner.life_points, 6300)

    def test_equal_attack_position_battle_destroys_both(self):
        attacker = self.monster("attacker", 1500, 1000)
        defender = self.monster("defender", 1500, 900)
        self.attacker_owner.battle_cards.append(attacker)
        self.defender_owner.battle_cards.append(defender)

        result = resolve_battle(self.board, attacker, defender)

        self.assertEqual(result.outcome, "both_destroyed")
        self.assertEqual(self.attacker_owner.graveyard, [attacker])
        self.assertEqual(self.defender_owner.graveyard, [defender])

    def test_self_play_is_repeatable_for_a_seed(self):
        first = simulate_game(23)
        second = simulate_game(23)

        self.assertEqual(
            (first.winner, first.reason, first.turns, first.log),
            (second.winner, second.reason, second.turns, second.log),
        )

    def test_trap_hole_prompts_and_activates_on_opponent_summon(self):
        trap = SimpleNamespace(
            name=constants.special_card_effects.TRAP_HOLE,
            type=constants.card_types.TRAP,
            race="normal",
            is_face_up=False,
            marked_for_graveyard=False,
            special_cards=[],
            special_spells=[],
        )
        monster = self.monster("summoned monster", 1500, 1000)
        monster.type = constants.card_types.MONSTER
        monster.summon = True
        monster.is_face_up = True
        self.attacker_owner.battle_cards.append(monster)
        self.defender_owner.special_cards.append(trap)
        self.board.ask_yes_no = Mock(return_value=True)
        manager = PhaseManager(self.board)

        manager.check_trap_triggers(constants.events.ON_SUMMON, monster)

        self.board.ask_yes_no.assert_called_once()
        self.assertEqual(self.attacker_owner.graveyard, [monster])
        self.assertEqual(self.defender_owner.graveyard, [trap])

    def test_trap_hole_does_not_prompt_on_draw(self):
        trap = SimpleNamespace(
            name=constants.special_card_effects.TRAP_HOLE,
            type=constants.card_types.TRAP,
            race="normal",
            is_face_up=False,
            marked_for_graveyard=False,
            special_cards=[],
            special_spells=[],
        )
        drawn_monster = self.monster("drawn monster", 1500, 1000)
        drawn_monster.type = constants.card_types.MONSTER
        drawn_monster.summon = True
        drawn_monster.is_face_up = True
        self.defender_owner.special_cards.append(trap)
        self.board.ask_yes_no = Mock(return_value=True)
        manager = PhaseManager(self.board)

        manager.check_trap_triggers(constants.events.DRAW, drawn_monster)

        self.board.ask_yes_no.assert_not_called()
        self.assertEqual(self.defender_owner.special_cards, [trap])

    def test_trap_hole_does_not_prompt_for_set_monster(self):
        trap = SimpleNamespace(
            name=constants.special_card_effects.TRAP_HOLE,
            type=constants.card_types.TRAP,
            race="normal",
            is_face_up=False,
            marked_for_graveyard=False,
            special_cards=[],
            special_spells=[],
        )
        set_monster = self.monster("set monster", 1500, 1000)
        set_monster.type = constants.card_types.MONSTER
        set_monster.summon = False
        set_monster.is_face_up = False
        self.defender_owner.special_cards.append(trap)
        self.board.ask_yes_no = Mock(return_value=True)
        manager = PhaseManager(self.board)

        manager.check_trap_triggers(constants.events.ON_SUMMON, set_monster)

        self.board.ask_yes_no.assert_not_called()
        self.assertEqual(self.defender_owner.special_cards, [trap])

    def test_life_point_spell_applies_when_clicked_from_hand_in_main_phase(self):
        spell_card = SimpleNamespace(
            name=constants.special_card_effects.HINOTAMA,
            type=constants.card_types.SPELL,
            race="normal",
            marked_for_graveyard=False,
        )
        self.attacker_owner.hand.append(spell_card)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        manager = PhaseManager(self.board)

        manager.hand_card_clicked(spell_card)

        self.assertEqual(self.defender_owner.life_points, 7500)
        self.assertEqual(self.attacker_owner.hand, [])
        self.assertEqual(self.attacker_owner.graveyard, [spell_card])

    def test_life_point_spell_is_rejected_outside_main_phases(self):
        spell_card = SimpleNamespace(
            name=constants.special_card_effects.HINOTAMA,
            type=constants.card_types.SPELL,
            race="normal",
            marked_for_graveyard=False,
        )
        self.attacker_owner.hand.append(spell_card)
        self.attacker_owner.turn_phase = constants.phase.BATTLE
        self.board.show_popup = Mock()
        manager = PhaseManager(self.board)

        manager.hand_card_clicked(spell_card)

        self.assertEqual(self.defender_owner.life_points, 8000)
        self.assertEqual(self.attacker_owner.hand, [spell_card])
        self.board.show_popup.assert_called_once()

    def test_raigeki_destroys_opponent_field_monsters_not_hand_monsters(self):
        field_monster = self.monster("field monster", 1500, 1200)
        hand_monster = self.monster("hand monster", 1000, 900)
        self.defender_owner.battle_cards.append(field_monster)
        self.defender_owner.hand.append(hand_monster)
        raigeki = self.effect_card(
            constants.special_card_effects.RAIGEKI,
            "normal",
        )
        self.attacker_owner.hand.append(raigeki)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        manager = PhaseManager(self.board)

        manager.hand_card_clicked(raigeki)

        self.assertEqual(self.defender_owner.battle_cards, [])
        self.assertEqual(self.defender_owner.graveyard, [field_monster])
        self.assertEqual(self.defender_owner.hand, [hand_monster])
        self.assertIn(raigeki, self.attacker_owner.graveyard)

    def test_zero_life_points_displays_opponent_as_winner(self):
        winner_board = GameEngine.__new__(GameEngine)
        winner_board.p1 = self.attacker_owner
        winner_board.p2 = self.defender_owner
        winner_board.board_canvas = Mock()
        winner_board.canvas_width = 1200
        winner_board.canvas_height = 900
        winner_board.game_over = False
        self.defender_owner.on_defeat = winner_board.show_winner

        self.defender_owner.take_damage(8000)

        texts = [
            call.kwargs.get("text")
            for call in winner_board.board_canvas.create_text.call_args_list
        ]
        self.assertIn("attacker\nHAS WON!", texts)
        winner_board.board_canvas.tag_raise.assert_called_once_with("game_over")
        self.assertTrue(winner_board.game_over)

    def test_red_medicine_heals_when_clicked_from_hand(self):
        spell_card = SimpleNamespace(
            name=constants.special_card_effects.RED_MEDICINE,
            type=constants.card_types.SPELL,
            race="normal",
            marked_for_graveyard=False,
        )
        self.attacker_owner.base_life_points = 8000
        self.attacker_owner.hand.append(spell_card)
        self.attacker_owner.turn_phase = constants.phase.MAIN2
        engine = GameEngine.__new__(GameEngine)
        engine.game_over = False
        engine.pending_hand_discard = False
        engine.current_player = self.attacker_owner
        engine.opposite_player = self.defender_owner
        engine.p1 = self.attacker_owner
        engine.p2 = self.defender_owner
        engine.effect_log_entries = []
        engine.refresh_board = Mock()
        engine.phase_manager = PhaseManager(engine)

        engine.handle_card_click(spell_card)

        self.assertEqual(self.attacker_owner.life_points, 8500)
        self.assertEqual(self.attacker_owner.graveyard, [spell_card])

    def test_latest_yami_replaces_previous_yami_for_both_players(self):
        first_yami = self.effect_card(
            constants.special_card_effects.YAMI, constants.race.FIELD
        )
        second_yami = self.effect_card(
            constants.special_card_effects.YAMI, constants.race.FIELD
        )
        fiend = self.monster("fiend", 1000, 900)
        fiend.race = constants.race.FIEND
        opposing_spellcaster = self.monster("spellcaster", 900, 800)
        opposing_spellcaster.race = constants.race.SPELLCASTER
        self.attacker_owner.battle_cards.append(fiend)
        self.defender_owner.battle_cards.append(opposing_spellcaster)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        self.attacker_owner.hand.append(first_yami)
        manager = PhaseManager(self.board)

        manager.activate_field_spell(first_yami)
        self.assertEqual((fiend.base_attack, opposing_spellcaster.base_attack), (1200, 1100))

        self.board.current_player = self.defender_owner
        self.board.opposite_player = self.attacker_owner
        self.defender_owner.turn_phase = constants.phase.MAIN1
        self.defender_owner.hand.append(second_yami)
        manager.activate_field_spell(second_yami)

        self.assertNotIn(first_yami, self.attacker_owner.special_cards)
        self.assertIn(first_yami, self.attacker_owner.graveyard)
        self.assertIn(second_yami, self.defender_owner.special_cards)
        self.assertEqual((fiend.base_attack, opposing_spellcaster.base_attack), (1200, 1100))

    def test_right_click_changes_eligible_field_monster_position_once(self):
        monster = self.monster("field monster", 1500, 1000)
        monster.summoned_this_turn = False
        monster.has_changed_position_this_turn = False
        monster.is_face_up = True
        self.attacker_owner.battle_cards.append(monster)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        manager = PhaseManager(self.board)

        changed = manager.right_click(self.attacker_owner, monster)
        second_change = manager.right_click(self.attacker_owner, monster)

        self.assertTrue(changed)
        self.assertFalse(second_change)
        self.assertEqual(monster.position, constants.possition.DEFENSE)

    def test_right_click_cannot_change_position_for_monster_summoned_this_turn(self):
        monster = self.monster("new monster", 1500, 1000)
        monster.summoned_this_turn = True
        monster.has_changed_position_this_turn = False
        monster.is_face_up = True
        self.attacker_owner.battle_cards.append(monster)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        manager = PhaseManager(self.board)

        changed = manager.right_click(self.attacker_owner, monster)

        self.assertFalse(changed)
        self.assertEqual(monster.position, constants.possition.ATTACK)

    def test_exodia_wins_after_confirmation_when_all_five_pieces_are_in_hand(self):
        piece_names = (
            "Exodia the Forbidden One",
            "Right Arm of the Forbidden One",
            "Left Arm of the Forbidden One",
            "Right Leg of the Forbidden One",
            "Left Leg of the Forbidden One",
        )
        pieces = [
            self.monster(name, 0, 0)
            for name in piece_names
        ]
        self.attacker_owner.hand.extend(pieces)
        self.board.ask_yes_no = Mock(return_value=True)
        self.board.show_winner = Mock()
        manager = PhaseManager(self.board)

        activated = manager.right_click(self.attacker_owner, pieces[0])

        self.assertTrue(activated)
        self.board.ask_yes_no.assert_called_once_with(
            "Exodia",
            "Would you like to activate Exodia?",
        )
        self.board.show_winner.assert_called_once_with(self.defender_owner)

    def test_exodia_decline_does_not_win_or_set_the_head(self):
        head = self.monster("Exodia the Forbidden One", 0, 0)
        self.attacker_owner.hand.extend(
            [
                head,
                self.monster("Right Arm of the Forbidden One", 0, 0),
                self.monster("Left Arm of the Forbidden One", 0, 0),
                self.monster("Right Leg of the Forbidden One", 0, 0),
                self.monster("Left Leg of the Forbidden One", 0, 0),
            ]
        )
        self.board.ask_yes_no = Mock(return_value=False)
        self.board.show_winner = Mock()
        manager = PhaseManager(self.board)

        manager.right_click(self.attacker_owner, head)

        self.board.show_winner.assert_not_called()
        self.assertIn(head, self.attacker_owner.hand)
        self.assertTrue(head.is_face_up)

    def test_exodia_prompt_requires_all_pieces_in_hand(self):
        head = self.monster("Exodia the Forbidden One", 0, 0)
        self.attacker_owner.hand.extend(
            [
                head,
                self.monster("Right Arm of the Forbidden One", 0, 0),
                self.monster("Left Arm of the Forbidden One", 0, 0),
                self.monster("Right Leg of the Forbidden One", 0, 0),
            ]
        )
        self.board.ask_yes_no = Mock()
        manager = PhaseManager(self.board)

        manager.right_click(self.attacker_owner, head)

        self.board.ask_yes_no.assert_not_called()
        self.assertFalse(head.is_face_up)

    def test_tribute_summon_marks_card_and_checks_summon_traps(self):
        tribute = self.monster("tribute", 1000, 1000)
        summoned = self.monster("tribute summon", 2000, 1500)
        summoned.summon = True
        summoned.is_face_up = False
        self.attacker_owner.battle_cards.append(tribute)
        self.attacker_owner.hand.append(summoned)
        self.attacker_owner.tribute_monster = summoned
        self.attacker_owner.monsters_to_tribute.append(tribute)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        manager = PhaseManager(self.board)
        manager.tributes = 1
        manager.check_trap_triggers = Mock()

        manager.tribute_monster(tribute)

        self.assertIn(summoned, self.attacker_owner.battle_cards)
        self.assertNotIn(summoned, self.attacker_owner.hand)
        self.assertTrue(summoned.summoned_this_turn)
        self.assertTrue(summoned.is_face_up)
        manager.check_trap_triggers.assert_called_once_with(
            constants.events.ON_SUMMON, summoned
        )

    @staticmethod
    def effect_card(name, race, card_type="spell card"):
        return SimpleNamespace(
            name=name,
            race=race,
            type=card_type,
            is_face_up=False,
            selected=False,
            can_be_selected=True,
            marked_for_graveyard=False,
            special_cards=[],
            special_spells=[],
        )

    def test_field_spell_activates_when_clicked_and_replaces_prior_field(self):
        insect = self.monster("insect", 1000, 1000)
        insect.type = constants.card_types.MONSTER
        insect.race = constants.race.INSECT
        insect.effect_on_card = {}
        insect.summoned_this_turn = False
        self.attacker_owner.battle_cards.append(insect)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        forest = self.effect_card(constants.special_card_effects.FOREST, constants.race.FIELD)
        self.attacker_owner.hand.append(forest)
        manager = PhaseManager(self.board)

        manager.hand_card_clicked(forest)

        self.assertEqual(insect.base_attack, 1200)
        self.assertTrue(forest.is_face_up)
        self.assertIn(forest, self.attacker_owner.special_cards)
        self.assertNotIn(forest, insect.special_cards)

        constants.destroy_card(self.board, insect)
        self.assertIn(forest, self.attacker_owner.special_cards)
        self.assertEqual(insect.base_attack, 1000)

        dragon = self.monster("dragon", 1200, 1000)
        dragon.type = constants.card_types.MONSTER
        dragon.race = constants.race.DRAGON
        dragon.effect_on_card = {}
        dragon.special_cards = []
        dragon.special_spells = []
        self.attacker_owner.battle_cards.append(dragon)
        mountain = self.effect_card(constants.special_card_effects.MOUNTAIN, constants.race.FIELD)
        self.attacker_owner.hand.append(mountain)

        manager.hand_card_clicked(mountain)

        self.assertEqual(insect.base_attack, 1000)
        self.assertEqual(dragon.base_attack, 1400)
        self.assertNotIn(forest, self.attacker_owner.special_cards)
        self.assertIn(forest, self.attacker_owner.graveyard)
        self.assertIn(mountain, self.attacker_owner.special_cards)
        new_dragon = self.monster("new dragon", 900, 900)
        new_dragon.race = constants.race.DRAGON
        self.attacker_owner.battle_cards.append(new_dragon)
        manager.apply_active_field_spells_to_card(new_dragon)
        self.assertEqual(new_dragon.base_attack, 1100)

    def test_field_spell_does_not_replace_opponents_field_spell(self):
        own_field = self.effect_card(
            constants.special_card_effects.FOREST, constants.race.FIELD
        )
        opponent_field = self.effect_card(
            constants.special_card_effects.MOUNTAIN, constants.race.FIELD
        )
        self.attacker_owner.special_cards.append(own_field)
        self.defender_owner.special_cards.append(opponent_field)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        manager = PhaseManager(self.board)
        manager.activate_field_spell(
            self.effect_card(
                constants.special_card_effects.SOGEN, constants.race.FIELD
            )
        )

        self.assertIn(opponent_field, self.defender_owner.special_cards)
        self.assertNotIn(own_field, self.attacker_owner.special_cards)

    def test_all_registered_field_spell_modifiers_apply_and_reverse(self):
        field_cases = {
            constants.special_card_effects.FOREST: (
                constants.race.INSECT,
                200,
            ),
            constants.special_card_effects.MOUNTAIN: (
                constants.race.WINGED_BEAST,
                200,
            ),
            constants.special_card_effects.SOGEN: (
                constants.race.WARRIOR,
                200,
            ),
            constants.special_card_effects.UMI: (
                constants.race.FISH,
                200,
            ),
            constants.special_card_effects.WASTELAND: (
                constants.race.DINOSAUR,
                200,
            ),
            constants.special_card_effects.YAMI: (
                constants.race.FIEND,
                200,
            ),
        }
        for name, (race, expected_change) in field_cases.items():
            with self.subTest(field_spell=name):
                spell_class = spell_cards.CARD_REGISTRY[name]
                field_card = self.effect_card(name, constants.race.FIELD)
                spell = spell_class(original_card=field_card)
                target = self.monster("matching monster", 1000, 900)
                target.race = race
                self.attacker_owner.battle_cards[:] = [target]
                self.defender_owner.battle_cards.clear()
                board = SimpleNamespace(
                    current_player=self.attacker_owner,
                    opposite_player=self.defender_owner,
                    p1=self.attacker_owner,
                    p2=self.defender_owner,
                )

                self.assertTrue(spell.get_valid_targets(board))
                spell.activate_spell_on_card(target)
                self.assertEqual(target.base_attack, 1000 + expected_change)
                self.assertEqual(target.base_defense, 900 + expected_change)
                spell.deactivate(None)
                self.assertEqual(target.base_attack, 1000)
                self.assertEqual(target.base_defense, 900)

    def test_mountain_applies_to_tyhone_winged_beast(self):
        tyhone = self.monster("Tyhone", 1200, 1400)
        tyhone.race = constants.race.WINGED_BEAST
        field_card = self.effect_card(
            constants.special_card_effects.MOUNTAIN,
            constants.race.FIELD,
        )
        mountain = spell_cards.CARD_REGISTRY[field_card.name](
            original_card=field_card
        )

        mountain.activate_spell_on_card(tyhone)

        self.assertEqual(tyhone.base_attack, 1400)
        self.assertEqual(tyhone.base_defense, 1600)

    def test_umi_field_spell_also_applies_its_declared_reduction(self):
        machine = self.monster("machine", 1500, 1000)
        machine.race = constants.race.MACHINE
        field_card = self.effect_card(
            constants.special_card_effects.UMI,
            constants.race.FIELD,
        )
        umi = spell_cards.CARD_REGISTRY[field_card.name](
            original_card=field_card
        )

        umi.activate_spell_on_card(machine)

        self.assertEqual(machine.base_attack, 1300)
        self.assertEqual(machine.base_defense, 800)
        umi.deactivate(None)
        self.assertEqual(machine.base_attack, 1500)
        self.assertEqual(machine.base_defense, 1000)


    def test_dedicated_spell_rows_exclude_field_spell_cards(self):
        regular = self.effect_card("regular spell", "normal")
        field_spell = self.effect_card("field spell", constants.race.FIELD)
        self.attacker_owner.special_cards.extend([regular, field_spell])

        self.assertEqual(
            GameEngine._row_special_cards(self.attacker_owner),
            [regular],
        )

    def test_field_spell_zone_text_is_black_and_centered(self):
        engine = GameEngine.__new__(GameEngine)
        engine.p1 = self.attacker_owner
        engine.image_references = []
        engine.card_back_img = object()
        engine.board_canvas = Mock()
        field_card = self.effect_card("dark hole", constants.race.FIELD)
        field_card.is_face_up = True
        field_card.get_photo = Mock(return_value=object())
        self.attacker_owner.special_cards.append(field_card)

        engine.draw_field_spell_zone(self.attacker_owner)

        labels = [
            call.kwargs
            for call in engine.board_canvas.create_text.call_args_list
        ]
        field_title = next(
            item for item in labels if "Field Spell" in item.get("text", "")
        )
        card_title = next(item for item in labels if item.get("text") == "dark hole")
        self.assertEqual(field_title["fill"], "black")
        self.assertEqual(field_title["justify"], "center")
        self.assertEqual(card_title["fill"], "black")
        self.assertEqual(card_title["justify"], "center")

    def test_graveyard_card_counts_are_positioned_above_the_card_back(self):
        engine = GameEngine.__new__(GameEngine)
        engine.p1 = self.attacker_owner
        engine.p2 = self.defender_owner
        engine.board_canvas = Mock()
        engine.graveyard_count_ids = {}

        with patch("board.Image.open") as open_image, patch(
            "board.ImageTk.PhotoImage"
        ), patch("board.tk.Label"):
            open_image.return_value.resize.return_value = Mock()
            engine.display_graveyard(self.attacker_owner)

        text_y = engine.board_canvas.create_text.call_args.args[1]
        image_y = engine.board_canvas.create_window.call_args.args[1]
        self.assertEqual(text_y, constants.card_height - 5)
        self.assertGreater(image_y, text_y + 20)

    def test_extra_deck_zone_displays_count_and_face_down_top_card(self):
        engine = GameEngine.__new__(GameEngine)
        engine.board_canvas = Mock()
        engine.card_back_img = object()
        engine.p1 = self.attacker_owner
        engine.p2 = self.defender_owner
        fusion = self.monster("fusion", 2000, 1800)
        self.attacker_owner.extra_deck.append(fusion)

        engine.draw_extra_deck_zone(self.attacker_owner)

        self.assertTrue(
            any(
                call.kwargs.get("text") == "Extra Deck (1)"
                for call in engine.board_canvas.create_text.call_args_list
            )
        )
        engine.board_canvas.create_image.assert_called_once()

    def test_chain_resolves_responses_last_in_first_out(self):
        resolution_order = []

        class TestQuickEffect:
            trigger = None
            require_card_selection = False
            name = "test quick effect"

            def __init__(self, original_card):
                self.original_card = original_card

            def get_valid_targets(self, board):
                return True

            def activate(self, board, target):
                resolution_order.append(self.original_card.name)

        first_card = SimpleNamespace(
            name="first response",
            type=constants.card_types.SPELL,
            race=constants.race.QUICK_SPELL,
            can_be_selected=True,
            is_face_up=True,
        )
        second_card = SimpleNamespace(
            name="second response",
            type=constants.card_types.SPELL,
            race=constants.race.QUICK_SPELL,
            can_be_selected=True,
            is_face_up=True,
        )
        self.attacker_owner.special_cards.append(first_card)
        self.defender_owner.special_cards.append(second_card)
        self.board.choose_chain_response = Mock(
            side_effect=[second_card, first_card]
        )
        manager = PhaseManager(self.board)

        with patch.dict(
            spell_cards.CARD_REGISTRY,
            {
                first_card.name: TestQuickEffect,
                second_card.name: TestQuickEffect,
            },
        ):
            manager.resolve_chain(
                lambda: resolution_order.append("initial effect"),
                self.attacker_owner,
                constants.events.SPELL_ACTIVATED,
            )

        self.assertEqual(
            resolution_order,
            ["first response", "second response", "initial effect"],
        )
        self.assertEqual(
            self.board.choose_chain_response.call_count,
            2,
        )

    def test_polymerization_summons_from_two_listed_materials(self):
        material_one = self.monster("material one", 1200, 1000)
        material_two = self.monster("material two", 1000, 1200)
        for material in (material_one, material_two):
            material.type = constants.card_types.MONSTER
            material.race = constants.race.WARRIOR
            material.effect_on_card = {}
        polymerization = self.effect_card(
            constants.special_card_effects.POLYMERIZATION, "normal"
        )
        fusion = self.monster("fusion monster", 2000, 1800)
        fusion.type = "fusion monster"
        fusion.description = 'A fusion of "Material One" and "Material Two".'
        fusion.effect_on_card = {}
        fusion.special_cards = []
        fusion.special_spells = []
        fusion.summoned_this_turn = False
        self.attacker_owner.battle_cards.append(material_one)
        self.attacker_owner.hand.extend([material_two, polymerization])
        self.attacker_owner.extra_deck.append(fusion)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        self.board.choose_fusion_monster = Mock(return_value=fusion)
        manager = PhaseManager(self.board)

        self.assertTrue(manager.start_fusion_summon(polymerization))
        self.assertTrue(manager.select_fusion_material(material_one))
        self.assertTrue(manager.select_fusion_material(material_two))

        self.assertIn(fusion, self.attacker_owner.battle_cards)
        self.assertEqual(
            self.attacker_owner.graveyard,
            [material_one, material_two, polymerization],
        )
        self.assertEqual(self.attacker_owner.extra_deck, [])
        self.assertIsNone(manager.pending_fusion_spell)

    def test_fusion_summon_rejects_wrong_materials(self):
        material_one = self.monster("material one", 1200, 1000)
        material_two = self.monster("wrong material", 1000, 1200)
        for material in (material_one, material_two):
            material.type = constants.card_types.MONSTER
            material.race = constants.race.WARRIOR
            material.effect_on_card = {}
        polymerization = self.effect_card(
            constants.special_card_effects.POLYMERIZATION, "normal"
        )
        fusion = self.monster("fusion monster", 2000, 1800)
        fusion.type = "fusion monster"
        fusion.description = 'A fusion of "Material One" and "Material Two".'
        self.attacker_owner.hand.extend(
            [material_one, material_two, polymerization]
        )
        self.attacker_owner.extra_deck.append(fusion)
        self.attacker_owner.turn_phase = constants.phase.MAIN1
        self.board.show_popup = Mock()
        manager = PhaseManager(self.board)

        manager.start_fusion_summon(polymerization)
        manager.select_fusion_material(material_one)
        summoned = manager.select_fusion_material(material_two)

        self.assertFalse(summoned)
        self.assertEqual(self.attacker_owner.extra_deck, [fusion])
        self.assertIn(material_one, self.attacker_owner.hand)
        self.assertIn(material_two, self.attacker_owner.hand)

    def test_stat_effect_colors_distinguish_atk_and_defense_changes(self):
        monster = self.monster("modified", 1300, 1400)
        monster.effect_on_card = {
            "boost": [{"attr": "base_attack", "value": 200}],
            "penalty": [{"attr": "base_defense", "value": -100}],
        }

        self.assertEqual(monster.stat_effect_direction("base_attack"), 200)
        self.assertEqual(monster.stat_effect_direction("base_defense"), -100)

    def test_stat_labels_are_larger_and_placed_by_player_side(self):
        class FakeImage:
            width = 120
            height = 150

            def rotate(self, degrees, expand):
                return self

            def resize(self, size, resample):
                return self

        engine = GameEngine.__new__(GameEngine)
        engine.card_back_img = object()
        engine.image_references = []
        engine.board_canvas = Mock()
        card = self.monster("stat card", 1234, 567)
        card.get_photo = Mock(return_value=object())
        with (
            patch("board.ImageTk.getimage", return_value=FakeImage()),
            patch("board.ImageTk.PhotoImage", return_value=object()),
        ):
            engine.draw_row(2, "red", [card])
            engine.draw_row(3, "red", [card])

        stat_calls = [
            call
            for call in engine.board_canvas.create_text.call_args_list
            if call.kwargs.get("text") in ("1234", "567")
        ]
        self.assertEqual(len(stat_calls), 4)
        p1_attack = stat_calls[0]
        p2_attack = stat_calls[2]
        self.assertLess(p1_attack.args[1], card.y_position)
        self.assertGreater(p2_attack.args[1], card.y_position)
        self.assertEqual(p1_attack.kwargs["font"], ("Arial", 11, "bold"))
        card.effect_on_card = {
            "boost": [{"attr": "base_attack", "value": 200}],
            "penalty": [{"attr": "base_defense", "value": -100}],
        }
        self.assertEqual(GameEngine._stat_color(card, "base_attack", "white"), "green")
        self.assertEqual(GameEngine._stat_color(card, "base_defense", "blue"), "red")

    def test_direct_attack_resolves_when_opponent_has_no_monsters(self):
        attacker = self.monster("attacker", 1800, 1000)
        attacker.is_face_up = True
        attacker.selected = False
        attacker.action = None
        self.attacker_owner.battle_cards.append(attacker)
        self.attacker_owner.turn_phase = constants.phase.BATTLE
        manager = PhaseManager(self.board)

        manager.battle_card_clicked(attacker)

        self.assertEqual(self.defender_owner.life_points, 6200)
        self.assertEqual(self.attacker_owner.is_attacking, [attacker])
        self.assertIsNone(self.board.attacking_card)

    def test_successful_draw_automatically_advances_to_main1(self):
        drawn = SimpleNamespace(name="drawn")
        player = Player(
            "active",
            [SimpleNamespace(name=f"starting-{i}") for i in range(5)] + [drawn],
            constants.player_is_1,
        )
        player.turn_phase = constants.phase.DRAW
        board = SimpleNamespace(
            current_player=player,
            phase_manager=SimpleNamespace(
                check_trap_triggers=Mock(),
                check_opponenet_quick_spell=Mock(),
            ),
            refresh_board=Mock(),
            update_phase_ui=Mock(),
        )

        GameEngine.draw_card_from_deck(board)

        self.assertEqual(player.turn_phase, constants.phase.MAIN1)
        board.phase_manager.check_trap_triggers.assert_called_once_with(
            constants.events.DRAW, drawn
        )
        board.phase_manager.check_opponenet_quick_spell.assert_called_once()
        board.refresh_board.assert_called_once()


if __name__ == "__main__":
    unittest.main()
