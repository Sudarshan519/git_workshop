from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.units import inch
from PIL import Image, ImageFilter
import io

# Import Paragraph and getSampleStyleSheet from platypus
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# Define your CUSTOM PAGE DIMENSIONS for a wider, shorter rectangle
CUSTOM_PAGE_WIDTH = 8 * inch  # Wider
CUSTOM_PAGE_HEIGHT = 5 * inch # Shorter

# Assign your custom dimensions to PAGE_WIDTH and PAGE_HEIGHT
PAGE_WIDTH, PAGE_HEIGHT = CUSTOM_PAGE_WIDTH, CUSTOM_PAGE_HEIGHT

def draw_background(c, img_data):
    # Draw background full page image from image data (BytesIO object)
    bg = ImageReader(img_data)
    # Ensure the background scales to the custom page size
    c.drawImage(bg, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)

def draw_centered_image(c, img_path, center_x, center_y, width, height):
    img = ImageReader(img_path)
    c.drawImage(img, center_x - width/2, center_y - height/2, width=width, height=height, mask='auto')

def draw_centered_text(c, text, x_center, y, font_name, font_size, color=colors.white):
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    text_width = c.stringWidth(text, font_name, font_size)
    c.drawString(x_center - text_width/2, y, text)

def create_speaker_kit_cover(
    pdf_path,
    bg_image_path,
    headshot_path,
    speaker_name,
    tagline,
    tags,
    discover_text="Discover Solutions",
    blur_radius=10,
    about_text="",
    career_highlights=[]
):
    c = canvas.Canvas(pdf_path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    # --- Helper function to process and draw background ---
    def process_and_draw_background(canvas_obj, image_path, blur_rad):
        try:
            img = Image.open(image_path)
            blurred_img = img.filter(ImageFilter.GaussianBlur(radius=blur_rad))
            img_byte_arr = io.BytesIO()
            output_format = img.format if img.format in ['JPEG', 'PNG'] else 'PNG'
            blurred_img.save(img_byte_arr, format=output_format)
            img_byte_arr.seek(0)
            draw_background(canvas_obj, img_byte_arr)
        except FileNotFoundError:
            print(f"Error: Background image not found at {image_path}. Drawing solid background.")
            canvas_obj.setFillColor(colors.black)
            canvas_obj.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1)
        except Exception as e:
            print(f"An error occurred while blurring or drawing background: {e}. Drawing solid background.")
            canvas_obj.setFillColor(colors.black)
            canvas_obj.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1)


    # --- Page 1: Cover Page ---
    process_and_draw_background(c, bg_image_path, blur_radius)

    headshot_width = 1.5 * inch
    headshot_height = 1.5 * inch
    headshot_x = PAGE_WIDTH / 2
    headshot_y = PAGE_HEIGHT * 0.7
    draw_centered_image(c, headshot_path, headshot_x, headshot_y, headshot_width, headshot_height)

    draw_centered_text(c, speaker_name, PAGE_WIDTH / 2, PAGE_HEIGHT * 0.48, "Helvetica-Bold", 20)
    draw_centered_text(c, tagline, PAGE_WIDTH / 2, PAGE_HEIGHT * 0.40, "Helvetica", 12)
    tags_text = " | ".join(tags)
    draw_centered_text(c, tags_text, PAGE_WIDTH / 2, PAGE_HEIGHT * 0.33, "Helvetica-Oblique", 10, colors.lightgrey)

    box_width = 320
    box_height = 50
    box_x = (PAGE_WIDTH - box_width) / 2
    box_y = PAGE_HEIGHT * 0.1

    c.setFillColor(colors.Color(0, 0, 0, alpha=0.4))
    c.roundRect(box_x + 3, box_y - 3, box_width, box_height, 8, fill=1, stroke=0)
    c.setStrokeColor(colors.whitesmoke)
    c.setFillColor(colors.HexColor("#03396c"))
    c.roundRect(box_x, box_y, box_width, box_height, 8, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.whitesmoke)
    text_y_in_box = box_y + box_height / 2 - (c.stringWidth(discover_text, "Helvetica-Bold", 18) / 12)
    c.drawCentredString(PAGE_WIDTH / 2, text_y_in_box, discover_text)

    c.showPage()

    # --- Page 2: About and Career Highlights ---
    process_and_draw_background(c, bg_image_path, blur_radius)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT * 0.85, "About " + speaker_name)

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontSize = 10
    styleN.leading = 12
    styleN.textColor = colors.white
    styleN.alignment = TA_CENTER

    p = Paragraph(about_text, styleN)

    about_text_frame_width = PAGE_WIDTH * 0.8
    about_text_x_pos = (PAGE_WIDTH - about_text_frame_width) / 2
    text_width_calc, text_height_calc = p.wrapOn(c, about_text_frame_width, PAGE_HEIGHT)
    about_text_y_pos = PAGE_HEIGHT * 0.78 - text_height_calc

    c.saveState()
    p.drawOn(c, about_text_x_pos, about_text_y_pos)
    c.restoreState()


    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT * 0.45, "Career Highlights")

    num_highlights = len(career_highlights)
    half_index = (num_highlights + 1) // 2
    highlights_col1 = career_highlights[:half_index]
    highlights_col2 = career_highlights[half_index:]

    # Define column properties
    column_area_width = PAGE_WIDTH * 0.85 # Slightly wider total area for highlights
    individual_col_width = (column_area_width / 2) # Width for each text column
    spacing_between_columns = PAGE_WIDTH * 0.05 # Increased space between columns
    bullet_indent = 0.15 * inch
    text_indent_after_bullet = 0.3 * inch

    col1_x_start = PAGE_WIDTH * 0.075 # Start of the first column area (more left padding)
    col2_x_start = col1_x_start + individual_col_width + spacing_between_columns

    initial_list_y = PAGE_HEIGHT * 0.38
    bullet_font_size = 9
    # *** Increased leading significantly for better spacing within wrapped text ***
    line_spacing = bullet_font_size + 5 # More vertical space per line (e.g., 9+5=14 points leading)
    buffer_between_items = 0.15 * inch # *** Increased buffer space between different highlight items ***

    highlight_style = ParagraphStyle(
        name='HighlightStyle',
        fontName='Helvetica',
        fontSize=bullet_font_size,
        leading=line_spacing, # Applied here
        textColor=colors.white,
        alignment=TA_LEFT
    )

    c.setFillColor(colors.white)
    c.setFont("Helvetica", bullet_font_size)


    # --- Draw Column 1 ---
    current_y_col1 = initial_list_y
    for highlight in highlights_col1:
        p_highlight = Paragraph(highlight, highlight_style)
        # Use available width after bullet indent
        text_width_wrapped, text_height_wrapped = p_highlight.wrapOn(c, individual_col_width - text_indent_after_bullet, PAGE_HEIGHT)

        # Check if drawing this item will go off the page
        if (current_y_col1 - text_height_wrapped) < PAGE_HEIGHT * 0.05:
            print(f"Warning: Column 1 highlight '{highlight[:30]}...' truncated due to page limit.")
            break

        # Calculate Y for the bottom of the paragraph
        paragraph_bottom_y = current_y_col1 - text_height_wrapped
        # Calculate Y for the bullet's baseline, aligning it with the first line of text
        # This aligns the bullet with the 'top' of the Paragraph's content area
        bullet_y = current_y_col1 - highlight_style.leading + (highlight_style.leading - highlight_style.fontSize) / 2


        c.drawString(col1_x_start + bullet_indent, bullet_y, "•")
        p_highlight.drawOn(c, col1_x_start + text_indent_after_bullet, paragraph_bottom_y)

        # Advance Y for the next highlight item
        current_y_col1 -= (text_height_wrapped + buffer_between_items)


    # --- Draw Column 2 ---
    current_y_col2 = initial_list_y
    for highlight in highlights_col2:
        p_highlight = Paragraph(highlight, highlight_style)
        text_width_wrapped, text_height_wrapped = p_highlight.wrapOn(c, individual_col_width - text_indent_after_bullet, PAGE_HEIGHT)

        if (current_y_col2 - text_height_wrapped) < PAGE_HEIGHT * 0.05:
            print(f"Warning: Column 2 highlight '{highlight[:30]}...' truncated due to page limit.")
            break

        paragraph_bottom_y = current_y_col2 - text_height_wrapped
        bullet_y = current_y_col2 - highlight_style.leading + (highlight_style.leading - highlight_style.fontSize) / 2

        c.drawString(col2_x_start + bullet_indent, bullet_y, "•")
        p_highlight.drawOn(c, col2_x_start + text_indent_after_bullet, paragraph_bottom_y)

        current_y_col2 -= (text_height_wrapped + buffer_between_items)


    c.save()


# Usage example with longer text for testing
create_speaker_kit_cover(
    pdf_path="Speaker_Kit_Cover_Two_Pages_Two_Col_Highlights_Final_NoOverlap.pdf",
    bg_image_path="publicspeakerhero.jpeg",
    headshot_path="Realtor-Headshots-2.webp",
    speaker_name="Jordan Smith",
    tagline="Keynote Speaker | Leadership Strategist | Author",
    tags=["Developer", "AI Alchemist", "Innovator"],
    blur_radius=15,
    about_text=(
        "Jordan Smith is a visionary leader and acclaimed author, renowned for his "
        "transformative insights into modern leadership and technological innovation. "
        "With over two decades of experience, Jordan empowers organizations and individuals "
        "to navigate complex challenges and unlock their full potential in the digital age. "
        "His expertise spans artificial intelligence, strategic planning, and fostering resilient team dynamics in fast-paced environments."
    ),
    career_highlights=[
        "Authored best-selling book 'The AI Alchemist: ' ",
        "Keynote speaker at over 100 international conferences on AI and leadership,",
        "Led a groundbreaking initiative that resulted in a 30% efficiency ",
        "Recognized as 'Top Innovator in Tech' by TechForward Magazine (2023)  ",
        "Founded a highly successful startup focused on ethical AI solutions,  ",
        "Delivered a highly-rated TEDx talk on 'The Future of Human-AI Collaboration' to a global audience, .",
        # "Served as a lead consultant for multiple Fortune 100 companies on comprehensive digital transformation strategies, enhancing their competitive edge and fostering a culture of innovation.",
        # "Received a prestigious innovation award for developing a novel framework in agile project management, significantly enhancing team productivity and accelerating project delivery rates for complex undertakings.",
        # "Mentored over 50 aspiring tech entrepreneurs, guiding them from initial ideation through product development to successful venture launches, contributing significantly to the startup ecosystem.",
        # "Developed and implemented AI-powered predictive analytics systems for supply chain optimization, reducing lead times by 20% and improving inventory management accuracy.",
        # "Implemented a company-wide upskilling program in AI and machine learning, boosting employee technical proficiency by over 40% and fostering internal innovation."
    ]
)