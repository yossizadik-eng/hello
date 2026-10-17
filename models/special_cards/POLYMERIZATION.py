#Fusion Summon 1 Fusion Monster using materials from your hand or field
def activate(board):
    board.show_popup("Select 1 monster from your hand or field to use as fusion material.")
    board.waiting_for_polymerization_materials = True