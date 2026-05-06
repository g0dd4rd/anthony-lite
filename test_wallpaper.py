#!/usr/bin/env python3
"""
Test wallpaper functionality
"""

import sys
import os
sys.path.insert(0, '/home/jprajzne/anthony')

from mcp_client import MCPClient


def test_wallpaper():
    """Test set_wallpaper function"""
    print("=" * 60)
    print("WALLPAPER TEST")
    print("=" * 60)

    client = MCPClient("gnome-desktop-mcp")

    # Find a test image
    # Common locations for wallpapers
    test_images = [
        "/usr/share/backgrounds/gnome/adwaita-l.jxl",
        "/usr/share/backgrounds/gnome/adwaita-l.webp",
        "/usr/share/backgrounds/gnome/adwaita-d.jxl",
        "~/Pictures",  # Check if user has images
        "/usr/share/pixmaps/fedora-logo.png",
    ]

    # Find first available image
    test_image = None
    for img_path in test_images:
        expanded = os.path.expanduser(img_path)
        if os.path.exists(expanded):
            if os.path.isfile(expanded):
                test_image = expanded
                break
            elif os.path.isdir(expanded):
                # Look for first image in directory
                for f in os.listdir(expanded):
                    full_path = os.path.join(expanded, f)
                    if os.path.isfile(full_path) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.svg')):
                        test_image = full_path
                        break
                if test_image:
                    break

    if not test_image:
        print("❌ No test image found. Create a test image:")
        print("   mkdir -p ~/Pictures")
        print("   wget -O ~/Pictures/test_wallpaper.jpg https://picsum.photos/1920/1080")
        return

    print(f"\n[1] Testing set_wallpaper with: {test_image}")
    try:
        result = client.call_tool("set_wallpaper", {"image_path": test_image})
        print(f"    Result: {result}")

        # Verify wallpaper was set
        print("\n[2] Verifying wallpaper setting...")
        import subprocess
        current = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.background", "picture-uri"],
            capture_output=True,
            text=True
        ).stdout.strip()
        print(f"    Current wallpaper URI: {current}")

    except Exception as e:
        print(f"    Error: {e}")

    # Test with tilde path
    if test_image.startswith(os.path.expanduser("~")):
        tilde_path = "~" + test_image[len(os.path.expanduser("~")):]
        print(f"\n[3] Testing with tilde path: {tilde_path}")
        try:
            result = client.call_tool("set_wallpaper", {"image_path": tilde_path})
            print(f"    Result: {result}")
        except Exception as e:
            print(f"    Error: {e}")

    # Test error handling - non-existent file
    print(f"\n[4] Testing error handling (non-existent file)...")
    try:
        result = client.call_tool("set_wallpaper", {"image_path": "/tmp/nonexistent.jpg"})
        print(f"    Result: {result}")
    except Exception as e:
        print(f"    Expected error: {e}")

    # Test error handling - invalid format
    print(f"\n[5] Testing error handling (invalid format)...")
    try:
        result = client.call_tool("set_wallpaper", {"image_path": "/etc/hostname"})
        print(f"    Result: {result}")
    except Exception as e:
        print(f"    Expected error: {e}")

    print("\n" + "=" * 60)
    print("✅ Wallpaper tests completed!")
    print("   Check your desktop - wallpaper should have changed.")
    print("=" * 60)


if __name__ == "__main__":
    test_wallpaper()
