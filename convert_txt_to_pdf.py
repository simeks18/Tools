import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

def text_to_pdf_reportlab(input_folder, output_filename):
    # Register a standard Unicode-ready font
    # 'HeiseiMin-W3' is a standard CID font that supports broad Unicode
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
    
    doc = SimpleDocTemplate(output_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create a custom style for our text
    text_style = ParagraphStyle(
        'UnicodeStyle',
        parent=styles['Normal'],
        fontName='HeiseiMin-W3',
        fontSize=10,
        leading=12,
    )
    
    title_style = styles['Heading2']
    
    story = []
    files = sorted([f for f in os.listdir(input_folder) if f.endswith('.txt')])

    for filename in files:
        if filename == output_filename:
            continue
            
        # Add Title for each file
        story.append(Paragraph(f"Source: {filename}", title_style))
        story.append(Spacer(1, 12))
        
        file_path = os.path.join(input_folder, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Replace newlines with <br/> for ReportLab's Paragraph tag
                content = f.read().replace('\n', '<br/>')
                story.append(Paragraph(content, text_style))
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
        # Add a page break between files
        from reportlab.platypus import PageBreak
        story.append(PageBreak())

    doc.build(story)
    print(f"✅ Success! Generated {output_filename}")

text_to_pdf_reportlab('.', 'Final_Submission_Merged.pdf')

