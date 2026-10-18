from PIL import Image, ImageDraw, ImageFont

img = Image.new("1", (384, 80), 1)
d = ImageDraw.Draw(img)
d.text((20, 20), "Hola MX10", font=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 40), fill=0)
img.save("prueba.png")
print("prueba.png", img.size)
