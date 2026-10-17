import constants


class Player:
    def __init__(self, name, deck, player_number, extra_deck=None):
        self.name = name
        self.player_number = player_number
        self.base_life_points = 8000
        self.on_defeat = None
        self.defeat_notified = False
        self.turn_phase = constants.phase.DRAW  
        self.has_drawn_this_turn = False
        self.has_summoned_this_turn = False
        self.has_set_this_turn = False        
        self.is_attacking = []     
        
        self.hand = deck[:5]
        self.deck = deck[5:]
        self.extra_deck = list(extra_deck or [])
        self.battle_cards = []
        self.special_cards = []    
        self.graveyard = []
        self.effect_on_card = {}
        self.monsters_to_tribute = []
        self.tribute_monster = None

    @property
    def life_points(self):
        return self.base_life_points + self._life_point_bonus()

    @life_points.setter
    def life_points(self, value):
        previous_life_points = self.life_points
        self.base_life_points = int(value) - self._life_point_bonus()
        if previous_life_points > 0 and self.life_points <= 0:
            callback = self.on_defeat
            if callback is not None and not self.defeat_notified:
                self.defeat_notified = True
                callback(self)

    def _life_point_bonus(self):
        return sum(
            effect.get("life_points", 0)
            for effect in self.effect_on_card.values()
            if isinstance(effect, dict)
        )
    
    def draw_card_from_deck(self):
        if self.deck and len(self.deck) > 0 and not self.has_drawn_this_turn:
            card = self.deck.pop(0)
            self.hand.append(card)
            self.has_drawn_this_turn = True
            return card
        return None

    def set_is_attacking(self, card):
        if card in self.battle_cards:
            if card in self.is_attacking:
                self.is_attacking.remove(card)
            else:
                self.is_attacking.append(card)

    def send_card_to_graveyard(self, card):
        if card in self.hand:
            self.hand.remove(card)
        elif card in self.battle_cards:
            self.battle_cards.remove(card)
        elif card in self.special_cards:
            self.special_cards.remove(card)
        self.graveyard.append(card) 

    @property
    def graveyard_monsters(self):
        return [
            card
            for card in self.graveyard
            if constants.card_types.MONSTER in card.type
        ]

    @property
    def graveyard_spell_traps(self):
        return [
            card
            for card in self.graveyard
            if constants.card_types.SPELL in card.type
            or constants.card_types.TRAP in card.type
        ]

    def take_damage(self, amount):
        self.life_points = max(0, self.life_points - amount)

    def heal(self, amount):
        self.life_points += amount

    def revive_card_from_graveyard(self):
        if not self.graveyard:
            return False

        card = self.graveyard[0]
        if constants.card_types.MONSTER in card.type:
            if len(self.battle_cards) >= 5:
                return False
            self.battle_cards.append(card)
        else:
            if len(self.special_cards) >= 5:
                return False
            self.special_cards.append(card)

        self.graveyard.pop(0)
        return True
