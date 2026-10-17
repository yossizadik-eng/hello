from dataclasses import dataclass

import constants


@dataclass(frozen=True)
class BattleResult:
    outcome: str
    damage_to_attacker: int = 0
    damage_to_defender: int = 0


def resolve_battle(board, attacker, defender=None):
    """Resolve one battle; board.current_player owns the attacking monster."""
    attacker_points = attacker.base_attack
    if defender is None:
        damage = max(0, attacker_points)
        board.opposite_player.take_damage(damage)
        return BattleResult("direct_attack", damage_to_defender=damage)

    defender_in_attack = defender.current_position == constants.possition.ATTACK
    defender_points = (
        defender.base_attack if defender_in_attack else defender.base_defense
    )

    if attacker_points == defender_points:
        if defender_in_attack:
            constants.destroy_card(board, attacker)
            constants.destroy_card(board, defender)
            return BattleResult("both_destroyed")
        return BattleResult("stalemate")

    if attacker_points > defender_points:
        if defender_in_attack:
            damage = attacker_points - defender_points
            board.opposite_player.take_damage(damage)
            constants.destroy_card(board, defender)
            return BattleResult("defender_destroyed", damage_to_defender=damage)
        constants.destroy_card(board, defender)
        return BattleResult("defender_destroyed")

    damage = defender_points - attacker_points
    if defender_in_attack:
        constants.destroy_card(board, attacker)
        board.current_player.take_damage(damage)
        return BattleResult("attacker_destroyed", damage_to_attacker=damage)
    return BattleResult("stalemate")
