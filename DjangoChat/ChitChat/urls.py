from django.urls import path, include
from ChitChat import views as chat_views
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    path('', chat_views.landing_page, name='landing_page'),  # Landing page
    path('chat/<str:username1>/<str:username2>/', chat_views.chat_room, name='chat_room'),    # Chat page
    path('email/', chat_views.email_page, name='email_page'),   # Existing page
    path('email/inbox/', chat_views.email_inbox, name='email_inbox'), # Inbox view
    path('email/compose/', chat_views.compose_email, name='compose_email'), # Compose view
    path('email/message/<str:message_id>/', chat_views.view_message, name='view_message'),  # New URL pattern
    path('sms/', chat_views.sms_page, name='sms_page'),       # SMS page
    path('call/', chat_views.call_page, name='call_page'),    # Call page
    path('upload/', chat_views.upload_attachment, name='upload_attachment'),
    path('twilio-webhook/', chat_views.twilio_webhook, name='twilio_webhook'),
    path('messages/', chat_views.list_sms_messages, name='messages_list'),
    path('compose-message/', chat_views.compose_message, name='compose_message'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    
    path('make-call/', chat_views.make_call, name='make_call'),
    path('twiml/', chat_views.twiml_response, name='twiml_response'),
    path('twiml_app/', chat_views.twiml_app, name='twiml_app'),
    path('generate_token/', chat_views.generate_token, name='generate_token'),

    path('sms/receive/', chat_views.receive_sms, name='receive_sms'),
    path('twilio/call/', chat_views.answer, name='twilio_incoming_call'),
    path('handle_call/', chat_views.handle_call, name='handle_call'),

    path('incoming_call_page/', chat_views.incoming_call_page, name='incoming_call_page'),
    path('handle_user_input/', chat_views.handle_user_input, name='handle_user_input'),

    path('update_preferences/', chat_views.update_preferences, name='update_preferences'),
    path('handle_incoming_call/', chat_views.handle_incoming_call, name='handle_incoming_call'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)