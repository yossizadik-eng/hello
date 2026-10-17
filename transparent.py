from PIL import Image

def remove_white_background(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        # Check if the pixel is white (or close to white)
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0)) # Set alpha to 0 (transparent)
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")

# Run this once to get your new file
remove_white_background("attack_sword.jpg", "attack_sword.png")