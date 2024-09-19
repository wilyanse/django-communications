# models.py
from django.db import models
from django.contrib.auth.models import User

class ChatRoom(models.Model):
    user1 = models.ForeignKey(User, related_name='chat_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='chat_user2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat between {self.user1.username} and {self.user2.username}"

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)  # Message content can be empty if only attachment
    timestamp = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='attachments/', null=True, blank=True)  # New attachment field

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

class TextMessage(models.Model):
    from_number = models.CharField(max_length=15)
    body = models.TextField()
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.from_number} at {self.received_at}"

class SMSMessage(models.Model):
    from_number = models.CharField(max_length=20)
    message_body = models.TextField()
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'From {self.from_number}: {self.message_body[:50]}'

class CallPreference(models.Model):
    auto_accept_calls = models.BooleanField(default=False)
    accept_message = models.CharField(max_length=255, blank=True)
    reject_message = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Auto accept: {self.auto_accept_calls}, Accept message: {self.accept_message}, Reject message: {self.reject_message}"
