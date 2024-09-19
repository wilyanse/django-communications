# forms.py
from django import forms
from .models import CallPreference

class MessageForm(forms.Form):
    phone_number = forms.CharField(max_length=15, label="Phone Number")
    message = forms.CharField(widget=forms.Textarea, label="Message")
    media_url = forms.URLField(required=False, label="Media URL", help_text="Optional: URL of the media to send (e.g., image, video)")

class CallForm(forms.Form):
    phone_number = forms.CharField(label='Phone Number', max_length=15)

class CallPreferenceForm(forms.ModelForm):
    class Meta:
        model = CallPreference
        fields = ['auto_accept_calls', 'accept_message', 'reject_message']
