# email_utils.py
from googleapiclient.discovery import build
from .oauth_setup import authenticate_gmail
import base64
import email as em
from email.mime.text import MIMEText
import mimetypes
from googleapiclient.http import MediaFileUpload
import io

def create_message(sender, to, subject, body, attachments=None):
    """Create a message with optional attachments."""
    # Create the base message body
    message_body = f"From: {sender}\r\nTo: {to}\r\nSubject: {subject}\r\n\r\n{body}"
    
    # Create the email message with MIME format
    msg = em.mime.multipart.MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to
    msg['Subject'] = subject

    # Attach the text body
    msg.attach(em.mime.text.MIMEText(body, 'plain'))

    # Attach files if provided
    if attachments:
        for attachment in attachments:
            part = em.mime.base.MIMEBase('application', 'octet-stream')
            part.set_payload(base64.urlsafe_b64decode(attachment['data']))
            em.encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{attachment["filename"]}"'
            )
            msg.attach(part)

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    return {'raw': raw_message}

def send_email(sender, to, subject, body, attachments=None):
    """Send an email with optional attachments."""
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    message = create_message(sender, to, subject, body, attachments)
    try:
        message = service.users().messages().send(userId='me', body=message).execute()
        print(f'Message Id: {message["id"]}')
    except Exception as error:
        print(f'An error occurred: {error}')

def list_messages(service, user_id, query=''):
    """List all messages matching the query."""
    try:
        results = service.users().messages().list(userId=user_id, q=query).execute()
        messages = results.get('messages', [])
        return messages
    except Exception as error:
        print(f'An error occurred: {error}')
        return []

def get_email_data(message_id):
    """Retrieve both email details and attachments using the message ID."""
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    # Fetch the email message
    msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    
    headers = msg['payload']['headers']
    subject = next(header['value'] for header in headers if header['name'] == 'Subject')
    sender = next(header['value'] for header in headers if header['name'] == 'From')
    date = next(header['value'] for header in headers if header['name'] == 'Date')
    
    body = ""
    attachments = []

    # Extract body and attachments
    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            mime_type = part['mimeType']
            if mime_type == 'text/plain':
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif 'filename' in part and part['filename']:
                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    attachment = service.users().messages().attachments().get(userId='me', messageId=message_id, id=attachment_id).execute()
                    filename = part['filename']
                    data = base64.urlsafe_b64decode(attachment['data'])
                    attachments.append({
                        'filename': filename,
                        'data': base64.b64encode(data).decode('utf-8')  # Correct base64 encoding
                    })

    return {
        'subject': subject,
        'sender': sender,
        'date': date,
        'body': body,
        'attachments': attachments
    }

def get_message(service, user_id, message_id):
    """Get the message details and content."""
    try:
        message = service.users().messages().get(userId=user_id, id=message_id, format='full').execute()
        headers = message['payload']['headers']
        parts = message['payload'].get('parts', [])
        
        # Extract subject
        subject = next(header['value'] for header in headers if header['name'] == 'Subject')
        # Extract email body
        body = ''
        if parts:
            for part in parts:
                mime_type = part['mimeType']
                data = part['body'].get('data')
                if data:
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            # No parts, try the raw body
            data = message['payload']['body'].get('data')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')

        # Extract sender and recipient
        from_ = next(header['value'] for header in headers if header['name'] == 'From')
        to_ = next(header['value'] for header in headers if header['name'] == 'To')
        date_ = next(header['value'] for header in headers if header['name'] == 'Date')

        return {
            'id': message['id'],
            'subject': subject,
            'body': body,
            'from': from_,
            'to': to_,
            'date': date_
        }
    except Exception as error:
        print(f'An error occurred: {error}')
        return {}

def fetch_inbox():
    """Fetch emails from Gmail inbox and return them."""
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    
    messages = list_messages(service, 'me')
    email_data = []
    
    for message in messages:
        msg = get_message(service, 'me', message['id'])
        email_data.append(msg)
    
    return email_data

def get_email_attachments(message_id):
    """Retrieve attachments from an email."""
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    
    # Get the email message
    msg = service.users().messages().get(userId='me', id=message_id, format='raw').execute()
    msg_raw = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
    
    email_message = em.message_from_bytes(msg_raw)
    attachments = []

    for part in email_message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        
        filename = part.get_filename()
        if filename:
            data = part.get_payload(decode=True)
            attachments.append({
                'filename': filename,
                'data': base64.urlsafe_b64encode(data).decode('utf-8')
            })
    
    return attachments