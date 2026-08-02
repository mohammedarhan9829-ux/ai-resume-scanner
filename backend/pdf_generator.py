import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

from backend.openai_service import OpenAIService


class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total page count dynamically and prints Page X of Y."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header
        self.drawString(40, 762, "ResuMatch Pro AI Learning Masterclass")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 755, 572, 755)

        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 30, page_text)
        self.drawString(40, 30, "Confidential Educational Notes — Pro Tier Access 👑")
        self.line(40, 42, 572, 42)
        self.restoreState()


def generate_notes_pdf(skill_name: str, domain: str = "General Engineering & Tech", experience_level: str = "Entry Level") -> bytes:
    """
    Generate a detailed multi-page PDF study masterclass document (3-4 pages).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=50
    )

    content = OpenAIService.generate_ai_study_notes(skill_name, domain, experience_level)

    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#6366f1")
    dark_bg = colors.HexColor("#0f172a")
    text_dark = colors.HexColor("#1e293b")
    amber_color = colors.HexColor("#d97706")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=primary_color,
        spaceAfter=4
    )

    category_style = ParagraphStyle(
        'DocCat',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=amber_color,
        spaceAfter=14
    )

    chapter_style = ParagraphStyle(
        'ChapterHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        textColor=text_dark,
        leading=14,
        spaceAfter=10
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=1,
        borderPadding=10,
        leading=12,
        spaceBefore=8,
        spaceAfter=12
    )

    callout_style = ParagraphStyle(
        'CalloutBox',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        textColor=colors.HexColor("#1e293b"),
        backColor=colors.HexColor("#eff6ff"),
        borderColor=colors.HexColor("#93c5fd"),
        borderWidth=1,
        borderPadding=8,
        leading=13,
        spaceAfter=10
    )

    story = []

    # Title Banner
    story.append(Paragraph(content.get("title", f"Masterclass: {skill_name}"), title_style))
    story.append(Paragraph(f"STREAM / DOMAIN: {content.get('category', domain)} | PRO LEARNING KIT 👑", category_style))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceAfter=14))

    # CHAPTER 1: Theoretical Overview
    story.append(Paragraph("Chapter 1: Theoretical Foundations & Architecture", chapter_style))
    story.append(Paragraph(content.get("executive_summary", f"{skill_name} is a foundational skill in {domain}."), body_style))
    
    story.append(Paragraph(f"<b>Key Takeaway:</b> Mastery of {skill_name} transforms theoretical understanding into scalable production execution.", callout_style))
    story.append(Spacer(1, 10))

    # CHAPTER 2: Core Technical Concepts
    story.append(Paragraph("Chapter 2: Core Concepts & Operational Mechanics", chapter_style))
    concepts = content.get("core_concepts", [])
    for concept in concepts:
        story.append(Paragraph(f"• {concept}", body_style))
    story.append(Spacer(1, 14))

    # Force Page Break to create Page 2
    story.append(PageBreak())

    # CHAPTER 3: Code Examples & Implementation Syntax
    story.append(Paragraph("Chapter 3: Code Implementation & Syntax Reference", chapter_style))
    story.append(Paragraph("The following production-ready scripts demonstrate core implementation patterns:", body_style))

    code_examples = content.get("code_examples", [])
    if isinstance(code_examples, list):
        for idx, code in enumerate(code_examples, 1):
            story.append(Paragraph(f"<b>Example {idx}: Production Syntax & Execution Script</b>", body_style))
            formatted_code = str(code).replace('\n', '<br/>').replace(' ', '&nbsp;')
            story.append(Paragraph(formatted_code, code_style))
            story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))

    # CHAPTER 4: Production Best Practices & Optimization
    story.append(Paragraph("Chapter 4: Production Best Practices & Optimization", chapter_style))
    best_practices = content.get("best_practices", [])
    for practice in best_practices:
        story.append(Paragraph(f"✓ {practice}", body_style))
    
    story.append(Spacer(1, 14))

    # Force Page Break for Page 3 (Hands-on Project Blueprint)
    story.append(PageBreak())

    # CHAPTER 5: Hands-on Portfolio Project Blueprint
    story.append(Paragraph("Chapter 5: Hands-on Portfolio Project Blueprint", chapter_style))
    story.append(Paragraph("Build the following project to demonstrate hands-on mastery on your resume:", body_style))
    
    project = content.get("project_blueprint", f"Build an end-to-end portfolio project for {skill_name}.")
    project_formatted = str(project).replace('\n', '<br/>')
    story.append(Paragraph(project_formatted, callout_style))
    story.append(Spacer(1, 14))

    # Certification Checklist
    story.append(Paragraph("Chapter 6: Final Competency Verification Checklist", chapter_style))
    checklist_items = [
        f"Understands core memory and execution model of {skill_name}.",
        "Capable of writing modular, error-handled scripts.",
        "Experienced in deploying code into production environment.",
        f"Completed hands-on portfolio project demonstrating {skill_name} proficiency."
    ]
    for item in checklist_items:
        story.append(Paragraph(f"[  ]  {item}", body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
