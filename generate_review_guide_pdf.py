import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 750, "CallShield AI — College Review & Viva Presentation Guide")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 50, 558, 50)
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 35, page_str)
        self.drawString(54, 35, "Confidential — Prepared for Academic Review & Viva Evaluation")
        self.restoreState()

def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=64
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#1E1B4B") # Indigo 950
    accent_color = colors.HexColor("#4F46E5")  # Indigo 600
    dark_gray = colors.HexColor("#1E293B")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=accent_color,
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=dark_gray,
        spaceAfter=8
    )

    bold_body_style = ParagraphStyle(
        'BoldBodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=dark_gray,
        spaceAfter=6
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=dark_gray
    )

    story = []

    # Title & Header Block
    story.append(Paragraph("🛡️ CallShield AI", title_style))
    story.append(Paragraph("College Review & Viva Presentation Guide (Complete Reference)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceAfter=15))

    # Section 1: Executive Summary
    story.append(Paragraph("1. Executive Summary (Project Pitch)", h1_style))
    summary_text = (
        "<b>CallShield AI</b> is an intelligent real-time scam call detection and protection platform designed "
        "for Android smartphones and web environments. It automatically intercepts active incoming and outgoing phone calls, "
        "converts spoken speech into text using continuous speech recognition, and applies Machine Learning "
        "(TF-IDF Feature Extraction + Calibrated Classification) to compute fraud risk scores (0–100%) and "
        "alert users to scam threats in real time."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))

    # Section 2: Tech Stack Table
    story.append(Paragraph("2. Technology Stack", h1_style))
    tech_data = [
        [Paragraph("Layer", table_header_style), Paragraph("Technology Used", table_header_style), Paragraph("Purpose / Responsibility", table_header_style)],
        [Paragraph("Android App", table_cell_style), Paragraph("Java, Native XML Layouts", table_cell_style), Paragraph("Builds native dialer, contact list, overlay UI, and background phone state receiver.", table_cell_style)],
        [Paragraph("Web Frontend", table_cell_style), Paragraph("HTML5, TailwindCSS, FontAwesome, JS", table_cell_style), Paragraph("Renders real-time risk meter, speaker transcript bubbles, and dashboard controls.", table_cell_style)],
        [Paragraph("Backend API", table_cell_style), Paragraph("Python 3.10+, Flask", table_cell_style), Paragraph("Serves REST API endpoints (/api/analyze_live) to process text and calculate risk metrics.", table_cell_style)],
        [Paragraph("Machine Learning", table_cell_style), Paragraph("Scikit-Learn, TF-IDF Vectorizer", table_cell_style), Paragraph("Extracts textual n-grams and computes calibrated fraud probability percentage.", table_cell_style)],
        [Paragraph("Speech Recognition", table_cell_style), Paragraph("Android SpeechRecognizer & WebSpeech", table_cell_style), Paragraph("Converts live spoken audio to text continuously in Hindi (hi-IN) & English.", table_cell_style)],
        [Paragraph("Hosting & Cloud", table_cell_style), Paragraph("Vercel & GitHub", table_cell_style), Paragraph("Provides live cloud deployment and version control.", table_cell_style)]
    ]
    
    t_tech = Table(tech_data, colWidths=[100, 150, 254])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), accent_color),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")])
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 12))

    # Section 3: Web Project Files Table
    story.append(Paragraph("3. Website & ML Backend Files (Scam_audio_Full_Project)", h1_style))
    web_files_data = [
        [Paragraph("File Path", table_header_style), Paragraph("Key Function & Responsibility", table_header_style)],
        [Paragraph("app.py", table_cell_style), Paragraph("Main Flask application server. Handles routing, loads ML models, and serves /api/analyze_live endpoint.", table_cell_style)],
        [Paragraph("models/scam_detector_calibrated.pkl", table_cell_style), Paragraph("Trained Scikit-Learn classifier model file that outputs fraud risk probability (0% to 100%).", table_cell_style)],
        [Paragraph("models/vectorizer.pkl", table_cell_style), Paragraph("TF-IDF Vectorizer file that transforms raw speech text into numerical feature matrices.", table_cell_style)],
        [Paragraph("templates/modules/live_call.html", table_cell_style), Paragraph("Live call detection UI. Displays the animated circular risk gauge, speaker transcript, and red flag badges.", table_cell_style)],
        [Paragraph("templates/dashboard.html", table_cell_style), Paragraph("System dashboard displaying analytics, system status, and links to recorded call logs.", table_cell_style)],
        [Paragraph("generate_research_pdf.py", table_cell_style), Paragraph("Automated report generator script producing official academic documentation.", table_cell_style)]
    ]
    t_web = Table(web_files_data, colWidths=[180, 324])
    t_web.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")])
    ]))
    story.append(t_web)
    story.append(Spacer(1, 12))

    # Section 4: Android App Files Table
    story.append(Paragraph("4. Android App Architecture Files (CallShield_Android_App)", h1_style))
    app_files_data = [
        [Paragraph("File Path", table_header_style), Paragraph("Key Function & Responsibility", table_header_style)],
        [Paragraph("MainActivity.java", table_cell_style), Paragraph("Main Activity controller. Controls native dialpad, native contacts list, permissions, and overlay container.", table_cell_style)],
        [Paragraph("CallReceiver.java", table_cell_style), Paragraph("BroadcastReceiver intercepting PHONE_STATE_CHANGED and NEW_OUTGOING_CALL when a call connects.", table_cell_style)],
        [Paragraph("CallShieldService.java", table_cell_style), Paragraph("Foreground Service with high-priority notification to maintain live call scanning without background kill.", table_cell_style)],
        [Paragraph("activity_main.xml", table_cell_style), Paragraph("Native layout defining sleek dark keypad buttons, tab switcher, and hidden overlay view container.", table_cell_style)],
        [Paragraph("item_contact.xml", table_cell_style), Paragraph("Custom layout for contact items featuring colored initial avatars, name, phone number, and call button.", table_cell_style)],
        [Paragraph("AndroidManifest.xml", table_cell_style), Paragraph("Declares system permissions (RECORD_AUDIO, READ_CALL_LOG, SYSTEM_ALERT_WINDOW, FOREGROUND_SERVICE).", table_cell_style)]
    ]
    t_app = Table(app_files_data, colWidths=[180, 324])
    t_app.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")])
    ]))
    story.append(t_app)
    story.append(Spacer(1, 14))

    # Section 5: End-to-End Flow
    story.append(Paragraph("5. End-to-End System Workflow (Step-by-Step)", h1_style))
    workflow_text = (
        "<b>Step 1 (Call Connect):</b> User dials a number or receives an incoming call.<br/>"
        "<b>Step 2 (State Interception):</b> Android <i>CallReceiver</i> & <i>CallShieldService</i> detect <code>CALL_STATE_OFFHOOK</code>.<br/>"
        "<b>Step 3 (Overlay Display):</b> <i>MainActivity</i> brings the zero-click AI scanner overlay to the screen.<br/>"
        "<b>Step 4 (Speech to Text):</b> Audio is captured and converted to transcript text continuously.<br/>"
        "<b>Step 5 (ML Backend Request):</b> Transcript text is sent via HTTP POST to <code>/api/analyze_live</code>.<br/>"
        "<b>Step 6 (Feature Extraction & Scoring):</b> TF-IDF vectorizer extracts n-gram patterns (e.g., <i>'bank OTP'</i>, <i>'compromised account'</i>), and the Calibrated Classifier calculates the fraud risk score (%).<br/>"
        "<b>Step 7 (Real-Time Alert):</b> The UI updates the circular risk meter dynamically (Green = Safe, Red = Scam Confirmed)."
    )
    story.append(Paragraph(workflow_text, body_style))
    story.append(Spacer(1, 14))

    # Section 6: Teacher Q&A
    story.append(Paragraph("6. Anticipated Review Questions & Ideal Answers", h1_style))
    
    q1 = "<b>Q1: Why did you use TF-IDF + Calibrated Classifier instead of simple keyword matching?</b>"
    a1 = "<b>Answer:</b> Keyword matching is rigid and easily circumvented by minor word variations. TF-IDF measures word frequency and rarity across datasets, allowing our Machine Learning model to evaluate contextual n-grams and generate a calibrated probability percentage (e.g. 88.5% risk) rather than binary matches."
    story.append(Paragraph(q1, bold_body_style))
    story.append(Paragraph(a1, body_style))
    story.append(Spacer(1, 6))

    q2 = "<b>Q2: How does the Android app intercept calls automatically without clicking a button?</b>"
    a2 = "<b>Answer:</b> We implemented an Android <i>BroadcastReceiver</i> (CallReceiver) paired with a <i>ForegroundService</i> (CallShieldService) and requested <i>SYSTEM_ALERT_WINDOW</i> ('Display over other apps') permission. When the telephony state transitions to OFFHOOK, Android permits our service to launch the scanner activity automatically."
    story.append(Paragraph(q2, bold_body_style))
    story.append(Paragraph(a2, body_style))
    story.append(Spacer(1, 6))

    q3 = "<b>Q3: What languages are supported by the live scanner?</b>"
    a3 = "<b>Answer:</b> The speech engine supports Hindi (hi-IN), Marathi (mr-IN), Indian English (en-IN), and US English (en-US), making it tailored for diverse real-world Indian fraud attempts."
    story.append(Paragraph(q3, bold_body_style))
    story.append(Paragraph(a3, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {filename}")

if __name__ == "__main__":
    out1 = r"C:\Users\manav\OneDrive\Desktop\CallShield_AI_College_Review_Guide.pdf"
    out2 = r"C:\Users\manav\OneDrive\Desktop\Scam_audio_Full_Project\static\downloads\CallShield_AI_College_Review_Guide.pdf"
    
    os.makedirs(os.path.dirname(out2), exist_ok=True)
    
    build_pdf(out1)
    build_pdf(out2)
