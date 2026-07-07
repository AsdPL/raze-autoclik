"""
Ejecuta este script UNA VEZ para generar el archivo icon.ico
antes de compilar con PyInstaller.
Requiere: pip install Pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    sizes = [16, 32,48, 64, 128, 256]
    frames = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Fondo circular degradado (azul oscuro)
        margin = max(1, size // 16)
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill="#0f3460",
        )

        # Círculo interior (acento rojo)
        inner = size // 4
        draw.ellipse(
            [inner, inner, size - inner, size - inner],
            fill="#e94560",
        )

        # Punto central blanco
        center = size // 2
        dot = max(1, size // 8)
        draw.ellipse(
            [center - dot, center - dot, center + dot, center + dot],
            fill="#ffffff",
        )

        frames.append(img)

    out_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    frames[0].save(
        out_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"Ícono creado: {out_path}")

if __name__ == "__main__":
    create_icon()
