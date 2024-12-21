from PIL import Image
import os

# Open the webp image
img = Image.open('logo.webp')

# Convert to RGBA if not already
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Create icon sizes
sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
icon_images = []

for size in sizes:
    # Resize the image with high quality
    resized_img = img.resize(size, Image.Resampling.LANCZOS)
    icon_images.append(resized_img)

# Save as ICO
img.save('logo.ico', format='ICO', sizes=[(img.size[0], img.size[1])])
print("Conversion complete! logo.ico has been created.")
