#!/usr/bin/env python3
"""
Generate a beautiful PDF from the client message markdown file
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re
from datetime import datetime

def create_pdf():
    """Generate a beautiful PDF from the markdown content"""

    # Read the markdown file
    with open('CLIENT_MESSAGE_BUG_FIXES_DEPLOYED.md', 'r', encoding='utf-8') as f:
        content = f.read()

    # Create PDF document
    pdf_filename = f"Bug_Fixes_Deployed_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Define color scheme
    primary_color = HexColor('#2563eb')  # Blue
    success_color = HexColor('#10b981')  # Green
    heading_color = HexColor('#1e293b')  # Dark slate
    text_color = HexColor('#334155')     # Slate gray
    code_bg = HexColor('#f1f5f9')        # Light gray

    # Create custom styles
    styles = getSampleStyleSheet()

    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=primary_color,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Heading 2 style
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=heading_color,
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderColor=primary_color,
        borderPadding=8,
        backColor=HexColor('#f0f9ff')
    )

    # Heading 3 style
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=success_color,
        spaceAfter=10,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    # Body text style
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=text_color,
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        leading=16
    )

    # Bold text style
    bold_style = ParagraphStyle(
        'CustomBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    # Code style
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=10,
        textColor=HexColor('#dc2626'),
        backColor=code_bg,
        fontName='Courier',
        leftIndent=20,
        rightIndent=20,
        spaceAfter=12,
        spaceBefore=6
    )

    # List style
    list_style = ParagraphStyle(
        'CustomList',
        parent=body_style,
        leftIndent=30,
        bulletIndent=15,
        spaceAfter=6
    )

    # Build document content
    story = []

    # Parse markdown content and exclude database migration section
    lines = content.split('\n')
    i = 0
    skip_section = False

    while i < len(lines):
        line = lines[i].strip()

        # Check if we're entering sections to skip
        if line.startswith('## 📝 BEFORE YOU TEST - IMPORTANT!') or line.startswith('## ❓ ANSWERS TO YOUR QUESTIONS') or line.startswith('## 🚀 DEPLOYMENT STATUS'):
            skip_section = True
            i += 1
            continue

        # Check if we're exiting the skip section (next ## heading or end of file)
        if skip_section and line.startswith('## '):
            skip_section = False

        # Skip lines in the migration section
        if skip_section:
            i += 1
            continue

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Title (# with emoji)
        if line.startswith('# '):
            title_text = line[2:].strip()
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 0.2*inch))

        # H2 (##)
        elif line.startswith('## '):
            h2_text = line[3:].strip()
            story.append(Spacer(1, 0.15*inch))
            story.append(Paragraph(h2_text, h2_style))

        # H3 (###)
        elif line.startswith('### '):
            h3_text = line[4:].strip()
            story.append(Paragraph(h3_text, h3_style))

        # Horizontal rule
        elif line.startswith('---'):
            story.append(Spacer(1, 0.1*inch))

        # Code block
        elif line.startswith('```'):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code_text = '<br/>'.join(code_lines)
            story.append(Paragraph(f'<font face="Courier">{code_text}</font>', code_style))

        # Bullet points
        elif line.startswith('- '):
            bullet_text = line[2:].strip()
            # Skip the database migration script line
            if 'Database migration script included' in bullet_text:
                i += 1
                continue
            # Handle bold text
            bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
            # Handle inline code
            bullet_text = re.sub(r'`(.*?)`', r'<font face="Courier" color="#dc2626">\1</font>', bullet_text)
            story.append(Paragraph(f'• {bullet_text}', list_style))

        # Regular paragraph
        else:
            # Skip if it's just a closing code block
            if line == '```':
                i += 1
                continue

            # Handle bold text
            line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            # Handle inline code
            line = re.sub(r'`(.*?)`', r'<font face="Courier" color="#dc2626">\1</font>', line)
            # Handle links
            line = re.sub(r'\[(.*?)\]\((.*?)\)', r'<u><font color="#2563eb">\1</font></u>', line)

            story.append(Paragraph(line, body_style))

        i += 1

    # Build PDF
    doc.build(story)

    print(f"✅ PDF generated successfully: {pdf_filename}")
    return pdf_filename

if __name__ == "__main__":
    create_pdf()
