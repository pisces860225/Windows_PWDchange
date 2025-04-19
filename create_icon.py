from PIL import ImageFont


def create_icon():
    """創建一個簡單的應用程式圖標"""
    try:
        # 嘗試導入PIL
        from PIL import Image, ImageDraw
    except ImportError:
        print("未安裝PIL庫，無法創建圖標。請使用 'pip install pillow' 安裝。")
        return

    # 設置圖標尺寸和背景色
    size = (256, 256)
    background_color = (0, 123, 255)  # 藍色

    # 創建一個新圖像
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 繪製圓形背景
    circle_radius = size[0] // 2 - 5
    circle_center = (size[0] // 2, size[1] // 2)
    draw.ellipse(
        (
            circle_center[0] - circle_radius,
            circle_center[1] - circle_radius,
            circle_center[0] + circle_radius,
            circle_center[1] + circle_radius,
        ),
        fill=background_color,
    )

    # 繪製鎖形符號
    try:
        # 嘗試創建一個文字"🔒"作為鎖的符號
        font_size = int(circle_radius * 1.2)
        try:
            font = ImageFont.truetype("Arial", font_size)
        except IOError:
            # 如果無法找到Arial字體，使用默認字體
            font = ImageFont.load_default()

        text = "🔒"
        text_size = draw.textbbox((0, 0), text, font=font)
        text_width = text_size[2] - text_size[0]
        text_height = text_size[3] - text_size[1]

        draw.text(
            (
                circle_center[0] - text_width // 2,
                circle_center[1] - text_height // 2 - 10,
            ),
            text,
            fill="white",
            font=font,
        )
    except Exception as e:
        print(f"無法繪製文字: {e}")
        # 後備方案：繪製一個鎖形
        lock_width = circle_radius * 0.6
        lock_height = circle_radius * 0.8
        lock_top = circle_center[1] - lock_height // 2
        lock_left = circle_center[0] - lock_width // 2

        # 繪製鎖的主體
        draw.rectangle(
            (
                lock_left,
                lock_top + lock_height * 0.3,
                lock_left + lock_width,
                lock_top + lock_height,
            ),
            fill="white",
        )

        # 繪製鎖的環
        arc_radius = lock_width * 0.4
        draw.arc(
            (
                circle_center[0] - arc_radius,
                lock_top - arc_radius * 0.5,
                circle_center[0] + arc_radius,
                lock_top + arc_radius * 1.5,
            ),
            180,
            0,
            fill="white",
            width=int(lock_width * 0.2),
        )

    # 保存為ICO文件
    output_path = "favicon.ico"
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(output_path, format="ICO", sizes=sizes)

    print(f"圖標已創建: {output_path}")


if __name__ == "__main__":
    create_icon()
