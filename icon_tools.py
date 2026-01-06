from PIL import Image
import argparse
import os

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
APP_ICO = os.path.join(ASSETS_DIR, 'app.ico')


def remove_white_background_to_transparency(img: Image.Image, threshold: int = 250) -> Image.Image:
    """Convert near-white background to transparent.
    threshold: 0-255; pixels with all channels >= threshold become transparent.
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    datas = img.getdata()
    new_data = []
    for r, g, b, a in datas:
        if r >= threshold and g >= threshold and b >= threshold:
            new_data.append((r, g, b, 0))
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    return img


def save_ico_from_png(png_path: str, ico_path: str = APP_ICO) -> str:
    img = Image.open(png_path)
    img = remove_white_background_to_transparency(img)
    # ICO sizes commonly used
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    # Ensure square by padding transparent if needed
    w, h = img.size
    if w != h:
        side = max(w, h)
        canvas = Image.new('RGBA', (side, side), (255, 255, 255, 0))
        canvas.paste(img, ((side - w) // 2, (side - h) // 2))
        img = canvas
    img.save(ico_path, sizes=sizes)
    return ico_path


def main():
    parser = argparse.ArgumentParser(description='Build app.ico from a source PNG, removing white background.')
    parser.add_argument('--source', required=True, help='Path to source PNG (e.g., assets/logo_source.png)')
    parser.add_argument('--out', default=APP_ICO, help='Output .ico path (default assets/app.ico)')
    args = parser.parse_args()
    os.makedirs(ASSETS_DIR, exist_ok=True)
    out = save_ico_from_png(args.source, args.out)
    print(f'Icon saved to: {out}')


if __name__ == '__main__':
    main()
