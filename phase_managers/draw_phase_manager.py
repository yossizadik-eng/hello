import constants


# def manage_draw_phase(player, card, opposite_player):
#     if card in player.hand:
#         if can_activate_in_draw_phase(player, card, opposite_player): 
#             return constants.action_allowed_types.activate_hand_card      
#     elif not player.has_drawn_this_turn:
#         if len(player.deck) == 0:
#             return constants.action_allowed_types.no_more_cards_in_deck
#         else:                
#             player.draw_card_from_deck()
#             return constants.action_allowed_types.card_drawn_from_deck

# def can_activate_in_draw_phase(player, card, opposite_player):
#     if card.name == constants.special_card_effects.CAPTURE_JAR.value and card.possition == constants.possition.SET and card.is_face_up == False:
#         return True
#     elif card.name == constants.special_card_effects.TWO_PRONGED.value and card.possition == constants.possition.SET and card.is_face_up == False:
#         if len(player.battle_cards) >= 2 and len(opposite_player.battle_cards) >= 1:
#             return True        
        




