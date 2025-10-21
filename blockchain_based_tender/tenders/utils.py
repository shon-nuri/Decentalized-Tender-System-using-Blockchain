# tenders/utils.py
from io import BytesIO
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from datetime import datetime

def generate_contract_pdf(tender, winner_bid):
    """Generate a contract PDF for the winning bid"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center aligned
    )
    
    # Story (content)
    story = []
    
    # Title
    story.append(Paragraph("CONTRACT AGREEMENT", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Parties
    story.append(Paragraph(f"<b>Between:</b>", styles['Normal']))
    story.append(Paragraph(f"<b>{tender.creator.company_name or tender.creator.username}</b>", styles['Normal']))
    story.append(Paragraph(f"Email: {tender.creator.email}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(f"<b>And:</b>", styles['Normal']))
    story.append(Paragraph(f"<b>{winner_bid.bidder.company_name or winner_bid.bidder.username}</b>", styles['Normal']))
    story.append(Paragraph(f"Email: {winner_bid.bidder.email}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Contract details
    story.append(Paragraph(f"<b>Tender Title:</b> {tender.title}", styles['Normal']))
    story.append(Paragraph(f"<b>Contract Value:</b> ${winner_bid.price}", styles['Normal']))
    story.append(Paragraph(f"<b>Description:</b> {tender.description}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Terms and conditions
    story.append(Paragraph("<b>Terms and Conditions:</b>", styles['Heading2']))
    terms = [
        "1. The contractor shall complete the work as described in the tender.",
        "2. Payment will be made upon satisfactory completion of work.",
        "3. Any disputes shall be resolved through mutual agreement.",
        "4. This contract is binding for both parties.",
        "5. Work must be completed by the specified deadline."
    ]
    
    for term in terms:
        story.append(Paragraph(term, styles['Normal']))
    
    story.append(Spacer(1, 0.5*inch))
    
    # Signatures
    story.append(Paragraph("<b>Signatures:</b>", styles['Heading2']))
    story.append(Spacer(1, 0.5*inch))
    
    # Tender creator signature
    story.append(Paragraph("_________________________", styles['Normal']))
    story.append(Paragraph(f"<b>{tender.creator.company_name or tender.creator.username}</b>", styles['Normal']))
    story.append(Paragraph("Tender Creator", styles['Normal']))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Winner signature
    story.append(Paragraph("_________________________", styles['Normal']))
    story.append(Paragraph(f"<b>{winner_bid.bidder.company_name or winner_bid.bidder.username}</b>", styles['Normal']))
    story.append(Paragraph("Contractor", styles['Normal']))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer

def download_contract(request, tender_id):
    """View to download contract PDF"""
    from .models import Tender
    tender = Tender.objects.get(id=tender_id)
    
    if not tender.awarded_bid:
        return HttpResponse("No awarded bid for this tender")
    
    if request.user not in [tender.creator, tender.awarded_bid.bidder]:
        return HttpResponse("Unauthorized", status=403)
    
    buffer = generate_contract_pdf(tender, tender.awarded_bid)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contract_tender_{tender.id}.pdf"'
    return response
