from PIL import Image, ImageColor

fill_colour = ImageColor.getrgb('#ff000000')
print(repr(fill_colour))

im = Image.open('exit.jpg')
im = im.convert(mode='RGBA')
px = im.load()
border_colour = px[1, 1]
print(border_colour)

def match_colour(c1, c2):
    assert len(c1) == 4
    assert len(c2) == 4
    distance = sum((b1-b2)**2 for b1, b2 in zip(c1, c2))
    return distance < 5000

width, height = im.size
border = 20

for y in range(height):
    for x in range(width):
        if not (border < x < width - border and border < y < height - border) and match_colour(px[x, y], border_colour):
            px[x, y] = fill_colour

im.save('exit.png')
im.show()
