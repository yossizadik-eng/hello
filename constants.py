
from enum import Enum, auto

card_width = 120
card_height = 150
padding = 9
player_is_1=1
player_is_2=2

class messages():
    NO_CARDS_FOR_EFFECT = "No cards on board for this effect"
    SPELL_NOT_ALLOWED = "You are not allowed to use spell and this time"

class step(Enum):
    TURN_START= auto()
    HAND_CARD_SELECTED = auto()
    SPECIAL_CARD_SELECED = auto()
    SPECIAL_CARD_ENDED = auto()
    WAIT_FOR_BATTLE_CARD = auto()
    ACTIVATE_SPECIAL_CARD = auto()  
    NO_CARD_FOR_EFFECT = auto()

class phase(Enum):
    DRAW = "Draw"
    MAIN1 = "Main 1"
    BATTLE = "Battle"
    MAIN2 = "Main 2"
    END = "End" 

class possition(Enum):
    ATTACK = auto()
    DEFENSE = auto()    

class card_types():
    TRAP = 'trap'
    SPELL = 'spell'
    MONSTER = 'monster' 
    WARRIOR = 'warrior'
    BEAST = 'beast'     
    ZOMBIE = 'zombie'
    SPELLCASTER = 'spellcaster'
    AQUA = 'aqua'   
    FIEND = 'fiend'
    INSECT = 'insect'
    PLANT = 'plant' 
    BEAST_WARRIOR = 'beast-warrior'
    DINOSAUR = 'dinosaur'
    ROCK = 'rock' 
    DRAGON = 'dragon' 
    WINGED_BEAST = 'winged-beast'
    THUNDER = 'thunder' 
    MACHINE = 'machine'
    PYRO = 'pyro'   
    FISH = 'fish'
    SEA_SERPENT = 'sea serpent' 
    FAIRY = 'fairy'

class race():
    BEAST = 'beast'
    WARRIOR = 'warrior'
    ZOMBIE = 'zombie'
    SPELLCASTER = 'spellcaster'
    AQUA = 'aqua'
    FIEND = 'fiend'
    INSECT = 'insect'
    PLANT = 'plant'
    BEAST_WARRIOR = 'beast-warrior'
    DINOSAUR = 'dinosaur'
    ROCK = 'rock'
    DRAGON = 'dragon'
    WINGED_BEAST = 'winged-beast'
    THUNDER = 'thunder'
    MACHINE = 'machine'
    PYRO = 'pyro'
    FISH = 'fish'
    SEA_SERPENT = 'sea serpent'
    FAIRY = 'fairy'
    QUICK_SPELL = 'quick'
    CONTINUOUS = 'continuous'
    EQUIP = 'equip'
    FIELD = 'field'

class action_allowed_types(Enum):
    activate_hand_card = auto()
    set_hand_card = auto()
    activate_battle_card = auto()
    activate_special_card = auto()
    cannot_be_activated = auto()
    no_more_cards_in_deck = auto()
    card_drawn_from_deck = auto()

class special_card_effects():
    BEAST_FANGS = "beast fangs"
    BOOK_OF_SECRET_ARTS = "book of secret arts"
    CAPTURE_JAR = "dragon capture jar"
    DARK_ENERGY = "dark energy"
    DARK_HOLE = "dark hole"
    FISSURE = "fissure"
    FOREST = "forest"
    GRAVEDIGGER = "gravedigger's trap hole"
    HINOTAMA = "hinotama"
    LEGENDARY_SWORD = "legendary sword"
    MOUNTAIN = "mountain"
    POLYMERIZATION = "polymerization"
    POWER_OF_KAISHIN = "power of kaishin"
    RAIGEKI = "raigeki"
    RED_MEDICINE = "red medicine"
    REMOVE_TRAP = "remove trap"
    SOGEN = "sogen"
    SPARKS = "sparks"
    TRAP_HOLE = "trap hole"
    TWO_PRONGED = "two-pronged attack"
    UMI = "umi"
    VIOLET_CRYSTAL = "violet crystal"
    WASTELAND = "wasteland"
    YAMI = "yami"
    MONSTER_REBORN = "monster reborn"

class populationScope(Enum):
    PLAYER_HAND = auto()
    PLAYER_BATTLE = auto()
    PLAYER_SPECIAL = auto()
    OPPONENT_HAND = auto()
    OPPONENT_BATTLE = auto()
    OPPONENT_SPECIAL = auto()
    PLAYER = auto()
    OPPONENT = auto()

class events():
     ON_SUMMON = "ON SUMMON"  
     DRAW = "DRAW"  
     SPELL_ACTIVATED = "SPELL ACTIVATED"
     MONSTER_FLIPPED = "MONSTER FLIPPED"

class spell_type():
     SPELL = "spell"
     DESTROY = "destroy"
     TYPE_MODIFIER = "type_modifier"

class spell_level():
     CARD = "card"
     PLAYER = "player"   

class battle_action():
    ATTACKING = "ATTACKING"
    
def destroy_card(board, card):        
        # 1. Remove from field
        if card in board.current_player.hand:  
            board.current_player.hand.remove(card)        
            board.current_player.graveyard.append(card)   
        if card in board.current_player.battle_cards:
            for c in card.special_cards:
                if c in board.current_player.special_cards:
                    board.current_player.special_cards.remove(c)  
                    board.current_player.graveyard.append(c) 
            for c in list(card.special_spells):                    
                c.deactivate(card)
            board.current_player.battle_cards.remove(card)        
            board.current_player.graveyard.append(card)   
        if card in board.current_player.special_cards:
            board.current_player.special_cards.remove(card)        
            board.current_player.graveyard.append(card) 
        if card in board.opposite_player.hand:
            board.opposite_player.hand.remove(card)        
            board.opposite_player.graveyard.append(card)  
        if card in board.opposite_player.battle_cards:
            for c in card.special_cards:
                if c in board.opposite_player.special_cards:
                    board.opposite_player.special_cards.remove(c)  
                    board.opposite_player.graveyard.append(c) 
            for c in list(card.special_spells):                    
                c.deactivate(card)           
            board.opposite_player.battle_cards.remove(card)        
            board.opposite_player.graveyard.append(card)
        if card in board.opposite_player.special_cards:
            board.opposite_player.special_cards.remove(card)        
            board.opposite_player.graveyard.append(card) 