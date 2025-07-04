from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.units import inch
from PIL import Image, ImageFilter
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import io

# Custom page size
PAGE_WIDTH, PAGE_HEIGHT = 8 * inch, 6 * inch

def draw_background(c, img_data):
    bg = ImageReader(img_data)
    c.drawImage(bg, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)

def draw_centered_image(c, img_path, center_x, center_y, width, height):
    img = ImageReader(img_path)
    c.drawImage(img, center_x - width/2, center_y - height/2, width=width, height=height, mask='auto')

def draw_centered_text(c, text, x_center, y, font_name, font_size, color=colors.white):
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    text_width = c.stringWidth(text, font_name, font_size)
    c.drawString(x_center - text_width/2, y, text)

def process_and_draw_background(canvas_obj, image_path, blur_rad):
    try:
        img = Image.open(image_path)
        blurred_img = img.filter(ImageFilter.GaussianBlur(radius=blur_rad))
        img_byte_arr = io.BytesIO()
        output_format = img.format if img.format in ['JPEG', 'PNG'] else 'PNG'
        blurred_img.save(img_byte_arr, format=output_format)
        img_byte_arr.seek(0)
        draw_background(canvas_obj, img_byte_arr)
    except Exception:
        canvas_obj.setFillColor(colors.black)
        canvas_obj.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1)

def create_speaker_kit_cover(pdf_path, bg_image_path, headshot_path, speaker_name, tagline, tags,
                             discover_text="Discover Solutions", blur_radius=10, about_text="", career_highlights=[]):
    c = canvas.Canvas(pdf_path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    # Cover Page
    process_and_draw_background(c, bg_image_path, blur_radius)
    headshot_width = 1.5 * inch
    headshot_height = 1.5 * inch
    draw_centered_image(c, headshot_path, PAGE_WIDTH / 2, PAGE_HEIGHT * 0.7, headshot_width, headshot_height)

    draw_centered_text(c, speaker_name, PAGE_WIDTH / 2, PAGE_HEIGHT * 0.48, "Helvetica-Bold", 20)
    draw_centered_text(c, tagline, PAGE_WIDTH / 2, PAGE_HEIGHT * 0.40, "Helvetica", 12)
    draw_centered_text(c, (tags), PAGE_WIDTH / 2, PAGE_HEIGHT * 0.33, "Helvetica-Oblique", 10, colors.lightgrey) #" | ".join

    # Discover Box
    box_width, box_height = 300, 30
    box_x = (PAGE_WIDTH - box_width) / 2
    box_y = PAGE_HEIGHT * 0.1

    c.setFillColor(colors.Color(0, 0, 0, alpha=0.4))
    c.roundRect(box_x + 3, box_y + 27, box_width, box_height, 8, fill=1, stroke=0)

    c.setStrokeColor(colors.whitesmoke)
    c.setFillColor(colors.HexColor("#03396c"))
    c.roundRect(box_x, box_y + 30, box_width, box_height, 8, fill=1, stroke=1)

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.whitesmoke)
    c.drawCentredString(PAGE_WIDTH / 2, box_y + 30  + box_height / 2 - 6, discover_text)

    c.showPage()

    # About Page
    about_text_x = PAGE_WIDTH * 0.07
    about_text_y = PAGE_HEIGHT * 0.45
    process_and_draw_background(c, bg_image_path, blur_radius)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(about_text_x, PAGE_HEIGHT * 0.85, "About " + speaker_name)

    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleN.fontSize = 10
    styleN.leading = 12
    styleN.textColor = colors.white

    about_text_frame_width = PAGE_WIDTH * 0.45
    about_text_frame_height = PAGE_HEIGHT * 0.4


    frame = Frame(about_text_x, about_text_y, about_text_frame_width, about_text_frame_height, showBoundary=0)
    frame.addFromList([Paragraph(about_text, styleN)], c)

    headshot_width = 2.5 * inch
    headshot_height = 2.5 * inch
    image_x = PAGE_WIDTH * 0.6
    image_y = about_text_y + (about_text_frame_height - headshot_height) / 2

    c.drawImage(ImageReader(headshot_path), image_x, image_y, width=headshot_width, height=headshot_height, mask='auto')

    # Career Highlights
    c.setFont("Helvetica-Bold", 18)
    c.drawString(about_text_x, PAGE_HEIGHT * 0.45, "Career Highlights")

    num_highlights = len(career_highlights)
    half_index = (num_highlights + 1) // 2
    highlights_col1 = career_highlights[:half_index]
    highlights_col2 = career_highlights[half_index:]

    column_area_width = PAGE_WIDTH * 0.85
    individual_col_width = column_area_width / 2
    spacing_between_columns = PAGE_WIDTH * 0.05
    bullet_indent = 0.15 * inch
    text_indent_after_bullet = 0.3 * inch

    col1_x_start = PAGE_WIDTH * 0.075
    col2_x_start = col1_x_start + individual_col_width + spacing_between_columns

    initial_list_y = PAGE_HEIGHT * 0.38
    bullet_font_size = 9
    line_spacing = bullet_font_size + 5
    buffer_between_items = 0.15 * inch

    highlight_style = ParagraphStyle(
        name='HighlightStyle',
        fontName='Helvetica',
        fontSize=bullet_font_size,
        leading=line_spacing,
        textColor=colors.white,
        alignment=TA_LEFT
    )

    def draw_highlight_column(items, x_start, y_start):
        y = y_start
        for item in items:
            p = Paragraph(item, highlight_style)
            _, h = p.wrapOn(c, individual_col_width - text_indent_after_bullet, PAGE_HEIGHT)
            if y - h < PAGE_HEIGHT * 0.05:
                break
            bullet_y = y - highlight_style.leading + (highlight_style.leading - highlight_style.fontSize) / 2
            c.drawString(x_start + bullet_indent, bullet_y, "•")
            p.drawOn(c, x_start + text_indent_after_bullet, y - h)
            y -= (h + buffer_between_items)

    draw_highlight_column(highlights_col1, col1_x_start, initial_list_y)
    draw_highlight_column(highlights_col2, col2_x_start, initial_list_y)

    c.save()
    return pdf_path

# Usage example 
# create_speaker_kit_cover(
#     pdf_path="Speaker_Kit_Cover_Two_Pages_Wide_Short.pdf",
#     bg_image_path="publicspeakerhero.jpeg", # Original unblurred image path
#     headshot_path="Realtor-Headshots-2.webp",
#     speaker_name="Jordan Smith",
#     tagline="AIFOR ENTREPRENEURS & GLOBAL INNOVATION",
#     tags=["Keynote Speaker | Leadership Strategist | Author"],
#     blur_radius=15,
#     about_text=(
#         "Jordan Smith is a visionary leader and acclaimed author, renowned for his "
#         "transformative insights into modern leadership and technological innovation. "
#         "With over two decades of experience, Jordan empowers organizations and individuals "
#         "to navigate complex challenges and unlock their full potential in the digital age."
#     ),
#     career_highlights=[
#           "Authored best-selling book 'The AI Alchemist: ' ",
#         "Keynote speaker at over 100 international conferences on AI and leadership,",
#         "Led a groundbreaking initiative that resulted in a 30% efficiency ",
#         "Recognized as 'Top Innovator in Tech' by TechForward Magazine (2023)  ",
#         "Founded a highly successful startup focused on ethical AI solutions,  ",
#         "Delivered a highly-rated TEDx talk on 'The Future of Human-AI Collaboration .",
#     ]
# )