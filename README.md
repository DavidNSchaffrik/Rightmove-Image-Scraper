# Rightmove Image Scraper — Collage Generator

Generate a share-ready image from a Rightmove property page:

* downloads the listing’s images
* extracts **price, address, full description**
* creates a final image with a **black banner** containing wrapped price/address text
* shows **four centered icons** with values (Type, Bedrooms, Bathrooms, Size)

---

## Features

* ✅ Selenium scrape of page HTML (handles cookie consent)
* ✅ BeautifulSoup parsing for price & address; Selenium XPaths for stats
* ✅ Pixel-accurate **text wrapping** (Pillow 10+ safe; uses `textbbox`)
* ✅ **Dynamic banner height** so nothing overflows
* ✅ Four **equally spaced** icon “columns,” centered regardless of value length
* ✅ Saves:

  * `rightmove_images/<n>/image_1.jpg` (**final collage**, overwrites first image)
  * other downloaded photos: `image_2.jpg`, …
  * `property_info.txt` (Address, Price)
  * `description.txt` (Full description)

---

## Requirements

* **Python** 3.9–3.12

* **Google Chrome** (stable)

* **ChromeDriver** matching your Chrome version

* **Pip packages**

  ```bash
  pip install pillow==10.* selenium beautifulsoup4 requests lxml
  ```

  > Pillow ≥10 is supported (no deprecated `textsize` calls).

* **Icons (PNG)** — place in `icons/`:

  ```
  icons/
    house.png      # house type (e.g., “Freehold”, “Terraced”)
    bed.png        # bedrooms
    bathroom.png   # bathrooms
    floorplan.png  # size (e.g., “3,968 sq ft”)
  ```

> **Note:** SVG icons aren’t used directly to avoid native dependencies. Convert to PNG once if needed.

---

## Quick Start

1. Put `chromedriver.exe` in the project root (or update the path in the script).
2. Ensure the `icons/` folder contains the 4 PNGs above.
3. Run:

   ```bash
   python script.py "https://www.rightmove.co.uk/properties/XXXXXXXX"
   ```

   Or run without an argument and paste the URL at the prompt.

The script creates a new numbered folder in `rightmove_images/` for each run and saves outputs there.

---

## Configuration

In the script, look for these variables:

* **Driver path**

  ```python
  chrome_driver_path = os.path.join(os.getcwd(), "chromedriver.exe")
  ```
* **Fonts**

  ```python
  font_path = "arial.ttf"  # replace with a font file present on your system
  title_font    = ImageFont.truetype(font_path, size=80)  # price
  subtitle_font = ImageFont.truetype(font_path, size=50)  # address
  value_font    = ImageFont.truetype(font_path, size=40)  # icon values
  ```
* **Banner layout**

  ```python
  padding = 40
  gap_price_address = 10
  gap_text_icons = 30
  gap_icon_value = 8
  ```
* **Icon sizing & spacing (equal columns)**

  ```python
  target_icon_h = 84     # max icon height on banner (no upscaling beyond source)
  side_padding  = 40     # left/right padding for the icon row
  ```

---

## What Gets Scraped

* **Address**: via BeautifulSoup (`<h1 itemprop="streetAddress">` fallback via XPath)
* **Price**: first `£…` pattern on the page
* **Description**: XPath to the listing description block
* **Stats** (Selenium + explicit XPaths you supplied):

  * House Type: `/html/body/div[2]/main/div/div[2]/div/article[2]/dl/div[1]/dd/span/p`
  * Bedrooms:   `/html/body/div[2]/main/div/div[2]/div/article[2]/dl/div[2]/dd/span/p`
  * Bathrooms:  `/html/body/div[2]/main/div/div[2]/div/article[2]/dl/div[3]/dd/span/p`
  * Size (sq ft): `/html/body/div[2]/main/div/div[2]/div/article[2]/dl/div[4]/dd/span/p[1]`

The script logs each step, e.g.:

```
[INFO] Extracting property stats (type / beds / baths / size)...
[INFO] House type: Freehold
[INFO] Bedrooms: 5
[INFO] Bathrooms: 4
[INFO] Size (sqft): 3,968 sq ft
```

> Numbers are lightly normalized (e.g., “5 bedrooms” → “5”). Non-numeric type strings (e.g., “Freehold”) are kept as-is.

---

## Output Example

```
rightmove_images/
  31/
    image_1.jpg           # final collage (banner with wrapped text + icons row)
    image_2.jpg
    image_3.jpg
    property_info.txt     # Address + Price
    description.txt       # Full description text
```

---

## Troubleshooting

* **`PIL.UnidentifiedImageError` for icons**
  Ensure icons are **PNG** files and paths are correct. SVGs require rasterization first.
* **Icons look blurry**
  The script **won’t upscale** beyond the PNG’s native height. Use source icons ≥ `target_icon_h` (e.g., ≥ 168 px for 84 px target).
* **Text overflows or is cut off**
  The banner height is computed dynamically from wrapped text & icon row. If still tight, increase `padding`, decrease font sizes, or increase `gap_*`.
* **Cookie/consent popups**
  The script best-effort clicks the consent button; site changes may require updating the XPath.
* **`arial.ttf` not found**
  Replace `font_path` with a font file that exists on your machine (e.g., a local `.ttf` in the repo).

---

## Notes & Ethics

* Respect **Rightmove’s Terms of Use** and robots rules. Use this for personal, non-commercial purposes, and rate-limit if you automate multiple pages.
* XPaths can be fragile; consider adding CSS-selector fallbacks if the site updates.

---

## License

Add your preferred license (e.g., MIT) here.

---

## Roadmap (optional)

* Auto-font scaling for extremely long addresses
* Multiple layout themes (light/dark; top/bottom banner)
* Automatic ChromeDriver management (`webdriver_manager`)
* PNG export sizes optimized for TikTok/Instagram reels

---

If you want, I can generate a Markdown `README.md` file for you and tailor the examples to your GitHub project name.
