"""Small synthetic, non-explicit readable fixtures; no external downloads."""
from io import BytesIO


FINANCIAL = ['SYNTHETIC PAYMENT RECORD', 'Amount: INR 3,500.00', 'Payment method: UPI',
    'Transaction reference: SYNTH-UTR-3500', 'Status: Completed', 'Recipient: Sample Store',
    'Recipient UPI: sample-store@upi', 'Date: 07 October (year not shown)']
THREAT = ['SYNTHETIC NON-EXPLICIT CHAT', 'Platform: Instagram', 'Profile: https://example.invalid/profile/demo',
    'Message: Pay me or I will share your private photos.', 'No photos or explicit media included.',
    'Time shown: 10:30 (date and timezone not shown)']
ACCOUNT = ['SYNTHETIC ACCOUNT NOTICE', 'Platform: Google', 'Profile: demo@example.invalid',
    'Message: An unfamiliar device signed in.', 'Time shown: 08:15 (date and timezone not shown)']


def image_bytes(lines=FINANCIAL, format='PNG'):
    from pathlib import Path
    name = 'threat' if lines == THREAT else 'account' if lines == ACCOUNT else 'financial'
    return (Path(__file__).parent / 'fixtures/phase5' / (name + ('.jpg' if format == 'JPEG' else '.png'))).read_bytes()


def pdf_bytes(lines=FINANCIAL):
    def escape(line):
        return line.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    stream = ('BT /F1 16 Tf 40 750 Td ' + ' '.join('('+escape(line)+') Tj 0 -35 Td' for line in lines) + ' ET').encode('ascii')
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    result, offsets = b'%PDF-1.4\n', [0]
    for i, obj in enumerate(objects,1):
        offsets.append(len(result))
        result += str(i).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
    xref = len(result)
    result += b'xref\n0 6\n0000000000 65535 f \n'
    for offset in offsets[1:]:
        result += f'{offset:010d} 00000 n \n'.encode()
    return result+f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode()


if __name__ == '__main__':
    from pathlib import Path
    root = Path(__file__).parent / 'fixtures/phase5'
    root.mkdir(parents=True, exist_ok=True)
    (root/'financial.pdf').write_bytes(pdf_bytes())
    print('Synthetic readable PDF fixture generated.')
