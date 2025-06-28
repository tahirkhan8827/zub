
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import os
import io
import random

def user_avatar_path(instance, filename):
    return f'user_{instance.id}/avatar/{filename}'

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        blank=True,
        null=True,
        default=None
    )
    
    def save(self, *args, **kwargs):
        # Delete old avatar when new one is uploaded
        try:
            old = User.objects.get(id=self.id)
            if old.avatar and old.avatar != self.avatar:
                old.avatar.delete(save=False)
        except User.DoesNotExist:
            pass
        
        # Create default avatar with initial if none exists
        if not self.avatar and not kwargs.get('skip_default_avatar', False):
            self.create_default_avatar()
            
        super().save(*args, **kwargs)
    
    def create_default_avatar(self):
        # Create a default avatar with the user's first initial
        size = 200
        bg_color = (
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        )
        
        # Create image
        img = Image.new('RGB', (size, size), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Get initial
        initial = self.get_initials()
        
        # Try to load font
        try:
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Get text size using modern Pillow method
        left, top, right, bottom = draw.textbbox((0, 0), initial, font=font)
        text_width = right - left
        text_height = bottom - top
        
        # Draw initial
        draw.text(
            ((size - text_width) / 2, (size - text_height) / 2),
            initial,
            font=font,
            fill=(255, 255, 255)
        )
        
        # Save to memory
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        file = ContentFile(buffer.getvalue())
        
        # Save to avatar field
        self.avatar.save(f'default_{self.id}.png', file)
    
    def get_initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        elif self.username:
            return self.username[0].upper()
        return "U"
    
    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()
    
    def __str__(self):
        return self.get_full_name() or self.username