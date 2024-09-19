from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from .models import ChatRoom
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
import os

def chatPage(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("login-user")
    context = {}
    return render(request, "chat/chatPage.html", context)

def chat_room(request, username1, username2):
    user1 = get_object_or_404(User, username=username1)
    user2 = get_object_or_404(User, username=username2)
    
    # Ensure the users are sorted to avoid duplicate rooms like (user1, user2) and (user2, user1)
    if user1.id > user2.id:
        user1, user2 = user2, user1

    # Find or create a chat room between the two users
    room, created = ChatRoom.objects.get_or_create(user1=user1, user2=user2)

    return render(request, 'chat/chat.html', {
        'room_name': f'{user1.id}_{user2.id}',  # This will be used as the room identifier in WebSocket
        'username1': username1,
        'username2': username2
    })

@csrf_exempt
def upload_attachment(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        file_path = default_storage.save(os.path.join('attachments', file.name), file)
        file_url = settings.MEDIA_URL + file_path  # Construct the file URL based on MEDIA_URL
        return JsonResponse({'file_url': file_url})
    return JsonResponse({'error': 'No file uploaded'}, status=400)

@csrf_exempt
def landing_page(request):
    return render(request, 'landing_page.html', {
        'username1': 'user1',  # Hard-coded user1
        'username2': 'user2',  # Hard-coded user2
    })

def sms_page(request):
    return render(request, 'sms.html', {
        'username1': 'user1',  # Hard-coded user1
        'username2': 'user2',  # Hard-coded user2
    })

def call_page(request):
    return render(request, 'call.html', {
        'username1': 'user1',  # Hard-coded user1
        'username2': 'user2',  # Hard-coded user2
    })

# views.py
from .email_utils import send_email, fetch_inbox, get_email_data
from .oauth_setup import authenticate_gmail
from googleapiclient.discovery import build
import base64

def email_page(request):
    """Main email page with links to inbox and compose email."""
    return render(request, 'email.html')

def email_inbox(request):
    """View for displaying the email inbox."""
    email_data = fetch_inbox()  # Fetch emails
    return render(request, 'email_inbox.html', {'emails': email_data})


def view_message(request, message_id):
    """View to display an individual email with attachments."""
    email_data = get_email_data(message_id)
    
    return render(request, 'view_message.html', {
        'email': email_data
    })

def compose_email(request):
    """View for composing and sending an email with attachments."""
    if request.method == 'POST':
        recipient = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        
        # Handle attachments
        attachments = []
        if 'attachments' in request.FILES:
            for file in request.FILES.getlist('attachments'):
                attachment_data = base64.urlsafe_b64encode(file.read()).decode('utf-8')
                attachments.append({
                    'filename': file.name,
                    'data': attachment_data  # Ensure data is base64 encoded
                })
        
        # Send the email
        send_email(request.user.email, recipient, subject, body, attachments)
        return redirect('email_page')  # Redirect after sending

    return render(request, 'compose_email.html')

# views.py
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TextMessage  # Import your Message model

@csrf_exempt
def twilio_webhook(request):
    if request.method == 'POST':
        from twilio.request_validator import RequestValidator
        import os

        # Get your Twilio Auth Token from environment variables
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')

        validator = RequestValidator(auth_token)
        if validator.validate(
            request.build_absolute_uri(),
            request.POST,
            request.headers.get('X-Twilio-Signature')
        ):
            # Parse message details
            from_number = request.POST.get('From')
            body = request.POST.get('Body')

            # Save message to database
            TextMessage.objects.create(from_number=from_number, body=body)

            return HttpResponse('Message received', status=200)
        else:
            return HttpResponse('Invalid signature', status=403)
    return HttpResponse('Method not allowed', status=405)

from .models import Message

@csrf_exempt
def messages_list(request):
    messages = TextMessage.objects.all().order_by('-received_at')
    return render(request, 'messages_list.html', {'messages': messages})

from django.conf import settings
from twilio.rest import Client
from .forms import MessageForm
from django.contrib import messages

@csrf_exempt
def compose_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            # Extract the form data
            phone_number = form.cleaned_data['phone_number']
            message_body = form.cleaned_data['message']
            media_url = form.cleaned_data['media_url']

            # Send the message using Twilio
            try:
                # Twilio account credentials
                account_sid = settings.TWILIO_ACCOUNT_SID
                auth_token = settings.TWILIO_AUTH_TOKEN

                client = Client(account_sid, auth_token)

                # Send the SMS


                if media_url:
                    message = client.messages.create(
                        body=message_body,
                        from_=settings.TWILIO_PHONE_NUMBER,  # Your Twilio phone number
                        to=phone_number,
                        media_url = [media_url]
                    )
                else:
                    message = client.messages.create(
                        body=message_body,
                        from_=settings.TWILIO_PHONE_NUMBER,  # Your Twilio phone number
                        to=phone_number
                    )

                messages.success(request, f"Message sent to {phone_number}")
                print("Message SID: " + message.sid)
                return redirect('compose_message')  # Redirect to avoid re-submission on refresh

            except Exception as e:
                messages.error(request, f"Failed to send message: {str(e)}")

    else:
        form = MessageForm()

    return render(request, 'compose_message.html', {'form': form})

# views.py

from django.http import HttpResponse
from twilio.twiml.voice_response import VoiceResponse

def inbound_call(request):
    response = VoiceResponse()
    response.say("Hello, this is a test call from Django.")
    return HttpResponse(str(response), content_type='text/xml')

# views.py

from django.shortcuts import render, redirect
from django.conf import settings
from twilio.rest import Client
from .forms import CallForm

def make_call(request):
    if request.method == 'POST':
        form = CallForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            
            # Initialize Twilio client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            # Make the call
            call = client.calls.create(
                to=phone_number,
                from_=settings.TWILIO_PHONE_NUMBER,
                url='https://handler.twilio.com/twiml/EHec3fd46cdcb693a7b0f9753017ffc07a'  # URL of your Twilio Studio Flow
            )
            
            return redirect('success')  # Redirect to a success page or show a message
    else:
        form = CallForm()
    
    return render(request, 'make_call.html', {'form': form})

from django.http import HttpResponse
from twilio.twiml.voice_response import VoiceResponse

def twiml_response(request):
    response = VoiceResponse()
    response.dial(TWILIO_PHONE_NUMBER)
    return HttpResponse(str(response))

# views.py

import jwt
import time
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from django.conf import settings
from django.shortcuts import render

def generate_token(request):
    # Twilio Account credentials
    account_sid = settings.TWILIO_ACCOUNT_SID
    api_key_sid = 'SKcdfa93283ca4695321ba925bfe95620b'
    api_key_secret = 'uJ04J4CLA9jPa9s5GYIVKT5UbIXPCcS4'
    
    # Create access token
    token = AccessToken(account_sid, api_key_sid, api_key_secret, identity="user_identity")
    
    # Add a VoiceGrant to the token
    voice_grant = VoiceGrant(
        outgoing_application_sid='AP332cbfe471ea2285d8cc9bf17ac6a2eb',  # TwiML App SID
        incoming_allow=True  # Optional: Allow incoming calls
    )
    token.add_grant(voice_grant)
    
    # Return the token
    return JsonResponse({'token': token.to_jwt()})

from twilio.twiml.voice_response import VoiceResponse
from django.http import HttpResponse

def twiml_app(request):
    response = VoiceResponse()
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        to='+639391986763',
        from_=settings.TWILIO_PHONE_NUMBER,
        url='https://handler.twilio.com/twiml/EHec3fd46cdcb693a7b0f9753017ffc07a'  # URL of your Twilio Studio Flow
    )
    # Dial the number passed from the browser
    to_number = request.GET.get('To', None)
    if to_number:
        response.dial(caller_id=settings.TWILIO_PHONE_NUMBER).number(to_number)
    else:
        response.say("No number to dial.")

    return HttpResponse(str(response), content_type='application/xml')

# views.py
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse

@csrf_exempt
def receive_sms(request):
    if request.method == 'POST':
        # Extract the message details from Twilio's POST request
        from_number = request.POST.get('From')
        message_body = request.POST.get('Body')

        # You can save the message to your database if needed
        # Example:
        SMSMessage.objects.create(from_number=from_number, message_body=message_body)

        # Respond with an empty Twilio MessagingResponse to acknowledge the receipt
        response = MessagingResponse()
        msg = response.message("Check out this sweet owl!")
        return HttpResponse(str(response))

    return HttpResponse(status=400)

# views.py
from django.shortcuts import render
from .models import SMSMessage

def list_sms_messages(request):
    messages = SMSMessage.objects.all().order_by('-received_at')
    return render(request, 'list_messages.html', {'messages': messages})

from django.http import HttpResponse
from twilio.twiml.voice_response import VoiceResponse

def handle_call(self):
    response = VoiceResponse()
    if action == 'accept':
        # Connect the call or handle as needed
        response.say('Connecting your call.')
        response.dial('+13049320134')  # Replace with the number to connect the call to
    else:
        # Reject the call
        response.say('Call rejected.')
        response.hangup()
    
    return HttpResponse(str(response), content_type='application/xml')

def call_decision(request):
    # This view renders the page with "Accept" and "Reject" buttons
    return render(request, 'call_decision.html')

from django.shortcuts import redirect
from django.urls import reverse

@csrf_exempt
def answer(self):
    return False

def decision_page(request):
    data = request.GET.get('data')  # Retrieve the data sent from the webhook
    context = {'data': data}
    return render(request, 'decision_page.html', context)

from django.shortcuts import render, redirect
from django.http import HttpResponse
from twilio.twiml.voice_response import VoiceResponse

@csrf_exempt
def incoming_call_page(request):
    print(request)
    return render(request, 'call_input.html')

@csrf_exempt
def handle_user_input(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        print(f"Received action: {action}")  # Debugging line

        response = VoiceResponse()
        if action == 'accept':
            response.say("Call accepted.")
            response.dial("+1234567890")  # Replace with your desired number
        elif action == 'reject':
            response.say("Call rejected.")
            response.hangup()
        else:
            return redirect('incoming_call_page')

        return HttpResponse(str(response), content_type='application/xml')
    else:
        return redirect('incoming_call_page')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CallPreferenceForm
from .models import CallPreference
from twilio.rest import Client
from django.conf import settings


def update_preferences(request):
    # Ensure only one preference object exists
    if CallPreference.objects.exists():
        preference = CallPreference.objects.first()
    else:
        preference = CallPreference()

    if request.method == 'POST':
        form = CallPreferenceForm(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            return redirect('update_preferences')
    else:
        form = CallPreferenceForm(instance=preference)

    return render(request, 'update_preferences.html', {'form': form})

@csrf_exempt
def handle_incoming_call(request):
    call_sid = request.GET.get('CallSid')
    from_number = request.GET.get('From')
    to_number = request.GET.get('To')

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    preference = CallPreference.objects.first()
    response = VoiceResponse()
    if preference:
        if preference.auto_accept_calls:
            response.say('Call Accepted.')
        else:
            response.say('Call rejected.')
    else:
        response_message = "Rejected"

    return HttpResponse(str(response), content_type='application/xml')