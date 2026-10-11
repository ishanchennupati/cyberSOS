"""Reviewed official requirements; route hints never establish incident facts."""
LOGIN='https://cybercrime.gov.in/Webform/Crime_AuthoLogin.aspx'
MANUAL='https://cybercrime.gov.in/UploadMedia/MHA-CitizenManualReportOtherCyberCrime-v10.pdf'
FAQ='https://cybercrime.gov.in/Webform/FAQ.aspx'
ANONYMOUS='https://cybercrime.gov.in/Webform/Crime_ReportAnonymously.aspx'
VERSION='ncrp-2026-10-11.2'


def mapping(signals):
    routes=[]
    if 'financial' in signals: routes.append('Financial Fraud')
    if set(signals)&{'harassment','threats','impersonation','account_takeover','device_compromise','scam_attempt'}:
        routes.append('Other Cyber Crime')
    # General harassment alone does not establish the special women/children
    # portal branch, which has specific content eligibility requirements.
    fields=[{'id':'incident_time','label':'Incident Date and Time','required':True,'format':'Date/time; approximate wording retained until citizen confirms precision','source_id':'NCRP-LOGIN','maximum_characters':None},
        {'id':'platform','label':'Where did the incident occur?','required':True,'format':'Service/platform','source_id':'NCRP-MANUAL-2019','maximum_characters':None},
        {'id':'narrative','label':'Incident details','required':True,'format':'Plain text','source_id':'NCRP-LOGIN','maximum_characters':None},
        {'id':'identifiers','label':'Suspected website URLs / Social Media handles / Suspect details','required':False,'format':'Copy supported identifiers individually','source_id':'NCRP-LOGIN','maximum_characters':None}]
    if 'financial' in signals:
        fields += [{'id':key,'label':label,'required':True,'format':fmt,'source_id':'NCRP-LOGIN','maximum_characters':None}
            for key,label,fmt in [('transaction_id','Transaction id/UTR No.','The public checklist states 12 digits; confirm rail-specific format on the portal.'),
                ('amount','Fraud amount','Decimal amount; currency must stay as reported.'),
                ('transaction_date','Date of transaction','Do not invent an exact date from an approximate time.'),
                ('bank_wallet_merchant','Name of the Bank / Wallet / Merchant','Unknown here unless supported; enter directly on the portal if needed.')]]
    return {'version':VERSION,'reviewed_on':'2026-10-11','jurisdiction':'India','fields':fields,
        'suggested_routes':routes,'destination':LOGIN,'sources':[
            {'id':'NCRP-LOGIN','url':LOGIN,'status':'current_public_page'},
            {'id':'NCRP-FAQ','url':FAQ,'status':'current_public_page'},
            {'id':'NCRP-ANONYMOUS','url':ANONYMOUS,'status':'current_public_form'},
            {'id':'NCRP-MANUAL-2019','url':MANUAL,'status':'historical_field_reference'}],
        'narrative':{'label':'Incident details','minimum_characters':200,'maximum_characters':None,
            'excluded_characters':'#$@^*`’‘\u007e|!','source_id':'NCRP-LOGIN'},
        'evidence':{'maximum_bytes':10*1024*1024,'accepted_extensions':None,'source_id':'NCRP-LOGIN'},
        'identity_document':{'maximum_bytes':5*1024*1024,'accepted_extensions':['jpeg','jpg','png'],
            'source_id':'NCRP-LOGIN','location':'official_portal_only'},
        'route_requirements':[{'id':'women_children_anonymous','label':'Women/children anonymous content report',
            'destination':ANONYMOUS,'source_ids':['NCRP-FAQ','NCRP-ANONYMOUS'],
            'eligibility_established':False,
            'eligibility':'The official FAQ identifies CSEAM and rape/gang-rape sexually explicit content for the women/children section, and rape/gang-rape content for anonymous reports. Ordinary harassment or a private-image threat alone does not establish eligibility.',
            'required_fields':['Category of complaint','Approximate date and time of incident/receiving/viewing of content',
                'State/UT','District','Where did the incident occur?','Additional incident information'],
            'narrative':{'minimum_characters':200,'maximum_characters':1500,'excluded_characters':"~!#^'`$|{}<>*"},
            'evidence':{'maximum_bytes':None,'accepted_extensions':None},
            'meaning':'These limits belong to the public anonymous form only; no automatic route selection. Do not attach explicit intimate media or child sexual-abuse material in CyberSOS.'}],
        'portal_only':['Identity and contact details','Identity document','Official portal OTP and registration'],
        'limitations':['Authenticated route-specific fields and maximum narrative length are not independently verified.',
            'The older manual states a different evidence limit; confirm the applicable limit on the official form.',
            'CyberSOS PDF is a preparation aid and does not fill or replace the official form.',
            'Public eligibility and anonymous-form requirements are source-linked below; authenticated attachment types/limits remain unverified. Confirm the applicable current form before uploading there.']}
