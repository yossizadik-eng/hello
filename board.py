import tkinter as tk
import constants
from PIL import Image, ImageTk
import random
import phase_managers.phase_manager as phase_manager
import deck
import phase_managers.draw_phase_manager as draw_phase_manager
from models.special_cards import spell_cards
from models.special_cards import monster_effects

class GameEngine:
    def __init__(self, master_window, player1, player2):
        self.master = master_window
        self.p1 = player1
        self.p2 = player2
        self.game_over = False
        self.p1.on_defeat = self.show_winner
        self.p2.on_defeat = self.show_winner
        self.attacking_card = None
        self.attacked_card = None      
        self.special_card_effects_this_turn = []
        self.special_affected_cards = []
        self.special_affected_cards_opposite = []
        self.continous_card_effects = []        
        # decide who starts first
        self.current_player = random.choice([self.p1, self.p2])
        if self.current_player == self.p1:            
            self.opposite_player = self.p2            
        else:                
            self.opposite_player = self.p1        
        self.current_player.draw_card_from_deck()
        self.current_player.turn_phase = constants.phase.MAIN1
        self.wait_for_hand_selection = False
        self.wait_for_battle_selection = False
        self.wait_for_special_selection = False
        self.wait_for_any_selection = False
        self.cards_for_selection = []
        
        self.lp_text_id_1 = ""
        self.lp_text_id_2 = ""
        self.phase_text_id = ""
        self.graveyard_count_ids = {}
        self.effect_log_entries = []
        self.pending_hand_discard = False
        self.action_prompt_id = None
        
        # Load the face down image once globally
        img = Image.open("face_down.JPG").resize((constants.card_width, constants.card_height))
        self.card_back_img = ImageTk.PhotoImage(img)
        self.label = tk.Label()

        
        self.image_references = []  
        self.enlarged_width = int(constants.card_width * 3)
        self.enlarged_height = int(constants.card_height * 3)
        self.focus_panel = tk.Frame(
            self.master,
            width=self.enlarged_width,
            height=self.enlarged_height,
            padx=5,
            pady=5,
        )
        self.focus_panel.grid(row=3, column=4, sticky="nw", padx=10, pady=5)

        canvas_width = int(constants.card_width * 5 * 1.1) + int(constants.card_width * 7)
        canvas_height = int(constants.card_height * 6 * 1.1)
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        self.board_canvas = tk.Canvas(self.master, bd=0, highlightthickness=0,
                                      width=canvas_width,
                                      height=canvas_height)
        # Load the board background and place it behind the card rows
        self.displaybackground()

        self.display_name_and_points(self.p1)
        self.display_name_and_points(self.p2)

        self.refresh_board()        

        self.display_graveyard(self.p1)
        self.display_graveyard(self.p2)

        self.display_deck(self.p1)
        self.display_deck(self.p2)

        self.display_phase_buttons()

        self.phase_manager = phase_manager.PhaseManager(self)
        self.show_start_banner()

    def displaybackground(self):
        bg_img_1 = Image.open("gameBoard_background.JPG").resize((int(constants.card_width * 5 * 1.1), int(constants.card_height * 6 * 1.1)), Image.LANCZOS)
        self.background_photo_1 = ImageTk.PhotoImage(bg_img_1)
                
        self.board_canvas.grid(row=0, column=0, rowspan=6, columnspan=4, sticky="nw")
        self.board_canvas.create_image(0, 0, image=self.background_photo_1, anchor="nw", tags="background")

    def display_name_and_points(self, player):
    # 1. Determine position (your existing logic)
        if player.player_number == constants.player_is_1:
            y = 15
            anchor = "nw"
        else:
            y = int(constants.card_height * 6 * 1.1) - 15
            anchor = "sw"
        x = int(constants.card_width * 5 * 1.1) + 15

        # 2. Determine color
        lp = player.life_points
        if lp <= 2000: fg_color = "red"
        elif lp <= 4000: fg_color = "orange"
        else: fg_color = "black"

        # 3. Create the text on the canvas
        # We store the ID so we can update it later
        lp_text_id = self.board_canvas.create_text(
            x, y, 
            text=f"{player.name}\nLP: {lp}", 
            fill=fg_color, 
            font=("Arial", 14, "bold"), 
            anchor=anchor
        )
        if (player == self.p1):
            self.lp_text_id_1 = lp_text_id
        else:
            self.lp_text_id_2 = lp_text_id

        
    def display_graveyard(self, player):
        if player.player_number == constants.player_is_1:
            y = constants.card_height + 15
            anchor = "nw"            
        else:
            y = int(constants.card_height * 3 ) + 65
            anchor = "nw"            
        x = int(constants.card_width * 5 * 1.1) + 15                
        text_id = self.board_canvas.create_text(
            x, y - 20,
            text=self.graveyard_summary(player),
            fill="black",
            font=("Arial", 14, "bold"),
            anchor=anchor,
            tags="info",
        )
        self.graveyard_count_ids[player] = text_id
        img = Image.open("face_down.JPG").resize((80, 115))
        photo = ImageTk.PhotoImage(img)
        image_label = tk.Label(self.board_canvas, image=photo )
        y += 30
        self.board_canvas.create_window(x, y, window=image_label, anchor="nw")
        image_label.image_reference = photo       
        image_label.bind("<Button-1>", lambda e: self.graveyard_click(player))
    
    def refresh_board(self):
                
        
    #    self.board_canvas.delete("all")
        self.image_references.clear()
        # Map out exactly which data collections go onto which row on the screen
        # Player 1 takes rows 0, 1, 2. Player 2 takes rows 3, 4, 5.

        layout = [
            (0, "#1104c9", self.p1.hand),
            (1, "#d1a153", self._row_special_cards(self.p1)),
            (2, "#c50707", self.p1.battle_cards),
            (3, "#c50707", self.p2.battle_cards),
            (4, "#d1a153", self._row_special_cards(self.p2)),
            (5, "#1104c9", self.p2.hand)
        ]

        self.board_canvas.delete("card")
        self.board_canvas.delete("highlight")
        self.board_canvas.delete("spell_target")
        self.board_canvas.delete("sword")
        self.board_canvas.delete("extra_deck_zone")
        self.board_canvas.delete("field_spell_zone")
        self.board_canvas.delete("spell_availability")

        for row_num, bk_color, card_list in layout:
            self.draw_row(row_num, bk_color, card_list)
        self.draw_spell_target_highlights()
        self.draw_extra_deck_zone(self.p1)
        self.draw_extra_deck_zone(self.p2)
        self.draw_field_spell_zone(self.p1)
        self.draw_field_spell_zone(self.p2)
        self.update_lp_on_canvas(self.p1)
        self.update_lp_on_canvas(self.p2)
        self.update_graveyard_counts()
        self.display_phase_on_canvas()        
        if self.game_over:
            self.board_canvas.tag_raise("game_over")

    @staticmethod
    def _row_special_cards(player):
        return [
            card
            for card in player.special_cards
            if constants.race.FIELD not in card.race
        ]

    def draw_extra_deck_zone(self, player):
        x = int(constants.card_width * 7.0)
        y = 165 if player == self.p1 else int(constants.card_height * 4.1)
        label = f"Extra Deck ({len(player.extra_deck)})"
        self.board_canvas.create_text(
            x,
            y,
            text=label,
            fill="black",
            font=("Arial", 12, "bold"),
            anchor="nw",
            tags=("extra_deck_zone", f"extra_deck_{player.player_number}"),
        )
        if not player.extra_deck:
            return
        image_id = self.board_canvas.create_image(
            x,
            y + 24,
            image=self.card_back_img,
            anchor="nw",
            tags=("extra_deck_zone", f"extra_deck_{player.player_number}"),
        )
        self.board_canvas.tag_bind(
            image_id,
            "<Button-1>",
            lambda event, owner=player: self.show_extra_deck(owner),
        )
        self.board_canvas.tag_bind(
            image_id,
            "<Enter>",
            lambda event: self.board_canvas.config(cursor="hand2"),
        )
        self.board_canvas.tag_bind(
            image_id,
            "<Leave>",
            lambda event: self.board_canvas.config(cursor=""),
        )

    def draw_field_spell_zone(self, player):
        x = int(constants.card_width * 8.1)
        y = 165 if player == self.p1 else int(constants.card_height * 4.1)
        field_spells = [
            card
            for card in player.special_cards
            if constants.race.FIELD in card.race
        ]
        self.board_canvas.create_text(
            x + 45,
            y,
            text=f"{player.name}'s Field Spell",
            fill="black",
            font=("Arial", 11, "bold"),
            width=130,
            justify="center",
            anchor="n",
            tags=("field_spell_zone",),
        )
        if not field_spells:
            self.board_canvas.create_text(
                x + 45,
                y + 28,
                text="Empty",
                fill="black",
                font=("Arial", 10),
                width=130,
                justify="center",
                anchor="n",
                tags=("field_spell_zone",),
            )
            return

        card = field_spells[-1]
        image = card.get_photo(
            90, 125, self.card_back_img, reveal=card.is_face_up
        )
        if image is None:
            image = self.card_back_img
        self.image_references.append(image)
        image_id = self.board_canvas.create_image(
            x,
            y + 24,
            image=image,
            anchor="nw",
            tags=("field_spell_zone",),
        )
        self.board_canvas.create_text(
            x + 45,
            y + 153,
            text=card.name,
            fill="black",
            font=("Arial", 10, "bold"),
            width=120,
            justify="center",
            anchor="n",
            tags=("field_spell_zone",),
        )
        self.board_canvas.tag_bind(
            image_id,
            "<Button-1>",
            lambda event, selected_card=card: self.handle_card_click(selected_card),
        )
        self.board_canvas.tag_bind(
            image_id,
            "<Button-3>",
            lambda event, selected_card=card: self.handle_card_right_click(selected_card),
        )
        self.board_canvas.tag_bind(
            image_id,
            "<Enter>",
            lambda event, field_card=card: self.display_card_in_focus(field_card),
        )
        self.board_canvas.tag_bind(
            image_id,
            "<Leave>",
            lambda event, field_card=card: self.hide_card_in_focus(field_card),
        )

    def show_extra_deck(self, player):
        window = tk.Toplevel(self.master)
        window.title(f"{player.name}'s Extra Deck")
        window.geometry("420x480")
        container = tk.Frame(window)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        cards_frame = tk.Frame(canvas)
        cards_frame.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=cards_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not player.extra_deck:
            tk.Label(cards_frame, text="Extra Deck is empty.").pack(padx=12, pady=12)
        for fusion_card in player.extra_deck:
            tk.Label(
                cards_frame,
                text=f"{fusion_card.name}\n{fusion_card.description or ''}",
                justify="left",
                wraplength=360,
                anchor="w",
            ).pack(fill="x", padx=8, pady=6)
        tk.Button(window, text="Close", command=window.destroy).pack(pady=(0, 10))

    def update_graveyard_counts(self):
        for player, text_id in getattr(self, "graveyard_count_ids", {}).items():
            self.board_canvas.itemconfig(
                text_id,
                text=self.graveyard_summary(player),
            )

    @staticmethod
    def graveyard_summary(player):
        return (
            f"Graveyard\nMonsters: {len(player.graveyard_monsters)}"
            f" | Spells/Traps: {len(player.graveyard_spell_traps)}"
        )

    def show_start_banner(self):
        center_x = self.canvas_width / 2
        center_y = self.canvas_height / 2
        self.board_canvas.create_rectangle(
            center_x - 360,
            center_y - 80,
            center_x + 360,
            center_y + 80,
            fill="#101010",
            outline="#f4d03f",
            width=5,
            tags=("start_banner",),
        )
        self.board_canvas.create_text(
            center_x,
            center_y,
            text=f"{self.current_player.name} is starting",
            fill="#f4d03f",
            font=("Arial", 36, "bold"),
            tags=("start_banner",),
        )
        self.board_canvas.tag_raise("start_banner")
        self.master.after(
            2000,
            lambda: self.board_canvas.delete("start_banner"),
        )

    def update_lp_on_canvas(self, player):
        current_lp = player.life_points
        color = "red" if int(current_lp) <= 2000 else "black"
        if player == self.p1:
            lp_text_id = self.lp_text_id_1
        else:
            lp_text_id = self.lp_text_id_2
        self.board_canvas.itemconfig(
        lp_text_id, 
        text=f"{player.name}\nLP: {current_lp}",
        fill=color
        )     

    def show_winner(self, defeated_player):
        if self.game_over:
            return
        self.game_over = True
        winner = self.p2 if defeated_player is self.p1 else self.p1
        center_x = getattr(
            self,
            "canvas_width",
            int(constants.card_width * 5 * 1.1) + int(constants.card_width * 7),
        ) / 2
        center_y = getattr(
            self,
            "canvas_height",
            int(constants.card_height * 6 * 1.1),
        ) / 2
        self.board_canvas.create_rectangle(
            center_x - 340,
            center_y - 100,
            center_x + 340,
            center_y + 100,
            fill="#101010",
            outline="#f4d03f",
            width=5,
            tags=("game_over",),
        )
        self.board_canvas.create_text(
            center_x,
            center_y,
            text=f"{winner.name}\nHAS WON!",
            fill="#f4d03f",
            font=("Arial", 42, "bold"),
            justify="center",
            tags=("game_over",),
        )
        self.board_canvas.tag_raise("game_over")

    def update_phase_ui(self):
        self.board_canvas.itemconfig(
        self.phase_text_id, 
        text=f"Player {self.current_player.name} PHASE: {self.current_player.turn_phase.value}"
        )
        phase_color = "red" if self.current_player.turn_phase == constants.phase.BATTLE else "black"
        self.board_canvas.itemconfig(self.phase_text_id, fill=phase_color)      

    def draw_spell_target_highlights(self):
        manager = getattr(self, "phase_manager", None)
        spell = getattr(manager, "special_card", None)
        targets = []
        if (
            manager is not None
            and manager.step == constants.step.WAIT_FOR_BATTLE_CARD
            and spell is not None
        ):
            targets.extend(spell.valid_cards)
        pending_effect = getattr(manager, "pending_monster_effect", None)
        if pending_effect is not None:
            targets.extend(pending_effect["targets"])
        for target in dict.fromkeys(targets):
            if (
                target not in self.current_player.battle_cards
                and target not in self.opposite_player.battle_cards
                and target not in self.current_player.special_cards
                and target not in self.opposite_player.special_cards
            ):
                continue
            x_position = getattr(target, "x_position", 0)
            y_position = getattr(target, "y_position", 0)
            if target in self.current_player.special_cards and constants.race.FIELD in target.race:
                x_position = int(constants.card_width * 8.1)
                y_position = 165 if self.current_player is self.p1 else int(constants.card_height * 4.1)
            elif target in self.opposite_player.special_cards and constants.race.FIELD in target.race:
                x_position = int(constants.card_width * 8.1)
                y_position = 165 if self.opposite_player is self.p1 else int(constants.card_height * 4.1)
            self.board_canvas.create_rectangle(
                x_position - 4,
                y_position - 4,
                x_position + constants.card_width * 0.8 + 4,
                y_position + constants.card_height * 0.8 + 4,
                fill="",
                outline="#00ff00",
                width=3,
                dash=(5, 3),
                tags=("spell_target",),
            )

    def prompt_card_target(self, player, targets, message):
        if self.action_prompt_id is not None:
            self.board_canvas.delete(self.action_prompt_id)
        self.action_prompt_id = self.board_canvas.create_text(
            self.canvas_width / 2,
            self.canvas_height - 24,
            text=f"{player.name}: {message}",
            fill="#f4d03f",
            font=("Arial", 16, "bold"),
            anchor="center",
            tags=("action_prompt",),
        )

    def clear_card_target_prompt(self):
        if self.action_prompt_id is not None:
            self.board_canvas.delete(self.action_prompt_id)
            self.action_prompt_id = None

    def prompt_hand_discard(self):
        self.pending_hand_discard = True
        if self.action_prompt_id is not None:
            self.board_canvas.delete(self.action_prompt_id)
        self.action_prompt_id = self.board_canvas.create_text(
            self.canvas_width / 2,
            self.canvas_height - 24,
            text=f"{self.current_player.name}: destroy one card from your hand",
            fill="#f4d03f",
            font=("Arial", 16, "bold"),
            anchor="center",
            tags=("action_prompt",),
        )

    def complete_hand_discard(self, card):
        if not self.pending_hand_discard or card not in self.current_player.hand:
            return False
        constants.destroy_card(self, card)
        self.pending_hand_discard = False
        self.clear_card_target_prompt()
        success, message = self.phase_manager.can_move_to_phase(
            self.current_player,
            constants.phase.END,
        )
        if not success:
            self.show_popup(message)
            return False
        self.change_current_player()
        self.refresh_board()
        return True

    def activate_face_down_special(self, card):
        if card not in self.current_player.special_cards or card.is_face_up:
            return False
        card.is_face_up = True
        self.refresh_board()
        if not self.ask_yes_no("Activate card?", f"Activate {card.name}?"):
            return True
        self.phase_manager.special_card_clicked(card)
        self.refresh_board()
        return True

    def log_effect_resolution(self, message):
        self.effect_log_entries.append(message)
        self.effect_log_entries = self.effect_log_entries[-200:]

    def show_effect_log(self):
        window = tk.Toplevel(self.master)
        window.title("Effect Resolution Log")
        window.geometry("520x360")
        container = tk.Frame(window)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        entries = tk.Listbox(container, exportselection=False)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=entries.yview)
        entries.configure(yscrollcommand=scrollbar.set)
        entries.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        if not self.effect_log_entries:
            entries.insert(tk.END, "No effects have resolved yet.")
        else:
            for entry in self.effect_log_entries:
                entries.insert(tk.END, entry)
            entries.see(tk.END)
        tk.Button(window, text="Close", command=window.destroy).pack(pady=(0, 10))

    def display_phase_on_canvas(self):
    # Place this at a convenient location, e.g., center-right of the board
        if hasattr(self, 'phase_text_id') and self.phase_text_id:
            self.board_canvas.delete(self.phase_text_id)
        x = int(constants.card_width * 9) 
        y = 20
        
        self.phase_text_id = self.board_canvas.create_text(
            x, y, 
            text=f"Player {self.current_player.name} PHASE: {self.current_player.turn_phase.value}", 
            fill="black", 
            font=("Arial", 18, "bold"),
            anchor="center"
    )

    def draw_row(self, row_num, bk_color, cards):
        max_cards_before_overlap = 5

        card_count = len(cards)
        if card_count == 0 and (row_num == 0 or row_num == 5):
            return

        if card_count > max_cards_before_overlap:
            x_step = max(
                (constants.card_width + constants.padding) * max_cards_before_overlap / card_count,
                constants.card_width * 0.25
            )
        else:
            x_step = constants.card_width + constants.padding

        row_height = constants.card_height + 15
        y_base = row_num * row_height  + 10
        y_offset = 0        
        x_offset = 13
        for card in cards:
            if card.is_face_up:
                photo = card.get_photo(constants.card_width, constants.card_height, self.card_back_img)
            else:
                photo = self.card_back_img
            pil_img = ImageTk.getimage(photo)
            y_offset = y_base 
            if row_num > 2 and row_num < 5:
                y_offset += 30

            if card.current_position == constants.possition.DEFENSE or not card.summon:
                pil_img = pil_img.rotate(90, expand=True)
                pil_img = pil_img.resize((int(pil_img.width * 0.8), int(pil_img.height * 0.8)), Image.LANCZOS)
                y_offset += 25
                if row_num == 3 :
                    y_offset -= 15
            if (row_num != 0 and row_num != 5):
                x_offset += 10
                pil_img = pil_img.resize((int(pil_img.width * 0.75), int(pil_img.height * 0.75)), Image.LANCZOS)

            photo = ImageTk.PhotoImage(pil_img)
            
            card.x_position = int(x_offset)
            card.y_position = y_offset            
            if card.selected :
                self.board_canvas.create_rectangle(
                    card.x_position -6, card.y_position -6, card.x_position + constants.card_width * 0.8 + 3, card.y_position + constants.card_height * 0.8 + 10 ,
                    fill="",            
                    outline="blue",     
                    width=3,            
                    tags="highlight"    # Tag allows you to clear it easily later
                    )
            img_id = self.board_canvas.create_image(int(x_offset), y_offset, image=photo, anchor="nw", tags="card")        
            self.image_references.append(photo)                
            self.board_canvas.tag_bind(img_id, "<Button-1>", lambda e, c=card: self.handle_card_click(c))
            self.board_canvas.tag_bind(img_id, "<Button-3>", lambda e, c=card: self.handle_card_right_click(c))
            self.board_canvas.tag_bind(img_id, "<Enter>", lambda e, c=card: self.handle_card_hover(e, c))
            self.board_canvas.tag_bind(img_id, "<Leave>", lambda e, c=card: self.handle_card_leave(e, c))

            if card.action == constants.battle_action.ATTACKING:     
                attack_img = Image.open("attack_sword.PNG")
                attack_img = attack_img.resize((int(attack_img.width * 0.2), int(attack_img.height * 0.2)), Image.LANCZOS)
                attack_tk = ImageTk.PhotoImage(attack_img)
                self.board_canvas.create_image(x_offset - 10, y_offset, image=attack_tk, anchor="nw", tags="sword")
                self.image_references.append(attack_tk)   
            elif hasattr(self, 'attack_id'):  
                    if not self.attack_id == None:
                        self.board_canvas.delete(self.attack_id)                                 

            if (row_num != 0 and row_num != 5):
                x_step -= 5
                if row_num == 2 or row_num == 3:
                    stat_y = (
                        y_offset - 24
                        if row_num == 2
                        else y_offset + constants.card_height - 40
                    )
                    self.board_canvas.create_text(
                        int(x_offset) + 3,
                        stat_y,
                        text=str(card.base_attack),
                        fill=self._stat_color(card, "base_attack", "black"),
                        font=("Arial", 11, "bold"),
                        anchor="nw",
                        tags="card",
                    )
                    self.board_canvas.create_text(
                        int(x_offset) + 48,
                        stat_y,
                        text=str(card.base_defense),
                        fill=self._stat_color(card, "base_defense", "blue"),
                        font=("Arial", 11, "bold"),
                        anchor="nw",
                        tags="card",
                    )
            x_offset += x_step    

    @staticmethod
    def _stat_color(card, attribute, default_color):
        direction = card.stat_effect_direction(attribute)
        if direction > 0:
            return "green"
        if direction < 0:
            return "red"
        return default_color

    def handle_card_hover(self, event, card):
        self.display_card_in_focus(card)
        self.board_canvas.delete("spell_availability")
        if not self._spell_has_available_battlefield_target(card):
            return
        self.board_canvas.create_text(
            card.x_position + constants.card_width * 0.35,
            card.y_position + 12,
            text="Available!",
            fill="#00ff00",
            font=("Arial", 11, "bold"),
            state=tk.DISABLED,
            tags=("spell_availability",),
        )

    def handle_card_leave(self, event, card):
        self.hide_card_in_focus(card)
        self.board_canvas.delete("spell_availability")

    def _spell_has_available_battlefield_target(self, card):
        if (
            card not in self.current_player.hand
            and card not in self.current_player.special_cards
        ):
            return False
        if (
            not card.can_be_selected
            or self.current_player.turn_phase
            not in (constants.phase.MAIN1, constants.phase.MAIN2)
        ):
            return False

        spell_class = spell_cards.CARD_REGISTRY.get(card.name)
        if spell_class is None:
            return False
        spell = spell_class(original_card=card)
        if (
            spell.spell_level != constants.spell_level.CARD
            or spell.spell_type != constants.spell_type.TYPE_MODIFIER
            or spell.target_filter is None
            or not spell.get_valid_targets(self)
        ):
            return False
        return any(
            target in owner.battle_cards
            for target in spell.valid_cards
            for owner in (self.current_player, self.opposite_player)
        )

    def display_card_in_focus(self, card):    
        photo = card.get_photo_enlared(self.enlarged_width, self.enlarged_height, self.card_back_img)
        for widget in self.focus_panel.winfo_children():
            widget.destroy()
        image_label = tk.Label(self.focus_panel, image=photo)
        image_label.image_reference = photo
        image_label.pack()

    def hide_card_in_focus(self, card):
        for widget in self.focus_panel.winfo_children():
            widget.destroy()

    def display_phase_buttons(self):
        button_panel = tk.Frame(self.master, width=200, height=200, padx=5, pady=5)
        button_panel.grid(row=1, column=4, sticky="nw", padx=10, pady=5)

        for phase in constants.phase:
            btn = tk.Button(button_panel, text=phase.name, width=20, command=lambda p=phase: self.phase_button_clicked(p))
            btn.pack(pady=2)
        tk.Button(
            button_panel,
            text="Effect Log",
            width=20,
            command=self.show_effect_log,
        ).pack(pady=8)

    def display_deck(self, player):
        if player == self.p1:         
            y = (constants.card_height + 15) * 2 
            anchor = "nw"        
        else:
            y = int(constants.card_height * 5 * 1.1) - 120
            anchor = "sw" 
        x = int(constants.card_width * 5 * 1.1) + 15                
        self.board_canvas.create_text(x, y, text="Deck", fill="black", font=("Arial", 14, "bold"), anchor=anchor, tags="info")
        img = Image.open("face_down.JPG").resize((80, 115))
        photo = ImageTk.PhotoImage(img)
        image_label = tk.Label(self.board_canvas, image=photo )
        if player == self.p1:
            y += 20        
        self.board_canvas.create_window(x, y, window=image_label, anchor="nw")
        image_label.image_reference = photo               
        image_label.bind("<Button-1>", lambda event, p=player: self.handle_deck_click(p))

        
# event handlers
    def phase_button_clicked(self, phase_button):            
        if self.game_over:
            return
        valid, message = self.phase_manager.phase_button_is_valid(
            self.current_player,
            phase_button,
        )
        if not valid:
            self.display_ok_message("invalid phase change", message)
            return
        if (
            phase_button == constants.phase.END
            and len(self.current_player.hand) >= 7
        ):
            self.prompt_hand_discard()
            return
        success, message = self.phase_manager.can_move_to_phase(self.current_player, phase_button)
        if not success:
            self.display_ok_message("invalid phase change", message)        
        else:
            if phase_button == constants.phase.END:
                self.change_current_player()

        self.update_phase_ui()              

    def handle_card_click(self, card):                        
        if self.game_over:
            return
        if self.pending_hand_discard:
            self.complete_hand_discard(card)
            return
        if self.phase_manager.pending_monster_effect is not None:
            self.phase_manager.select_monster_effect_target(card)
            self.refresh_board()
            return
        if self.phase_manager.pending_fusion_spell is not None:
            self.phase_manager.select_fusion_material(card)
            self.refresh_board()
            return
        if card in self.current_player.hand:
            self.phase_manager.hand_card_clicked(card)                                
        elif card in self.current_player.special_cards:
            self.phase_manager.special_card_clicked(card)                                
        elif card in self.current_player.battle_cards or card in self.opposite_player.battle_cards:
            if not self.phase_manager.special_card_selected == None :         
                self.phase_manager.handle_special_card(card)                
            else:
                self.phase_manager.battle_card_clicked(card)
                
        self.refresh_board()
        
    def handle_card_right_click(self, card):
        if self.game_over:
            return
        if card in self.current_player.special_cards and not card.is_face_up:
            self.activate_face_down_special(card)
            return
        if card in self.current_player.hand:
            if constants.card_types.MONSTER not in card.type:
                self.phase_manager.set_hand_spell_or_trap(card)
            else:
                self.phase_manager.right_click(self.current_player, card)
            self.refresh_board()
        elif card in self.current_player.battle_cards:
            self.phase_manager.right_click(self.current_player, card)
            self.refresh_board()

    def graveyard_click(self, player):
        monsters = player.graveyard_monsters
        spell_traps = player.graveyard_spell_traps
        window = tk.Toplevel(self.master)
        window.title(f"{player.name}'s Graveyard")
        window.geometry("640x520")

        container = tk.Frame(window)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        cards_frame = tk.Frame(canvas)
        cards_frame.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=cards_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not player.graveyard:
            tk.Label(
                cards_frame,
                text="No cards in this graveyard.",
                font=("Arial", 12),
            ).grid(row=0, column=0, padx=12, pady=12)
        else:
            row = 0
            for section_title, cards in (
                ("Monsters", monsters),
                ("Spells and Traps", spell_traps),
            ):
                tk.Label(
                    cards_frame,
                    text=section_title,
                    font=("Arial", 14, "bold"),
                ).grid(row=row, column=0, columnspan=4, sticky="w", padx=8, pady=8)
                row += 1
                if not cards:
                    tk.Label(
                        cards_frame,
                        text=f"No {section_title.lower()} in this graveyard.",
                        font=("Arial", 11),
                    ).grid(row=row, column=0, columnspan=4, sticky="w", padx=12)
                    row += 1
                    continue
                for index, card in enumerate(cards):
                    photo = card.get_photo(
                        100, 140, self.card_back_img, reveal=True
                    )
                    photo = photo or self.card_back_img
                    card_frame = tk.Frame(cards_frame, padx=8, pady=8)
                    card_frame.grid(
                        row=row + index // 4,
                        column=index % 4,
                        sticky="n",
                    )
                    image_label = tk.Label(card_frame, image=photo)
                    image_label.image_reference = photo
                    image_label.pack()
                    stats = (
                        f"\nATK {card.base_attack} / DEF {card.base_defense}"
                        if constants.card_types.MONSTER in card.type
                        else ""
                    )
                    tk.Label(
                        card_frame,
                        text=f"{card.name}{stats}",
                        wraplength=120,
                        justify="center",
                    ).pack(pady=(4, 0))
                row += (len(cards) + 3) // 4

        tk.Button(window, text="Close", command=window.destroy).pack(pady=(0, 10))

    def handle_deck_click(self, player):
        if self.game_over:
            return
        if player is not self.current_player:
            self.show_popup("You can only draw from your own deck.")
            return
        self.draw_card_from_deck()

    def draw_card_from_deck(self):
        drawn_card = self.current_player.draw_card_from_deck()
        if drawn_card is None:
            self.show_popup("You cannot draw a card: your deck is empty or you already drew this turn.")
            return
        self.phase_manager.check_trap_triggers(constants.events.DRAW, drawn_card)
        self.phase_manager.check_opponenet_quick_spell()
        if self.current_player.turn_phase == constants.phase.DRAW:
            self.current_player.turn_phase = constants.phase.MAIN1
        self.refresh_board()
            
    def change_current_player(self):        
        player = self.current_player
        player.has_drawn_this_turn = False
        player.has_summoned_this_turn = False
        for card in player.hand:    
            card.can_be_selected = True
        for card in player.battle_cards:    
            card.can_be_selected = True
        for card in player.special_cards:    
            card.can_be_selected = True      
        
        self.current_player = self.opposite_player
        self.opposite_player = player
        self.current_player.turn_phase = constants.phase.DRAW
        for card in self.current_player.battle_cards:
            card.summoned_this_turn = False
            card.has_changed_position_this_turn = False
        self.current_player.is_attacking.clear()
        self.draw_card_from_deck()

    def any_player_can_use_spell(self):
        for c in self.current_player.special_cards :
            if c.can_be_selected == True and constants.race.QUICK_SPELL in c.race:
                return True
        for c in self.opposite_player.special_cards :
            if c.can_be_selected == True and constants.race.QUICK_SPELL in c.race:                
                return True
        return False
    
    def show_popup(self, message):
        popup = tk.Label(self.master, text=message, bg="#f5f5f5", fg="black", 
                        font=("Arial", 14, "bold"), relief="solid", padx=20, pady=10)
        popup.place(relx=0.5, rely=0.5, anchor="center")
        
        # 3. Schedule removal after 2 seconds
        self.master.after(2000, popup.destroy)    

    def two_pronged_attack(self, card):
        if len(self.current_player.battle_cards) >= 2 and len(self.opposite_player.battle_cards) >= 1:
            self.show_popup(f"{self.current_player.name} choose 2 of your monsters that you would like to tribute and 1 from your opponent's to destroy!")
            self.special_card_effects_this_turn = [card]
            self.special_card_affected_cards = []

    def ask_yes_no(self, title, message):
        popup = tk.Toplevel(self.master)
        popup.title(title)
        
        result = {"choice": None} # Use a dictionary so it's mutable inside the lambda
        popup.geometry("300x150") 
        popup.configure(bg="#f5f5f5")
    
        label = tk.Label(
            popup, 
            text=message, 
            bg="#f5f5f5", 
            fg="black", 
            font=("Arial", 12, "bold"),
            wraplength=250 # Wraps long text so it doesn't go off-screen
        )
        label.pack(pady=20, padx=10)

        
        def on_yes():
            result["choice"] = True
            popup.destroy()
            
        def on_no():
            result["choice"] = False
            popup.destroy()
            
        btn_yes = tk.Button(popup, text="Yes", command=on_yes)
        btn_yes.pack(side=tk.LEFT, padx=20)
        
        btn_no = tk.Button(popup, text="No", command=on_no)
        btn_no.pack(side=tk.RIGHT, padx=20)
        
        popup.wait_window(popup)
        
        return result["choice"]
    
    def display_ok_message(self, title, message):
        popup = tk.Toplevel(self.master)
        popup.title(title)
        
        popup.geometry("500x150") 
        popup.configure(bg="#f5f5f5")
    
        label = tk.Label(
            popup, 
            text=message, 
            bg="#f5f5f5", 
            fg="black", 
            font=("Arial", 12, "bold"),
            wraplength=450 # Wraps long text so it doesn't go off-screen
        )
        label.pack(pady=20, padx=10)

        def on_ok():
            popup.destroy()

        btn_ok = tk.Button(popup, text="OK", command=on_ok)
        btn_ok.pack(padx=20)
        popup.wait_window(popup)        
        return True

    def choose_fusion_monster(self, fusion_cards):
        if not fusion_cards:
            return None
        if len(fusion_cards) == 1:
            return fusion_cards[0]

        popup = tk.Toplevel(self.master)
        popup.title("Choose a Fusion Monster")
        popup.geometry("360x400")
        tk.Label(
            popup,
            text="Select the Fusion Monster to summon:",
            font=("Arial", 12, "bold"),
        ).pack(padx=10, pady=10)
        choices = tk.Listbox(popup, height=14, exportselection=False)
        for fusion_card in fusion_cards:
            choices.insert(tk.END, fusion_card.name)
        choices.pack(fill="both", expand=True, padx=10, pady=10)
        choices.selection_set(0)

        result = {"card": None}

        def confirm():
            selection = choices.curselection()
            if selection:
                result["card"] = fusion_cards[selection[0]]
                popup.destroy()

        tk.Button(popup, text="Summon", command=confirm).pack(pady=(0, 10))
        popup.wait_window(popup)
        return result["card"]

    def choose_chain_response(self, player, candidates, chain_labels):
        if not candidates:
            return None

        popup = tk.Toplevel(self.master)
        popup.title(f"{player.name}: Chain Response")
        popup.geometry("440x420")
        tk.Label(
            popup,
            text=(
                f"Current chain: {' -> '.join(chain_labels)}\n"
                "Choose one response or pass priority."
            ),
            justify="left",
            wraplength=410,
        ).pack(fill="x", padx=12, pady=12)
        choices = tk.Listbox(popup, height=12, exportselection=False)
        for candidate in candidates:
            choices.insert(tk.END, candidate["card"].name)
        choices.pack(fill="both", expand=True, padx=12, pady=8)
        choices.selection_set(0)
        result = {"card": None}

        def activate():
            selection = choices.curselection()
            if selection:
                result["card"] = candidates[selection[0]]["card"]
                popup.destroy()

        buttons = tk.Frame(popup)
        buttons.pack(fill="x", padx=12, pady=12)
        tk.Button(buttons, text="Activate", command=activate).pack(side="left")
        tk.Button(
            buttons,
            text="Pass",
            command=popup.destroy,
        ).pack(side="right")
        popup.wait_window(popup)
        return result["card"]

    def choose_chain_target(self, player, targets, spell_name):
        if not targets:
            return None
        if len(targets) == 1:
            return targets[0]

        popup = tk.Toplevel(self.master)
        popup.title(f"Choose target for {spell_name}")
        popup.geometry("380x400")
        tk.Label(
            popup,
            text=f"{player.name}, select a target for {spell_name}:",
            wraplength=350,
        ).pack(fill="x", padx=12, pady=12)
        choices = tk.Listbox(popup, height=12, exportselection=False)
        for target in targets:
            choices.insert(
                tk.END,
                f"{target.name} (ATK {target.base_attack} / DEF {target.base_defense})",
            )
        choices.pack(fill="both", expand=True, padx=12, pady=8)
        choices.selection_set(0)
        result = {"card": None}

        def confirm():
            selection = choices.curselection()
            if selection:
                result["card"] = targets[selection[0]]
                popup.destroy()

        tk.Button(popup, text="Target", command=confirm).pack(pady=(0, 12))
        popup.wait_window(popup)
        return result["card"]

    def choose_monster_effect_target(self, player, targets, monster_name):
        if not targets:
            return None

        popup = tk.Toplevel(self.master)
        popup.title(f"Resolve {monster_name}'s Effect")
        popup.geometry("380x400")
        tk.Label(
            popup,
            text=(
                f"{player.name}, choose a monster to "
                f"{self._monster_effect_action(monster_name).lower()}:"
            ),
            wraplength=350,
        ).pack(fill="x", padx=12, pady=12)
        choices = tk.Listbox(popup, height=12, exportselection=False)
        for target in targets:
            label = (
                f"{target.name} (ATK {target.base_attack} / DEF {target.base_defense})"
                if target.is_face_up
                else "Face-down monster"
            )
            choices.insert(tk.END, label)
        choices.pack(fill="both", expand=True, padx=12, pady=8)
        choices.selection_set(0)
        result = {"card": None}

        def confirm():
            selection = choices.curselection()
            if selection:
                result["card"] = targets[selection[0]]
                popup.destroy()

        tk.Button(
            popup,
            text=self._monster_effect_action(monster_name),
            command=confirm,
        ).pack(pady=(0, 12))
        popup.wait_window(popup)
        return result["card"]

    @staticmethod
    def _monster_effect_action(monster_name):
        effect = monster_effects.FLIP_EFFECT_REGISTRY.get(monster_name.casefold())
        return getattr(effect, "action_label", "Select")
