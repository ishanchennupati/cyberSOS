"""Render the reviewed packet as inert private artifacts, without fetching URLs."""
import html
import io
from pathlib import Path
from app.services.reporting import display


def sections(data):
    packet,narrative=data['packet'],data['narrative']
    return [('Citizen account',narrative['text']),('Portal transfer copy',narrative['portal_text']),
        ('Reviewed facts','\n'.join(f"{fact['label']}: {display(fact['value'])}" for fact in packet['facts'])),
        ('Unknown information','\n'.join(packet['unknowns']) or 'No additional unknowns listed.'),
        ('Evidence inventory','\n'.join(f"{item['name']} ({item['mime_type']}, {item['size_bytes']} bytes). Contents not verified by inventory." for item in packet['evidence']) or 'No attachments listed.'),
        ('Actions recorded by you','\n'.join(f"{item['action_id']}: {'completed' if item['completed'] else 'not completed'}; reference: {item['reference'] or 'not recorded'}" for item in packet['recorded_actions']) or 'No action completion recorded.'),
        ('Official handoff','Complete registration, identity verification and submission on the official portal. This packet is not an official receipt. Uploading this PDF does not fill or replace the official form.'),
        ('Official sources','\n'.join(s['url'] for s in packet['mapping']['sources']))]


def printable(data):
    body=''.join(f'<section><h2>{html.escape(title)}</h2><p>{html.escape(text)}</p></section>' for title,text in sections(data))
    return '<!doctype html><html lang="en"><meta charset="utf-8"><title>CyberSOS reviewed reporting packet</title><style>body{font:16px system-ui;max-width:760px;margin:32px auto;padding:16px}p{white-space:pre-wrap;overflow-wrap:anywhere}section{break-inside:avoid}@media print{body{margin:0;padding:0}}</style><body><h1>CyberSOS reviewed reporting packet</h1><p>Prepared by CyberSOS. Use your browser Print command to print or save a PDF.</p>'+body+'</body></html>'


def pdf(data):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
    from fastapi import HTTPException
    candidates=[Path('C:/Windows/Fonts/segoeui.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    path=next((p for p in candidates if p.exists()),None)
    if path is None:raise HTTPException(503,'PDF font unavailable. Use the print view or JSON download.')
    if 'CyberSOS' not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont('CyberSOS',str(path)))
    font=pdfmetrics.getFont('CyberSOS')
    content=sections(data)
    if any(ord(c) not in font.face.charToGlyph for _,text in content for c in text if not c.isspace()):
        raise HTTPException(422,'PDF font cannot render part of this packet. Use browser print or the Unicode JSON download.')
    styles=getSampleStyleSheet()
    for style in styles.byName.values():style.fontName='CyberSOS'
    stream=io.BytesIO();story=[Paragraph('CyberSOS reviewed reporting packet',styles['Title']),
        Paragraph('Prepared by CyberSOS; not an official receipt.',styles['BodyText']),Spacer(1,12)]
    for title,text in content:
        story += [Paragraph(html.escape(title),styles['Heading2']),Paragraph(html.escape(text).replace('\n','<br/>'),styles['BodyText']),Spacer(1,8)]
    SimpleDocTemplate(stream,title='CyberSOS reviewed reporting packet',author='CyberSOS').build(story)
    return stream.getvalue()
