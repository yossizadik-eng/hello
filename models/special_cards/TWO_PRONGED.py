from tkinter import TRUE

import constants

class TWO_PRONGED:
    def __init__(self, board, player, opposite_player, card):
        self.board = board
        self.player = player 
        self.opposite_player = opposite_player
        self.card = card  
        self.player_card_selection = []
        self.opposite_player_card_selection = [] 

    def players_have_cards_for_effect(self):
        if (len(self.board.current_player.hand) + len(self.board.current_player.battle_cards)) > 1 and (len(self.board.opposite_player.hand) + len(self.board.opposite_player.battle_cards)) > 0:
            return True
        else:
            return False

    def player_select_card(self, card):
        if card in self.player.battle_cards:
            if len(self.player_card_selection) < 2 and (card in self.player.hand or card in self.player.battle_cards) and constants.card_types.MONSTER in card.type.lower():
                self.player_card_selection.append(card)
                card.selected = True
        else:            
            if len(self.opposite_player_card_selection) < 1 and (card in self.opposite_player.hand or card in self.opposite_player.battle_cards) and constants.card_types.MONSTER in card.type.lower():
                self.opposite_player_card_selection.append(card)
                card.selected = True
        if len(self.player_card_selection) == 2 and len(self.opposite_player_card_selection) == 1:
            return constants.step.ACTIVATE_SPECIAL_CARD
        else:            
            return constants.step.WAIT_FOR_BATTLE_CARD
        

    def activate(self):     
        if len(self.player_card_selection) == 2 and len(self.opposite_player_card_selection) == 1:
            # Implement the effect of Two-Pronged Attack here (e.g., destroy the 2 monsters from player's hand and 1 monster from opponent's hand)
            for affected_card in self.player_card_selection:
                if affected_card in self.player.hand:
                    self.player.hand.remove(affected_card)
                    self.player.send_card_to_graveyard(affected_card)
                    affected_card.selected = False
                elif affected_card in self.player.battle_cards:                
                    self.player.battle_cards.remove(affected_card)
                    self.player.send_card_to_graveyard(affected_card)            
                    affected_card.selected = False
            for affected_card in self.opposite_player_card_selection:
                if affected_card in self.opposite_player.hand:
                    self.opposite_player.hand.remove(affected_card)
                    self.opposite_player.send_card_to_graveyard(affected_card)                
                    affected_card.selected = False
                elif affected_card in self.opposite_player.battle_cards:
                    self.opposite_player.battle_cards.remove(affected_card)
                    self.opposite_player.send_card_to_graveyard(affected_card)
                    affected_card.selected = False
            # Clear the special card effect state after resolution
            target_name = constants.special_card_effects.TWO_PRONGED.value
            for card in self.player.hand:            
                if card.name == target_name:
                    self.player.hand.remove(card)                
                    break  
