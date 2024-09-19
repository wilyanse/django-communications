# services/twilio_call_service.py
from django.conf import settings
from twilio.rest import Client

def make_call(to_phone_number, url_for_twiml):
    # Initialize the Twilio client
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    # Make the call
    call = client.calls.create(
        to=to_phone_number,
        from_=settings.TWILIO_PHONE_NUMBER,
        url=url_for_twiml  # URL pointing to TwiML instructions for call actions
    )
    
    return call.sid
