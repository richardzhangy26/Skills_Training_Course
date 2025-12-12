#!/usr/bin/env python3
"""
Split the queue diagram SVG into 5 separate SVG files.
"""
import xml.etree.ElementTree as ET
import os

# Input and output paths
input_file = '/Users/richardzhang/工作/能力训练/skills_training_course/天津科技大学-数据结构与算法/queue_diagram.svg'
output_dir = '/Users/richardzhang/工作/能力训练/scenes'

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Parse the SVG
tree = ET.parse(input_file)
root = tree.getroot()

# Define the namespaces
namespaces = {
    'svg': 'http://www.w3.org/2000/svg'
}

# Extract each scene
for i in range(1, 6):
    scene_id = f'diagram{i}'
    scene = root.find(f".//svg:g[@id='{scene_id}']", namespaces)

    if scene is not None:
        # Get the bounding box of the scene
        # The scenes are at different Y positions:
        # diagram1: y=100, height=220 -> viewBox: 0 100 1200 320
        # diagram2: y=350, height=220 -> viewBox: 0 350 1200 420
        # diagram3: y=600, height=280 -> viewBox: 0 600 1200 880
        # diagram4: y=910, height=280 -> viewBox: 0 910 1200 1190
        # diagram5: y=1220, height=330 -> viewBox: 0 1220 1200 1550

        scene_bounds = {
            1: {'x': 0, 'y': 100, 'width': 1200, 'height': 320},
            2: {'x': 0, 'y': 350, 'width': 1200, 'height': 420},
            3: {'x': 0, 'y': 600, 'width': 1200, 'height': 880},
            4: {'x': 0, 'y': 910, 'width': 1200, 'height': 1190},
            5: {'x': 0, 'y': 1220, 'width': 1200, 'height': 1550}
        }

        bounds = scene_bounds[i]

        # Create a new SVG for this scene
        new_svg = ET.Element('svg')
        new_svg.set('viewBox', f"{bounds['x']} {bounds['y']} {bounds['width']} {bounds['height']}")
        new_svg.set('xmlns', 'http://www.w3.org/2000/svg')

        # Copy the scene content
        scene_copy = ET.SubElement(new_svg, 'g')
        for child in scene:
            scene_copy.append(child)

        # Convert to string
        svg_str = ET.tostring(new_svg, encoding='unicode')

        # Save SVG file
        svg_path = os.path.join(output_dir, f'scene_{i}.svg')
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_str)

        print(f"✓ Scene {i} -> {svg_path}")

        # Calculate PNG dimensions (using the same width and height)
        png_width = 1200
        png_height = bounds['height']
        png_width_px = int(png_width * 0.75)  # Scale down a bit
        png_height_px = int(png_height * 0.75)

        # Create HTML wrapper for the SVG to convert to PNG
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Scene {i}</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: white;
        }}
        svg {{
            width: {png_width_px}px;
            height: {png_height_px}px;
        }}
    </style>
</head>
<body>
{svg_str}
</body>
</html>
        """

        html_path = os.path.join(output_dir, f'scene_{i}.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"  -> HTML wrapper: {html_path}")
    else:
        print(f"✗ Scene {i} not found!")

print(f"\nAll scenes saved to: {output_dir}")
print("\nTo convert to PNG:")
print("Option 1: Open each HTML file in a browser and take screenshots")
print("Option 2: Use an online SVG to PNG converter")
print("Option 3: Install Inkscape and run: inkscape scene_*.svg --export-type=png")
