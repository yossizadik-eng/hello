#Target 1 monster in your opponent'
# s Graveyard; banish it.
import constants

def prepare(board, card):
    return [c for c in board.opposite_player.graveyard if constants.card_types.MONSTER in c.type.lower()]

def activate(board, target_card):
    board.opposite_player.graveyard.remove(target_card)
    