from email.policy import default
from enum import unique
from random import choice
from django.contrib.auth.models import User
from django.db import models
from django.db.models.deletion import PROTECT
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


# Create your models here.
class House_Cup_Year(models.Model):
    year = models.DateField()
    season = models.PositiveSmallIntegerField()
    
    def __str__(self):
        return f"{self.year} - Season {self.season}"
    
    class Meta:
        verbose_name = "House Cup Year"
        verbose_name_plural = "House Cup Years"
# class Activity_category(models.Model):
#     name = models.CharField(max_length=255)
#     description = models.TextField(max_length=255)
    
#     def __str__(self):
#         return self.name
#     class Meta:
#         verbose_name = "Activity Category"
#         verbose_name_plural = "Activity Categories"
        
class Activity(models.Model):
    ACTIVITY_TYPE = [
        ('sports', 'Sports'),
        ('esport', 'Esports'),
        ('academics', 'Academics'),
        ('arts', 'Arts'),
        ('other', 'Other'),
    ]
    ACTIVITY_STATUS = [
        ('draft','DRAFT'), 
        ('scheduled','Scheduled'), 
        ('ongoing','Ongoing'), 
        ('completed','Completed'),
        ('cancelled','Cancelled'), 
    ]
    #basic info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    activity_type = models.CharField(max_length=20, choices= ACTIVITY_TYPE)
    house_cup_year = models.ForeignKey(House_Cup_Year, on_delete=models.CASCADE)
    
    #event details
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    organizer = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    #scoring system
    max_points = models.IntegerField(default=100, validators=[MinValueValidator(1)])
    points_distribution = models.JSONField(default=dict, blank=True)
    
    #status
    status = models.CharField(max_length=20, choices= ACTIVITY_STATUS, default= "draft") 
    
    #timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_activity_type_display()})"
    def get_activity_type_color(self):
        color_map={
            'sports':'red',
            'academics':'blue',
            'arts':'yellow',
            'other':'green',
        }
        return color_map.get(self.activity_type, 'gray')
    
    def save(self, *args, **kwargs):
        if not self.points_distribution:
            self.points_distribution = {
                1: self.max_points,
                2: int(self.max_points * 0.8),
                3: int(self.max_points * 0.6),
                4: int(self.max_points * 0.4),
                5: int(self.max_points * 0.2)
            }
        super().save(*args, **kwargs)
        
    def get_points_for_placement(self, placement):
        return self.points_distribution.get(placement, 0)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Activities"

class House(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    #logo
    
    # member_id = 
    
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'House'
        verbose_name_plural = 'Houses'

class Score(models.Model):
    PLACEMENT = [
        (1, '1st'),
        (2, '2nd'),
        (3, '3rd'),
        (4, '4th'),
        (5, '5th')
    ]
    #core ralationship
    activity = models.ForeignKey(Activity, on_delete=PROTECT, related_name='score')
    house = models.ForeignKey(House, on_delete=models.PROTECT, related_name='score')
    
    #scoring details
    points_earned = models.IntegerField(null=True)
    placement = models.IntegerField(choices= PLACEMENT, null = True, blank = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    #additional info
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    #audit fileds
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_scores')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['activity','house']
        ordering = ['-created_at']
        verbose_name = 'Score'
        verbose_name_plural = 'Scores'
        indexes = [
            models.Index(fields=['activity','house']),
            models.Index(fields=['created_at'])
        ]
        
    def __str__(self):
        return f"{self.house.name} - {self.points_earned} pts in {self.activity.name}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.points_earned > self.activity.max_points:
            raise ValidationError("Points earned cannot exceed activity's maximum points")
        
    def save(self, *args, **kwargs):
        # Auto-verify if awarded by admin/staff
        if self.awarded_by and self.awarded_by.is_staff and not self.verified_by:
            self.is_verified = True
            self.verified_by = self.awarded_by
            self.verified_at = timezone.now()
        super().save(*args, **kwargs)
        
