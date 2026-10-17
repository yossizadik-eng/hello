#Target 1 face-up Trap on the field; destroy it
import board
import constants

def prepare(board, card):
    return [c for c in board.opposite_player.battle_cards if c.is_face_up and constants.card_types.TRAP in c.type.lower()]
    
    
def activate(board, target_card):
    board.opposite_player.battle_cards.remove(target_card)
    board.opposite_player.graveyard.append(target_card)    
    