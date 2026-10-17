import constants
import tkinter as tk
import constants
from PIL import Image, ImageTk

def display_deck(board):
        if board.current_player == board.p1:         
            row_num = 2   
            y = (constants.card_height + 15) * 2 
            anchor = "nw"        
        else:
            row_num = 3
            y = int(constants.card_height * 5 * 1.1) - 120
            anchor = "sw" 
        x = int(constants.card_width * 5 * 1.1) + 15                
        board.board_canvas.create_text(x, y, text="Deck", fill="black", font=("Arial", 14, "bold"), anchor=anchor, tags="info")
        img = Image.open("face_down.JPG").resize((80, 115))
        photo = ImageTk.PhotoImage(img)
        image_label = tk.Label(board.board_canvas, image=photo )
        if board.current_player == board.p1:
            y += 20        
        board.board_canvas.create_window(x, y, window=image_label, anchor="nw")
        image_label.image_reference = photo               
        image_label.bind("<Button-1>", lambda e: board.draw_card_from_deck())
