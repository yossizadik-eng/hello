import constants


class SpellManager:
    def __init__(
        self,
        name,
        spell_type,
        spell_level,
        target_filter,
        extra_selection,
        stat_modifier,
        scopes,
        require_card_selection,
        trigger_condition=None,
        trigger=None,
        trigger_opponent_only=False,
        original_card=None,
    ):
        self.original_card = original_card
        self.name = name
        self.spell_type = spell_type
        self.spell_level = spell_level
        self.target_filter = target_filter
        self.extra_selection = extra_selection
        self.stat_modifier = stat_modifier
        self.scopes = scopes
        self.valid_cards = []
        self.affected_cards = {}
        self.require_card_selection = require_card_selection
        self.trigger_condition = trigger_condition
        self.trigger = trigger
        self.trigger_opponent_only = trigger_opponent_only

    def get_valid_targets(self, board):
        if self.spell_level == constants.spell_level.PLAYER:
            return True

        scope_map = {
            constants.populationScope.PLAYER_HAND: board.current_player.hand,
            constants.populationScope.PLAYER_BATTLE: board.current_player.battle_cards,
            constants.populationScope.PLAYER_SPECIAL: board.current_player.special_cards,
            constants.populationScope.OPPONENT_HAND: board.opposite_player.hand,
            constants.populationScope.OPPONENT_BATTLE: board.opposite_player.battle_cards,
            constants.populationScope.OPPONENT_SPECIAL: board.opposite_player.special_cards,
        }
        found_cards = []
        if self.target_filter is not None:
            for scope in self.scopes:
                source = scope_map.get(scope, [])
                found_cards.extend(card for card in source if self.target_filter(card))

        if found_cards and self.extra_selection:
            result = self.extra_selection(found_cards)
            found_cards = result if isinstance(result, list) else [result]

        self.valid_cards = found_cards
        return bool(self.valid_cards)

    def activate(self, board, card):
        if self.spell_type == constants.spell_type.SPELL:
            return True

        if self.spell_level == constants.spell_level.PLAYER:
            life_point_change = self.stat_modifier["life_points"]
            if constants.populationScope.PLAYER in self.scopes:
                target_player = board.current_player
            elif constants.populationScope.OPPONENT in self.scopes:
                target_player = board.opposite_player
            else:
                raise ValueError(f"{self.name} has no player target scope")

            if life_point_change < 0:
                target_player.take_damage(-life_point_change)
            else:
                target_player.heal(life_point_change)
            constants.destroy_card(board, self.original_card)
            return True

        permanent_types = (
            constants.race.CONTINUOUS,
            constants.race.EQUIP,
            constants.race.FIELD,
        )
        targets = self.valid_cards if card is None else [card]
        for target in targets:
            if self.spell_type == constants.spell_type.DESTROY:
                constants.destroy_card(board, target)
                self.original_card.marked_for_graveyard = True
            elif self.spell_type == constants.spell_type.TYPE_MODIFIER:
                self.activate_spell_on_card(target)

        if self.original_card.race not in permanent_types:
            constants.destroy_card(board, self.original_card)

    def _modifiers_for_card(self, card):
        if not isinstance(self.stat_modifier, dict):
            return []

        race = str(getattr(card, "race", "")).lower()
        card_type = str(getattr(card, "type", "")).lower()
        mod_data = self.stat_modifier.get(
            race,
            self.stat_modifier.get(
                card_type, self.stat_modifier.get("target_filter")
            ),
        )
        if mod_data is None:
            return []
        return [mod_data] if isinstance(mod_data, dict) else list(mod_data)

    def activate_spell_on_card(self, card):
        modifiers = self._modifiers_for_card(card)
        if not modifiers:
            return

        applied_modifiers = [dict(modifier) for modifier in modifiers]
        for modifier in applied_modifiers:
            attribute = modifier["attr"]
            setattr(card, attribute, getattr(card, attribute) + modifier["value"])

        card.effect_on_card[self.name] = applied_modifiers
        self.affected_cards[card] = applied_modifiers
        if (
            self.original_card.race != constants.race.FIELD
            and self.original_card not in card.special_cards
        ):
            card.special_cards.append(self.original_card)
        if self not in card.special_spells:
            card.special_spells.append(self)

    def deactivate(self, card):
        targets = list(self.affected_cards) if card is None else [card]
        for target in targets:
            modifiers = self.affected_cards.pop(target, [])
            for modifier in modifiers:
                attribute = modifier["attr"]
                setattr(
                    target,
                    attribute,
                    getattr(target, attribute) - modifier["value"],
                )
            target.effect_on_card.pop(self.name, None)
            if self.original_card in target.special_cards:
                target.special_cards.remove(self.original_card)
            if self in target.special_spells:
                target.special_spells.remove(self)

    def deactivate_spell_on_card(self, card):
        self.deactivate(card)
