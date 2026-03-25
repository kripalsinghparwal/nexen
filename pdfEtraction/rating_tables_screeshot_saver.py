########################### Code to Screeshot tables fully and only rating tables in separate folder ###############
import pdfplumber
from pdf2image import convert_from_path
import cv2
import numpy as np
import os

# First stage: Save full screenshots below tables
def save_full_screenshots():
    pdf_path = "filtered_pages_with_ratings.pdf"
    output_dir_full = "screenshots_bottom_blocks"
    os.makedirs(output_dir_full, exist_ok=True)

    DPI = 300
    PDF_DPI = 72
    SCALE = DPI / PDF_DPI

    images = convert_from_path(pdf_path, dpi=DPI)

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.find_tables()
            page_heading = page.extract_text_lines()[0]['text'].strip().replace(" ", "_")
            
            for i, table in enumerate(tables):
                header = table.extract()[0]

                if any("Composition by Ratings" in h for h in header if h):
                    continue

                if any("Ratings" in h for h in header if h):
                    x0, top, x1, bottom = table.bbox
                    image = np.array(images[page_num])
                    h, w, _ = image.shape

                    padding = 20
                    x0_img = max(0, int(x0 * SCALE) - padding)
                    x1_img = min(w, int(x1 * SCALE) + padding)
                    top_img = int(bottom * SCALE) - 10
                    bottom_img = int(page.height * SCALE)

                    x0_img = max(0, min(x0_img, w))
                    x1_img = max(0, min(x1_img, w))
                    top_img = max(0, min(top_img, h))
                    bottom_img = max(0, min(bottom_img, h))

                    crop = image[top_img:bottom_img, x0_img:x1_img]
                    # filename = f"{output_dir_full}/page_{page_num+1}_table_{i+1}_below.png"
                    filename = f"{output_dir_full}/{page_heading}_page_{page_num+1}_table_{i+1}_below.png"
                    cv2.imwrite(filename, cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))
                    print(f"✅ Full screenshot saved: {filename}")

# Second stage: Process saved screenshots to crop at rectangles
def detect_topmost_deep_blue_rectangle(image_path):
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error loading image: {image_path}")
        return None

    # Convert to HSV color space for better color segmentation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Define deeper blue color range in HSV
    lower_blue = np.array([100, 150, 100])  # Hue, Saturation, Value
    upper_blue = np.array([140, 255, 255])
    
    # Create mask for deep blue regions
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Morphological operations to clean up the mask
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter and collect valid rectangles
    valid_rectangles = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 2000:  # Minimum area threshold
            continue
            
        x, y, w, h = cv2.boundingRect(cnt)
        if h > 30:
            aspect_ratio = w / float(h)
            
            # Look for wide rectangles
            # if 3.0 < aspect_ratio < 15.0:
            if aspect_ratio:
                valid_rectangles.append({
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h,
                    'area': area
                })
    
    if valid_rectangles:
        # Sort by vertical position first (y), then horizontal (x)
        valid_rectangles.sort(key=lambda r: (r['y'], r['x']))
        
        # Select the topmost rectangle
        top_rect = valid_rectangles[0]
        
        # Extract and return rectangle
        return {
            'rectangle': image[top_rect['y']:top_rect['y']+top_rect['h'], 
                         top_rect['x']:top_rect['x']+top_rect['w']],
            'coordinates': (top_rect['x'], top_rect['y'], top_rect['w'], top_rect['h']),
            'mask': mask
        }
    
    return None


def crop_at_rectangles():
    input_dir = "screenshots_bottom_blocks"
    output_dir_cropped = "screenshots_cropped_at_rectangles"
    os.makedirs(output_dir_cropped, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith(".png"):
            img_path = os.path.join(input_dir, filename)
            
            # Use your improved detection function
            result = detect_topmost_deep_blue_rectangle(img_path)
            
            if result:
                x, y, w, h = result['coordinates']
                image = cv2.imread(img_path)
                
                # Crop from top of image to top of detected rectangle
                cropped_img = image[:y, :]
                
                # Save with original filename (not prefixed with 'cropped_')
                output_path = os.path.join(output_dir_cropped, filename)
                cv2.imwrite(output_path, cropped_img)
                print(f"✅ Cropped at y={y}px: {output_path}")
                
                # Optional: Save debug images
                debug_dir = os.path.join(output_dir_cropped, "debug")
                os.makedirs(debug_dir, exist_ok=True)
                cv2.imwrite(os.path.join(debug_dir, f"mask_{filename}"), result['mask'])
            else:
                print(f"⚠️ No rectangle found in {filename} - saving original")
                # Copy original image if no rectangle detected
                original = cv2.imread(img_path)
                output_path = os.path.join(output_dir_cropped, filename)
                cv2.imwrite(output_path, original)

# Run both stages
save_full_screenshots()
crop_at_rectangles()

print("Processing complete!")
print(f"Full screenshots saved to: screenshots_bottom_blocks")
print(f"Cropped screenshots saved to: screenshots_cropped_at_rectangles")