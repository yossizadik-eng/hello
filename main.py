# when sending a card to field (battle/sepcial): is set to defense- it is face-down. if summon - face-up
# after sending a card to filed - you can use quick-spell or trap if you have one, and then the opponent can too.
# when a card is attcked -it becomes face-up
# special card has no summon. it is face-down in "attack" and defense mode.


import sys
import random
import tkinter as tk
import constants

from utils import get_all_yugioh_cards
from models.card import Card
from models.player import Player
from board import GameEngine
from typing import cast
from models.special_cards import spell_cards


def filter_card_deck(raw_deck_data, registry):
        allowed_registered_names = {
        str(key).strip().lower() for key in registry.keys()
        }

        valid_cards = []

        for card_data in raw_deck_data:
            card_type = card_data.get("type", "")
            card_name = str(card_data.get("name", "")).strip().lower()

            # Check if card is a Spell or Trap
            if "Spell" in card_type or "Trap" in card_type:
                # Only include if card name is in CARD_REGISTRY keys
                if card_name in allowed_registered_names:
                    valid_cards.append(card_data)
            else:
                # Monster cards pass through automatically
                valid_cards.append(card_data)

        return valid_cards


class main :
    

    def __init__(self):

        self.image_references = []
        
        cardDeck = get_all_yugioh_cards()
        if not cardDeck :
            sys.exit(1)  

        cardDeck = filter_card_deck(cardDeck, spell_cards.CARD_REGISTRY)
        fusion_cards = [
            card_data
            for card_data in cardDeck
            if "fusion" in str(card_data.get("type", "")).lower()
        ]
        main_deck_cards = [
            card_data for card_data in cardDeck if card_data not in fusion_cards
        ]
        
    

        root = tk.Tk()
        root.geometry("1900x1900")
        canvas = tk.Canvas(root)
        canvas.pack(side=tk.LEFT, anchor="n", padx=5, pady=5)
    
        player1_cards = random.sample(main_deck_cards, 40)
        player2_cards = random.sample(main_deck_cards, 40)


        player1 = Player(
            "Yossi",
            [Card(data) for data in player1_cards],
            constants.player_is_1,
            [Card(data) for data in fusion_cards],
        )
        player2 = Player(
            "Yaniv",
            [Card(data) for data in player2_cards],
            constants.player_is_2,
            [Card(data) for data in fusion_cards],
        )


        target_name = constants.special_card_effects.TWO_PRONGED   
        found_card = None

        for card in player1.deck:
            
            if card.name == target_name:
                found_card = card
                break  # Stop looking once we find it

        # 2. Move it to position 1 (Index 0 in Python)
        if found_card is not None:
            player1.hand[0] = found_card

        target_name = "larvas"

        found_card = None

        for card in player1.deck:
            
            if card.name == target_name:
                found_card = card
                break  # Stop looking once we find it

        # 2. Move it to position 1 (Index 0 in Python)
        if found_card is not None:
            player1.hand[1] = found_card      

        # target_name = 'Book of Secret Arts'   
        # found_card = None

        # for card in player1.deck:
            
        #     if card.name.lower() == target_name.lower():
        #         found_card = card
        #         break  # Stop looking once we find it

        # # 2. Move it to position 1 (Index 0 in Python)
        # if found_card is not None:
        #     player1.hand[2] = found_card


        GameEngine(canvas, player1, player2)

        root.mainloop()
    
if __name__ == "__main__":
    main()

  