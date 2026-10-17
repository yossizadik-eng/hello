import constants


class ManEaterBug:
    action_label = "Destroy"
    target_label = "monster"

    @staticmethod
    def get_valid_targets(board):
        return [
            monster
            for owner in (board.current_player, board.opposite_player)
            for monster in owner.battle_cards
            if constants.card_types.MONSTER in monster.type
        ]

    @staticmethod
    def activate(board, target):
        constants.destroy_card(board, target)


class HaneHane:
    action_label = "Return"
    target_label = "monster"

    @staticmethod
    def get_valid_targets(board):
        return [
            monster
            for owner in (board.current_player, board.opposite_player)
            for monster in owner.battle_cards
            if constants.card_types.MONSTER in monster.type
        ]

    @staticmethod
    def activate(board, target):
        for owner in (board.current_player, board.opposite_player):
            if target in owner.battle_cards:
                owner.battle_cards.remove(target)
                owner.hand.append(target)
                return


class OldVindictiveMagician:
    action_label = "Destroy"
    target_label = "monster"

    @staticmethod
    def get_valid_targets(board):
        return [
            monster
            for monster in board.opposite_player.battle_cards
            if constants.card_types.MONSTER in monster.type
        ]

    @staticmethod
    def activate(board, target):
        constants.destroy_card(board, target)


class ReaperOfTheCards:
    action_label = "Destroy"
    target_label = "Trap"

    @staticmethod
    def get_valid_targets(board):
        return [
            card
            for owner in (board.current_player, board.opposite_player)
            for card in owner.special_cards
            if constants.card_types.TRAP in card.type
        ]

    @staticmethod
    def activate(board, target):
        constants.destroy_card(board, target)


FLIP_EFFECT_REGISTRY = {
    "man-eater bug": ManEaterBug,
    "hane-hane": HaneHane,
    "old vindictive magician": OldVindictiveMagician,
    "reaper of the cards": ReaperOfTheCards,
}
