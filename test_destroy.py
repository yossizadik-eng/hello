import unittest
from unittest.mock import MagicMock
import constants

# Import your classes here
# from your_game_file import destroy_card, Card, Player, Board

class TestGameEngine(unittest.TestCase):
    def setUp(self):
        """Runs before every single test method."""
        # 1. Arrange: Create a fake board
        self.board = MagicMock()
        self.player1 = MagicMock()
        self.player2 = MagicMock()
        
        # Setup lists for our mock players
        self.player1.battle_cards = []
        self.player1.graveyard = []
        self.player2.battle_cards = []
        self.player2.graveyard = []
        
        # Point the board to our mock players
        self.board.current_player = self.player1
        self.board.opposite_player = self.player2
        
        # Create a dummy card
        self.test_card = MagicMock()
        self.test_card.name = "Test Monster"

    def test_destroy_card_moves_to_graveyard(self):
        # Arrange: Put card on player1's field
        self.player1.battle_cards.append(self.test_card)
        
        # Act: Destroy the card
        constants.destroy_card(self.board, self.test_card)
        
        # Assert: Check the results
        self.assertNotIn(self.test_card, self.player1.battle_cards)
        self.assertIn(self.test_card, self.player1.graveyard)