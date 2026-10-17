
# # Import all your card classes
# from special_cards.BEAST_FANGS import BeastFangs
# from special_cards.BOOK_OF_SECRET_ARTS import BookOfSecretArts
# # ... etc

# # Map the string name (from your constant) to the Class reference

from models import SpellManager 
import constants

class BeastFangs(SpellManager.SpellManager):
#Equip only to a Beast monster. It gains 300 ATK/DEF.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.BEAST_FANGS, 
            spell_type=constants.spell_type.TYPE_MODIFIER,  
            spell_level=constants.spell_level.CARD,         
            target_filter=lambda c: constants.race.BEAST in c.race,
            extra_selection= None,
            stat_modifier={"target_filter" : 
                           [{"attr" : "base_attack" , "value" : 300}, 
                            {"attr" : "base_defense" , "value" : 300}
                           ]
            },
            scopes=[constants.populationScope.PLAYER_HAND, constants.populationScope.PLAYER_BATTLE],
            require_card_selection = True
        )

class BookOfSecretArts(SpellManager.SpellManager):
#Equip only to a SPELLCASTER. It gains 300 ATK/DEF.    
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.BOOK_OF_SECRET_ARTS,  
            spell_type=constants.spell_type.TYPE_MODIFIER,  
            spell_level=constants.spell_level.CARD,                   
            target_filter=lambda c: constants.card_types.SPELLCASTER in c.race,
            extra_selection= None,
            stat_modifier={"target_filter" : 
                           [{"attr" : "base_attack" , "value" : 300}, 
                            {"attr" : "base_defense" , "value" : 300}
                           ]
            },
            scopes=[constants.populationScope.PLAYER_HAND, constants.populationScope.PLAYER_BATTLE],
            require_card_selection = True
        )          

class DarkEnergy(SpellManager.SpellManager):
#Equip only to a Fiend monster. It gains 300 ATK/DEF.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.DARK_ENERGY,
            spell_type=constants.spell_type.TYPE_MODIFIER, 
            spell_level=constants.spell_level.CARD,                      
            target_filter=lambda c: constants.card_types.FIEND in c.type,
            extra_selection= None,
            stat_modifier={"target_filter" : 
                           [{"attr" : "base_attack" , "value" : 300}, 
                            {"attr" : "base_defense" , "value" : 300}
                           ]
            },
            scopes=[constants.populationScope.PLAYER_HAND, constants.populationScope.PLAYER_BATTLE],
            require_card_selection = True
        ) 

class LegendarySword(SpellManager.SpellManager):
#Equip only to a Warrior monster. It gains 300 ATK/DEF.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.DARK_ENERGY,  
            spell_type=constants.spell_type.TYPE_MODIFIER, 
            spell_level=constants.spell_level.CARD,                    
            target_filter=lambda c: constants.card_types.WARRIOR in c.type,
            extra_selection= None,
            stat_modifier={"target_filter" : 
                           [{"attr" : "base_attack" , "value" : 300}, 
                            {"attr" : "base_defense" , "value" : 300}
                           ]
            },
            scopes=[constants.populationScope.PLAYER_HAND, constants.populationScope.PLAYER_BATTLE],
            require_card_selection = True
        ) 

class PowerOfKaishin (SpellManager.SpellManager):       
#Equip only to an Aqua monster. It gains 300 ATK/DEF. 
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.POWER_OF_KAISHIN,  
            spell_type=constants.spell_type.TYPE_MODIFIER,
            spell_level=constants.spell_level.CARD,                     
            target_filter=lambda c: constants.card_types.AQUA in c.type,
            extra_selection= None,
            stat_modifier={"target_filter" : 
                           [{"attr" : "base_attack" , "value" : 300}, 
                            {"attr" : "base_defense" , "value" : 300}
                           ]
            },
            scopes=[constants.populationScope.PLAYER_HAND, constants.populationScope.PLAYER_BATTLE],
            require_card_selection = True
        )    

# class CaptureJar (SpellManager.SpellManager): 
# # change all DRAGONS to DEFENSE
#     def __init__(self, original_card):
#         super().__init__(
#             original_card = original_card,
#             name=constants.special_card_effects.CAPTURE_JAR, 
#             spell_type=constants.spell_type.TYPE_MODIFIER, 
#             spell_level=constants.spell_level.CARD,                     
#             target_filter=lambda c: c.is_face_up and constants.race.DRAGON in c.race,
#             extra_selection= None,
#             stat_modifier={"target_filter" : {"attr" : "position" , "value" : constants.possition.DEFENSE.value}},
#             scopes=[constants.populationScope.PLAYER_BATTLE, constants.populationScope.OPPONENT_BATTLE],
#             require_card_selection = False
#        ) 

class Forest (SpellManager.SpellManager): 
#All Insect, Beast, Plant, and Beast-Warrior monsters gain 200 ATK/DEF.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.FOREST,      
            spell_type=constants.spell_type.TYPE_MODIFIER, 
            spell_level=constants.spell_level.CARD,                
            target_filter=lambda c: c.race.lower() in [constants.card_types.INSECT, constants.card_types.BEAST, constants.card_types.PLANT, constants.card_types.BEAST_WARRIOR],
            extra_selection= None,
            stat_modifier={"target_filter" : 
                           [{"attr" : "base_attack" , "value" : 200}, 
                            {"attr" : "base_defense" , "value" : 200}
                           ]
            },
            scopes=[constants.populationScope.PLAYER_BATTLE, constants.populationScope.OPPONENT_BATTLE],
            require_card_selection = False
        ) 

class Mountain (SpellManager.SpellManager): 
 #All Dragon, Winged Beast, and Thunder monsters gain 200 ATK/DEF.  
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.MOUNTAIN, 
            spell_type=constants.spell_type.TYPE_MODIFIER,
            spell_level=constants.spell_level.CARD,                                 
            target_filter=lambda c: c.race.lower() in [constants.card_types.DRAGON, constants.card_types.WINGED_BEAST, constants.card_types.THUNDER],
            extra_selection= None,
            stat_modifier={"target_filter" : 
                           [{"attr" : "base_attack" , "value" : 200}, 
                            {"attr" : "base_defense" , "value" : 200}
                           ]
            },
            scopes=[constants.populationScope.PLAYER_BATTLE, constants.populationScope.OPPONENT_BATTLE],
            require_card_selection = False
        )

class Sogen(SpellManager.SpellManager): 
#All Warrior and Beast-Warrior monsters gain 200 ATK/DEF.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.SOGEN, 
            spell_type=constants.spell_type.TYPE_MODIFIER,
            spell_level=constants.spell_level.CARD,                                 
            target_filter=lambda c: c.race.lower() in [constants.card_types.WARRIOR, constants.card_types.BEAST_WARRIOR],
            extra_selection= None,
            stat_modifier={"target_filter" : 
                           [{"attr" : "base_attack" , "value" : 200}, 
                            {"attr" : "base_defense" , "value" : 200}
                           ]
            },
            scopes=[constants.populationScope.PLAYER_BATTLE, constants.populationScope.OPPONENT_BATTLE],
            require_card_selection = False
        )

class VioletCrystal(SpellManager.SpellManager): 
#Equip only to a Zombie monster. It gains 300 ATK/DEF.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.VIOLET_CRYSTAL, 
            spell_type=constants.spell_type.TYPE_MODIFIER, 
            spell_level=constants.spell_level.CARD,                                
            target_filter=lambda c: c.race.lower() in constants.card_types.ZOMBIE ,
            extra_selection= None,
            stat_modifier={"target_filter" : 
                           [{"attr" : "base_attack" , "value" : 300}, 
                            {"attr" : "base_defense" , "value" : 300}
                           ]
            },
            scopes=[constants.populationScope.PLAYER_BATTLE],
            require_card_selection = False
        )

class Wasteland(SpellManager.SpellManager): 
#All Dinosaur, Zombie, and Rock monsters gain 200 ATK/DEF.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.WASTELAND, 
            spell_type=constants.spell_type.TYPE_MODIFIER,  
            spell_level=constants.spell_level.CARD,                               
            target_filter=lambda c: c.race.lower() in [constants.card_types.DINOSAUR, constants.card_types.ZOMBIE, constants.card_types.ROCK],
            extra_selection= None,
            stat_modifier={"target_filter" : 
                           [{"attr" : "base_attack" , "value" : 200}, 
                            {"attr" : "base_defense" , "value" : 200}
                           ]
            },
            scopes=[constants.populationScope.PLAYER_BATTLE, constants.populationScope.OPPONENT_BATTLE],
            require_card_selection = False
        )

class DarkHole (SpellManager.SpellManager):
    # destroy all monsters on the battle field
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.DARK_HOLE, 
            spell_type=constants.spell_type.DESTROY, 
            spell_level=constants.spell_level.CARD,                                
            target_filter=lambda c: True,
            extra_selection= None,
            stat_modifier = None,
            scopes=[constants.populationScope.PLAYER_BATTLE, constants.populationScope.OPPONENT_BATTLE],
            require_card_selection = False
        ) 


class MONSTER_REBORN(SpellManager.SpellManager):
#Revive dead monster from graveyard.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.MONSTER_REBORN,
            spell_type=constants.spell_type.spell,
            spell_level=constants.spell_level.CARD,  
            stat_modifier=None,
            scopes=[constants.populationScope.OPPONENT, constants.populationScope.PLAYER],                                  
            target_filter=lambda c: constants.card_types.MONSTER in c.type, 
            extra_selection=None,           
            require_card_selection = True         
        )


class Fissure (SpellManager.SpellManager):
    # destroy all monsters on the battle field
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.FISSURE,
            spell_type=constants.spell_type.DESTROY, 
            spell_level=constants.spell_level.CARD,           
            target_filter=lambda c: c.is_face_up and constants.card_types.MONSTER in c.type,
            extra_selection=lambda cards: min(cards, key=lambda c: c.base_attack),
            stat_modifier = None,
            scopes=[constants.populationScope.OPPONENT_BATTLE],
            require_card_selection = False
        )                 

class Raigeki (SpellManager.SpellManager): 
# destroy all opponent monsters on the field
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.RAIGEKI, 
            spell_type=constants.spell_type.DESTROY, 
            spell_level=constants.spell_level.CARD,          
            target_filter=lambda c: constants.card_types.MONSTER in c.type,
            extra_selection= None,
            stat_modifier = None,
            scopes=[constants.populationScope.OPPONENT_BATTLE],
            require_card_selection = False
        )  

class TrapHole(SpellManager.SpellManager):
# destroy opponents monster when summon and attack > 1000
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.TRAP_HOLE,
            spell_type=constants.spell_type.DESTROY,
            spell_level=constants.spell_level.CARD,                        
            target_filter=lambda c: constants.card_types.MONSTER in c.type, 
            extra_selection= None,   
            stat_modifier = None,
            scopes=[constants.populationScope.OPPONENT_BATTLE],            
            require_card_selection = False,
            trigger_condition=lambda summoned_card: summoned_card.base_attack >= 1000,
            trigger=constants.events.ON_SUMMON,
            trigger_opponent_only=True,
        )


class Polymerization(SpellManager.SpellManager):
    def __init__(self, original_card):
        super().__init__(
            original_card=original_card,
            name=constants.special_card_effects.POLYMERIZATION,
            spell_type=constants.spell_type.SPELL,
            spell_level=constants.spell_level.CARD,
            target_filter=None,
            extra_selection=None,
            stat_modifier=None,
            scopes=[],
            require_card_selection=False,
        )

class Hinotama(SpellManager.SpellManager):
#Inflict 500 damage to your opponent's Life Points.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.HINOTAMA,
            spell_type=constants.spell_type.TYPE_MODIFIER,
            spell_level=constants.spell_level.PLAYER,  
            stat_modifier={"life_points": -500},
            scopes=[constants.populationScope.OPPONENT],                                  
            target_filter=None, 
            extra_selection=None,           
            require_card_selection = False         
        )

class Sparks(SpellManager.SpellManager):
#Inflict 500 damage to your opponent's Life Points.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.SPARKS,
            spell_type=constants.spell_type.TYPE_MODIFIER,
            spell_level=constants.spell_level.PLAYER,  
            stat_modifier={"life_points": -200},
            scopes=[constants.populationScope.OPPONENT],                                  
            target_filter=None, 
            extra_selection=None,           
            require_card_selection = False         
        )

class RedMedicine(SpellManager.SpellManager):
# Increase your Life Points by 500.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.RED_MEDICINE,
            spell_type=constants.spell_type.TYPE_MODIFIER,
            spell_level=constants.spell_level.PLAYER,  
            stat_modifier={"life_points": 500},
            scopes=[constants.populationScope.PLAYER],                                  
            target_filter=None, 
            extra_selection=None,           
            require_card_selection = False         
        )

class Umi(SpellManager.SpellManager):
#Fish, Sea Serpent, Thunder, and Aqua gain 200 ATK/DEF; Machine and Pyro lose 200 ATK/DEF.  
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.UMI,
            spell_type=constants.spell_type.TYPE_MODIFIER,
            spell_level=constants.spell_level.CARD,             
            stat_modifier={
                "target_filter": [{"attr": "base_attack", "value": 200}, {"attr": "base_defense", "value": 200}],
                constants.race.FISH: [{"attr": "base_attack", "value": 200}, {"attr": "base_defense", "value": 200}],
                constants.race.SEA_SERPENT: [{"attr": "base_attack", "value": 200}, {"attr": "base_defense", "value": 200}],
                constants.race.THUNDER: [{"attr": "base_attack", "value": 200}, {"attr": "base_defense", "value": 200}],
                constants.race.AQUA: [{"attr": "base_attack", "value": 200}, {"attr": "base_defense", "value": 200}],
                constants.race.MACHINE: [{"attr": "base_attack", "value": -200}, {"attr": "base_defense", "value": -200}],
                constants.race.PYRO: [{"attr": "base_attack", "value": -200}, {"attr": "base_defense", "value": -200}],
            },
            scopes=[constants.populationScope.PLAYER_BATTLE, constants.populationScope.OPPONENT_BATTLE],
            target_filter=lambda c: c.race.lower() in {
                constants.race.FISH,
                constants.race.SEA_SERPENT,
                constants.race.THUNDER,
                constants.race.AQUA,
                constants.race.MACHINE,
                constants.race.PYRO,
            },
            extra_selection=None,           
            require_card_selection = False         
        )   

class Yami(SpellManager.SpellManager):
#Fiend and Spellcaster gain 200 ATK/DEF; Fairy monsters lose 200 ATK/DEF.
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.YAMI,
            spell_type=constants.spell_type.TYPE_MODIFIER,
            spell_level=constants.spell_level.CARD,             
            stat_modifier={
                constants.race.FIEND: [{"attr": "base_attack", "value": 200}, {"attr": "base_defense", "value": 200}],
                constants.race.SPELLCASTER: [{"attr": "base_attack", "value": 200}, {"attr": "base_defense", "value": 200}],
                constants.race.FAIRY: [{"attr": "base_attack", "value": -200}, {"attr": "base_defense", "value": -200}],
            },
            scopes=[constants.populationScope.PLAYER_BATTLE, constants.populationScope.OPPONENT_BATTLE],
            target_filter=lambda c: c.race.lower() in {
                constants.race.FIEND,
                constants.race.SPELLCASTER,
                constants.race.FAIRY,
            },
            extra_selection=None,           
            require_card_selection = False         
        )   

class RemoveTrap(SpellManager.SpellManager):
#Target 1 face-up Trap on the field; destroy it
    def __init__(self, original_card):
        super().__init__(
            original_card = original_card,
            name=constants.special_card_effects.REMOVE_TRAP,
            spell_type=constants.spell_type.DESTROY,
            spell_level=constants.spell_level.CARD,             
            stat_modifier= None,
            scopes=[constants.populationScope.OPPONENT_SPECIAL],                                  
            target_filter=lambda c: c.is_face_up and constants.card_types.TRAP in c.type, 
            extra_selection=None,           
            require_card_selection = True  
        )   

CARD_REGISTRY = {
    constants.special_card_effects.BEAST_FANGS: BeastFangs,
    constants.special_card_effects.BOOK_OF_SECRET_ARTS: BookOfSecretArts,
    constants.special_card_effects.DARK_ENERGY: DarkEnergy,
    constants.special_card_effects.LEGENDARY_SWORD: LegendarySword,
    constants.special_card_effects.POWER_OF_KAISHIN: PowerOfKaishin,
#    constants.special_card_effects.CAPTURE_JAR: CaptureJar,
    constants.special_card_effects.FOREST: Forest,  
    constants.special_card_effects.DARK_HOLE: DarkHole,     
    constants.special_card_effects.FISSURE: Fissure,     
    constants.special_card_effects.MOUNTAIN: Mountain,
    constants.special_card_effects.RAIGEKI: Raigeki,
    constants.special_card_effects.SOGEN: Sogen,    
    constants.special_card_effects.VIOLET_CRYSTAL: VioletCrystal,
    constants.special_card_effects.WASTELAND: Wasteland,
    constants.special_card_effects.TRAP_HOLE: TrapHole,
    constants.special_card_effects.POLYMERIZATION: Polymerization,
    constants.special_card_effects.HINOTAMA: Hinotama,
    constants.special_card_effects.SPARKS: Sparks,
    constants.special_card_effects.RED_MEDICINE: RedMedicine,
    constants.special_card_effects.UMI: Umi,
    constants.special_card_effects.YAMI: Yami,
    constants.special_card_effects.REMOVE_TRAP: RemoveTrap,

 }
