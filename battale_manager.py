from unittest import case
import constants
class PhaseManager:
    def __init__(self, player):
        self.player = player
        
    def set_battle_cards(self, board, card):
        if card in board.current_player.battle_cards:
            if card in board.current_player.is_attacking:
                self.current_player.is_attacking.remove(card)
            else:
                self.current_player.is_attacking.append(card)        

        if (self.player_1_attacking_card and self.player_2_attacked_card) or (self.player_2_attacking_card and self.player_1_attacked_card):
            self.resolve_battle()
        
    def resolve_battle(self):
        
        if self.player_turn == constants.player_is_1:
            attacking_card = self.player_1_attacking_card
            attacked_card = self.player_2_attacked_card
            attacking_player = self.p1
            attacked_player = self.p2
        else:
            attacking_card = self.player_2_attacking_card
            attacked_card = self.player_1_attacked_card
            attacking_player = self.p2
            attacked_player = self.p1

        if not attacking_card or not attacked_card:
            return

        if attacked_card.is_attack_position:
            attack_value = attacking_card.attack
            defence_value = attacked_card.attack
        else:
            attack_value = attacking_card.attack
            defence_value = attacked_card.defence

        if attack_value > defence_value:
            damage = attack_value - defence_value
            attacked_player.take_damage(damage)
            attacked_player.send_card_to_graveyard(attacked_card)

        elif attack_value < defence_value:
            damage = defence_value - attack_value
            attacking_player.take_damage(damage)
            attacking_player.send_card_to_graveyard(attacking_card)
        else:
            attacked_player.send_card_to_graveyard(attacked_card)
            attacking_player.send_card_to_graveyard(attacking_card)

        # Reset battle state after resolution
        self.player_1_attacking_card = None
        self.player_2_attacking_card = None
        self.player_1_attacked_card = None
        self.player_2_attacked_card = None
