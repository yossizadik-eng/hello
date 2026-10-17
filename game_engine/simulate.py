"""Seeded, headless monster-only self-play for reproducible rule checks."""

import argparse
import random
from dataclasses import dataclass, field

import constants
from game_engine.combat import resolve_battle
from models.card import Card
from models.player import Player


@dataclass
class SimulationBoard:
    current_player: Player
    opposite_player: Player


@dataclass
class GameResult:
    seed: int
    winner: str | None
    reason: str
    turns: int
    log: list[str] = field(default_factory=list)


def _make_deck(rng):
    cards = []
    for index in range(40):
        attack = rng.randrange(500, 2501, 100)
        defense = rng.randrange(500, 2501, 100)
        cards.append(
            Card(
                {
                    "name": f"Test Monster {index + 1}",
                    "type": constants.card_types.MONSTER,
                    "attribute": "earth",
                    "level": 4,
                    "spell speed": None,
                    "atk": attack,
                    "def": defense,
                    "race": constants.race.WARRIOR,
                    "card_images": [{"image_url": ""}],
                    "desc": "Generated for deterministic self-play.",
                }
            )
        )
    rng.shuffle(cards)
    return cards


def simulate_game(seed, max_turns=200, keep_log=True):
    rng = random.Random(seed)
    first = Player("Bot 1", _make_deck(rng), constants.player_is_1)
    second = Player("Bot 2", _make_deck(rng), constants.player_is_2)
    players = [first, second]
    log = []

    def record(message):
        if keep_log:
            log.append(message)

    record(f"seed={seed}")
    for turn in range(1, max_turns + 1):
        player = players[(turn - 1) % 2]
        opponent = players[turn % 2]
        board = SimulationBoard(player, opponent)
        drawn = player.draw_card_from_deck()
        if drawn is None:
            return GameResult(seed, opponent.name, "deck_out", turn, log)
        player.turn_phase = constants.phase.MAIN1
        record(f"turn={turn} player={player.name} draws={drawn.name}")

        if len(player.battle_cards) < 5 and not player.has_summoned_this_turn:
            summon = max(player.hand, key=lambda card: card.base_attack, default=None)
            if summon is not None:
                player.hand.remove(summon)
                player.battle_cards.append(summon)
                player.has_summoned_this_turn = True
                summon.is_face_up = True
                summon.position = constants.possition.ATTACK
                summon.summoned_turn = turn
                record(f"  summon={summon.name} atk={summon.base_attack}")

        player.turn_phase = constants.phase.BATTLE
        for attacker in list(player.battle_cards):
            if getattr(attacker, "summoned_turn", None) == turn:
                continue
            if attacker in player.is_attacking:
                continue
            defender = min(
                opponent.battle_cards,
                key=lambda card: card.base_attack,
                default=None,
            )
            result = resolve_battle(board, attacker, defender)
            player.is_attacking.append(attacker)
            if defender is None:
                record(
                    f"  direct={attacker.name} damage={result.damage_to_defender}"
                )
            else:
                record(
                    f"  battle={attacker.name} vs {defender.name} "
                    f"outcome={result.outcome} "
                    f"damage_to_attacker={result.damage_to_attacker} "
                    f"damage_to_defender={result.damage_to_defender}"
                )
            if player.life_points <= 0:
                return GameResult(seed, opponent.name, "life_points", turn, log)
            if opponent.life_points <= 0:
                return GameResult(seed, player.name, "life_points", turn, log)

        player.has_drawn_this_turn = False
        player.has_summoned_this_turn = False
        player.is_attacking.clear()
        for card in player.battle_cards:
            if getattr(card, "summoned_turn", None) == turn:
                card.summoned_turn = None

    return GameResult(seed, None, "turn_limit", max_turns, log)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--games", type=int, default=1)
    parser.add_argument("--max-turns", type=int, default=200)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    results = [
        simulate_game(args.seed + offset, args.max_turns, args.verbose)
        for offset in range(args.games)
    ]
    for result in results:
        print(
            f"seed={result.seed} winner={result.winner or 'none'} "
            f"reason={result.reason} turns={result.turns}"
        )
        if args.verbose:
            print("\n".join(result.log))


if __name__ == "__main__":
    main()
