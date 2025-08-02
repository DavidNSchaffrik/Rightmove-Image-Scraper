from PIL import Image, ImageDraw, ImageFont
import os
import time
import re
import requests
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# -------------------------------
# === HANDLE URL INPUT ===
# -------------------------------
if len(sys.argv) > 1:
    rightmove_url = sys.argv[1]
    print(f"[INFO] Using URL from command line: {rightmove_url}")
else:
    rightmove_url = input("Please enter the url: ")

# -------------------------------
# === FOLDER SETUP ===
# -------------------------------
base_folder = "rightmove_images"
os.makedirs(base_folder, exist_ok=True)

# Create a new numbered subfolder each time
existing_subfolders = [
    d for d in os.listdir(base_folder)
    if os.path.isdir(os.path.join(base_folder, d)) and d.isdigit()
]
if existing_subfolders:
    new_folder_number = max(int(d) for d in existing_subfolders) + 1
else:
    new_folder_number = 1
download_folder = os.path.join(base_folder, str(new_folder_number))
os.makedirs(download_folder, exist_ok=True)
print(f"[INFO] Using download folder: {download_folder}")

# -------------------------------
# === SCRAPING CONFIGURATION ===
# -------------------------------
chrome_driver_path = os.path.join(os.getcwd(), "chromedriver.exe")  # Adjust for your OS if needed

# -------------------------------
# === SETUP SELENIUM & OPEN URL ===
# -------------------------------
options = Options()
# Uncomment the next line to run headless
# options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")

service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

print(f"[INFO] Opening Rightmove URL: {rightmove_url}")
driver.get(rightmove_url)

# --- Click the cookie consent (or similar) button ---
try:
    consent_button_xpath = "/html/body/div[7]/div[2]/div/div/div[2]/div/div/button[2]"
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, consent_button_xpath)))
    driver.find_element(By.XPATH, consent_button_xpath).click()
    print("[INFO] Clicked the consent button.")
except Exception as e:
    print(f"[WARN] Could not click the consent button: {e}")

# --- Click the image to open the gallery ---
try:
    image_click_xpath = "/html/body/div[2]/main/div/article/div/div[1]/div[1]/section/div/a[1]"
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, image_click_xpath)))
    driver.find_element(By.XPATH, image_click_xpath).click()
    print("[INFO] Clicked the image link to open the gallery.")
except Exception as e:
    print(f"[WARN] Could not click the image link: {e}")

# Wait for images to appear on the page
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='media'] img"))
    )
except Exception as e:
    print("[ERROR] Timeout waiting for images to load.")
    driver.quit()
    exit()

# Get the page source and close the browser
html = driver.page_source
driver.quit()
print("[INFO] Page loaded. Parsing HTML...")

# -------------------------------
# === PARSE THE HTML WITH BEAUTIFULSOUP ===
# -------------------------------
soup = BeautifulSoup(html, "html.parser")

# --- Extract Address ---
address_tag = soup.find("h1", {"itemprop": "streetAddress"})
if address_tag:
    address = address_tag.text.strip()
    print(f"[INFO] Address (via itemprop): {address}")
else:
    print("[WARN] Address not found via itemprop, trying XPath fallback...")
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(rightmove_url)
        address_xpath = "/html/body/div[2]/main//h1[@itemprop='streetAddress']"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, address_xpath))
        )
        address_elem = driver.find_element(By.XPATH, address_xpath)
        address = address_elem.text.strip()
        print(f"[INFO] Address (via XPath fallback): {address}")
        driver.quit()
    except Exception as e:
        print(f"[ERROR] Address not found via XPath either. {e}")
        address = "Not found"
        driver.quit()

# --- Extract Price ---
price_tag = soup.find("span", string=re.compile(r"£[\d,]+"))
price = price_tag.text.strip() if price_tag else "Not found"
print(f"[INFO] Price: {price}")

# --- Extract Image URLs ---
media_imgs = soup.select("div[id^='media'] img")
print(f"[DEBUG] Found {len(media_imgs)} <img> tags inside media divs")
img_urls = []
seen_urls = set()

for img in media_imgs:
    src = img.get("src")
    if src and "media.rightmove.co.uk" in src and src not in seen_urls:
        img_urls.append(src)
        seen_urls.add(src)
        print(f"[INFO] Found image: {src}")
    else:
        print(f"[WARN] Skipped invalid or missing image src")

# -------------------------------
# === DOWNLOAD IMAGES ===
# -------------------------------
for idx, url in enumerate(img_urls):
    try:
        print(f"[INFO] Downloading image {idx + 1}: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            file_path = os.path.join(download_folder, f"image_{idx + 1}.jpg")
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"[SUCCESS] Saved to: {file_path}")
        else:
            print(f"[ERROR] Failed to download: {url} (Status code: {response.status_code})")
    except Exception as e:
        print(f"[EXCEPTION] Error downloading {url}: {e}")

# --- Save Address and Price to a file ---
info_file = os.path.join(download_folder, "property_info.txt")
with open(info_file, "w", encoding="utf-8") as f:
    f.write(f"Address: {address}\n")
    f.write(f"Price: {price}\n")
print(f"[DONE] Scraped and saved all data to '{download_folder}' ✅")

# -------------------------------
# === EXTRACT FULL DESCRIPTION ===
# -------------------------------
try:
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(rightmove_url)
    # XPath to the full description as provided
    description_xpath = "/html/body/div[2]/main/div/div[2]/div/article[3]/div[3]/div/div"
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, description_xpath))
    )
    description_elem = driver.find_element(By.XPATH, description_xpath)
    full_description = description_elem.text.strip()
    driver.quit()
    print("[INFO] Full description extracted successfully.")
except Exception as e:
    print(f"[ERROR] Full description not found. {e}")
    full_description = "Not found"

description_file = os.path.join(download_folder, "description.txt")
with open(description_file, "w", encoding="utf-8") as f:
    f.write(full_description)
print(f"[INFO] Full description saved to: {description_file}")

# -------------------------------
# === CREATE COLLAGE WITH PIL ===
# -------------------------------
# Use the first downloaded image for the collage and replace it with the final image
image_path = os.path.join(download_folder, "image_1.jpg")
if not os.path.exists(image_path):
    print(f"[ERROR] Image not found at {image_path}. Cannot create collage.")
    exit()

# Set the output path as the same as image_1.jpg to replace it with the collage
output_path = image_path
font_path = "arial.ttf"  # Update this path if needed

# Load the original image and get its size
img = Image.open(image_path).convert("RGB")
original_width, original_height = img.size

# Define banner height and create a new image with extra space for the banner
banner_height = 350
new_height = original_height + banner_height
new_img = Image.new("RGB", (original_width, new_height), color=(0, 0, 0))
new_img.paste(img, (0, 0))

import textwrap

# --- Draw wrapped text on banner (Pillow 10+ compatible) ---

def _text_wh(draw, text, font):
    # returns (width, height) using textbbox (works in Pillow 10+)
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return r - l, b - t

def _wrap_text_to_width(draw, text, font, max_width):
    if not text:
        return []
    words, lines, line = text.split(), [], ""
    for w in words:
        test = w if not line else f"{line} {w}"
        tw, _ = _text_wh(draw, test, font)
        if tw <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines

def _draw_wrapped_text(draw, text, font, max_width, x, y, line_spacing=10, fill=(255, 255, 255)):
    lines = _wrap_text_to_width(draw, text, font, max_width)
    # stable line height (accounts for ascenders/descenders)
    _, line_h = _text_wh(draw, "Ay", font)
    for i, line in enumerate(lines):
        draw.text((x, y + i * (line_h + line_spacing)), line, font=font, fill=fill)
    return y + len(lines) * (line_h + line_spacing)

# --- draw price and address onto the banner ---

draw = ImageDraw.Draw(new_img)
title_font = ImageFont.truetype(font_path, size=80)
subtitle_font = ImageFont.truetype(font_path, size=50)

padding = 40
text_y = original_height + padding
max_text_width = original_width - 2 * padding
line_spacing = 10

# price (wrapped)
text_y = _draw_wrapped_text(draw, price, title_font, max_text_width, padding, text_y, line_spacing)

# small gap between price and address
text_y += 10

# address (wrapped)
_draw_wrapped_text(draw, address, subtitle_font, max_text_width, padding, text_y, line_spacing)

# Adding Icons

from PIL import Image, ImageDraw, ImageFont, ImageOps

# ---------- LOAD BASE ----------
image_path = os.path.join(download_folder, "image_1.jpg")
if not os.path.exists(image_path):
    print(f"[ERROR] Image not found at {image_path}. Cannot create collage.")
    exit()

img = Image.open(image_path).convert("RGB")
original_width, original_height = img.size

font_path = "arial.ttf"  # adjust if needed
title_font = ImageFont.truetype(font_path, size=80)
subtitle_font = ImageFont.truetype(font_path, size=50)
value_font = ImageFont.truetype(font_path, size=40)

padding = 40
line_spacing = 10
gap_price_address = 10
gap_text_icons = 30
gap_icon_value = 6
spacing_x = 70  # gap between icon clusters

# ---------- TEXT WRAP HELPERS ----------
def text_wh(draw, text, font):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return r - l, b - t

def wrap_text_to_width(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = w if not cur else f"{cur} {w}"
        wpx, _ = text_wh(draw, test, font)
        if wpx <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

# ---------- MEASURE EVERYTHING FIRST ----------
measure = Image.new("RGB", (original_width, 10), "black")
m_draw = ImageDraw.Draw(measure)
max_text_w = original_width - 2 * padding

price_lines = wrap_text_to_width(m_draw, price, title_font, max_text_w)
addr_lines  = wrap_text_to_width(m_draw, address, subtitle_font, max_text_w)

_, title_h = text_wh(m_draw, "Ay", title_font)
_, sub_h   = text_wh(m_draw, "Ay", subtitle_font)
_, val_h   = text_wh(m_draw, "9999", value_font)

text_block_h = (
    len(price_lines) * (title_h + line_spacing) +
    gap_price_address +
    len(addr_lines)  * (sub_h + line_spacing)
)

# ---------- ICONS (PNG) ----------
icon_paths = [
    "icons/house.png",      # house type
    "icons/bed.png",        # bedrooms
    "icons/bathroom.png",   # bathrooms
    "icons/floorplan.png"   # square feet
]
value_texts = ["Freehold", "2", "2", "9999sqft"]

# slightly smaller icons
target_icon_h = 64  # was 96
side_padding = 40   # left/right padding for the row
gap_icon_value = 8  # icon -> value
# no spacing_x needed—using equal columns

icons = []
for pth in icon_paths:
    ico = Image.open(pth).convert("RGBA")
    # don't upscale -> avoids blur
    t_h = min(target_icon_h, ico.height)
    ico = ImageOps.contain(ico, (10_000, t_h), method=Image.LANCZOS)
    icons.append(ico)

# row height for banner sizing
icons_row_h = max(i.size[1] for i in icons) + gap_icon_value + val_h

# ---------- COMPUTE BANNER HEIGHT DYNAMICALLY ----------
banner_height = (
    padding +
    text_block_h +
    gap_text_icons +
    icons_row_h +
    padding
)

new_height = original_height + banner_height
new_img = Image.new("RGB", (original_width, new_height), color=(0, 0, 0))
new_img.paste(img, (0, 0))
draw = ImageDraw.Draw(new_img)

# ---------- DRAW TEXT ----------
y = original_height + padding
for line in price_lines:
    draw.text((padding, y), line, font=title_font, fill=(255, 255, 255))
    y += title_h + line_spacing

y += gap_price_address
for line in addr_lines:
    draw.text((padding, y), line, font=subtitle_font, fill=(255, 255, 255))
    y += sub_h + line_spacing

# ---------- DRAW ICONS (EQUAL COLUMNS) + VALUES UNDER ----------
y += gap_text_icons
row_y = int(y)

n = len(icons)
inner_w = original_width - 2 * side_padding
col_w = inner_w / n  # may be float; we center per-column

for i, (ico, val) in enumerate(zip(icons, value_texts)):
    # column center
    center_x = int(side_padding + (i + 0.5) * col_w)

    # icon centered in its column
    icon_x = int(center_x - ico.width // 2)
    icon_y = int(row_y)
    new_img.paste(ico, (icon_x, icon_y), ico)

    # value centered under icon
    val_w, val_hh = text_wh(draw, val, value_font)
    val_x = int(center_x - val_w // 2)
    val_y = int(icon_y + ico.height + gap_icon_value)
    draw.text((val_x, val_y), val, font=value_font, fill=(255, 255, 255))


# ---------- SAVE ----------
output_path = image_path  # overwrite image_1.jpg
new_img.save(output_path)
print(f"[SUCCESS] Collage created and saved at: {output_path}")


