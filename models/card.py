import io
import urllib.request
from PIL import Image, ImageTk
import constants

class Card:
    def __init__(self, data):
        self.name = data.get("name").lower() if data.get("name") else "Unknown Card"
        self.type = data.get("type").lower() if data.get("type") else "Unknown Type"
        self.attribute = data.get("attribute").lower() if data.get("attribute") else "Unknown Attribute"
        self.level = data.get("level")
        self.spell_speed = data.get("spell speed")
        self.base_attack= self._to_int(data.get("atk"), 0)
        self.base_defense = self._to_int(data.get("def"), 0)
        self.race = data.get("race").lower() if data.get("race") else "Unknown Race"
        self.image_url = data.get("card_images")[0].get("image_url")
        self.description = data.get("desc")
        self.is_face_up = True
        self.position  = constants.possition.ATTACK
        self.summon = True
        self.cached_photo = None
        self.x_position = 0
        self.y_position = 0
        self.selected = False
        self.can_be_selected = True
        self.effect_on_card = {}
        self.marked_for_graveyard = False
        self.attack_modifier = 0
        self.defense_modifier = 0
        self.summoned_this_turn = False
        self.has_changed_position_this_turn = False
        self.special_cards = []
        self.special_spells = []
        self.action = None
            
    @property
    def current_position(self):
        # Check if any active effect forces defense position
        # For example, look for "Dragon Capture Jar" in effect_on_card
        if constants.special_card_effects.CAPTURE_JAR in self.effect_on_card:
            return constants.possition.DEFENSE
        return self.position
    
    def set_position(self, new_position):        
        self.position = new_position

    @staticmethod
    def _to_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def get_photo(self, width, height, fallback_back_img, reveal=False):
        if not self.is_face_up and not reveal:
            return fallback_back_img
            
        if self.cached_photo is None:
            try:
                with urllib.request.urlopen(self.image_url) as url_stream:
                    raw_data = url_stream.read()
                    img_buffer = io.BytesIO(raw_data)
                    img = Image.open(img_buffer).resize((width, height))
                    self.cached_photo = ImageTk.PhotoImage(img)
            except Exception as exc:
                print(exc)
                return None
                
        return self.cached_photo
    
    def get_photo_enlared(self, width, height, fallback_back_img):        
        try:
            with urllib.request.urlopen(self.image_url) as url_stream:
                raw_data = url_stream.read()
                img_buffer = io.BytesIO(raw_data)
                img = Image.open(img_buffer).resize((width, height), Image.LANCZOS)
                enlarged_photo = ImageTk.PhotoImage(img)                    
                return enlarged_photo
        except Exception as exc:
            return None
                
        return self.enlarged_photo
    
    def get_stat_breakdown(self):
        print(f"Stats for {self.name}: Base {self.attack_points}/{self.defense_points}")
        for effect_name, stats in self.effect_on_card.items():
            print(f"  + {effect_name}: ATK {stats.get('atk', 0)}, DEF {stats.get('def', 0)}")
        print(f"  = Final: {self.atk}/{self.defense}")

    def has_effect_on_attribute(self, attribute_name):
    # Iterate through all active spell names
        for spell_name, mod_list in self.effect_on_card.items():
            # Iterate through the list of mods for each spell
            for mod in mod_list:
                if mod.get("attr") == attribute_name:
                    return True
        return False

    def stat_effect_direction(self, attribute_name):
        return sum(
            modifier.get("value", 0)
            for modifiers in self.effect_on_card.values()
            if isinstance(modifiers, list)
            for modifier in modifiers
            if modifier.get("attr") == attribute_name
        )