from email.policy import default
from enum import auto, unique
from random import choice
from tkinter import CASCADE
from turtle import update
from django.contrib.auth.models import User
from django.db import models
from django.db.models.deletion import PROTECT
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


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
    
    def clean(self):
        """Validate the model before saving"""
        # Ensure max_points is positive
        if self.max_points < 1:
            raise ValidationError({'max_points': 'Max points must be at least 1'})
    
    def save(self, *args, **kwargs):
        # Ensure points_distribution is always set and complete
        if not self.points_distribution:
            self.points_distribution = self.get_default_points_distribution()
        else:
            # Ensure all placements 1-5 exist
            default_distribution = self.get_default_points_distribution()
            for placement in range(1, 6):
                if placement not in self.points_distribution:
                    self.points_distribution[placement] = default_distribution[placement]
        
        # Ensure points_distribution values are integers
        self.points_distribution = {
            int(k): int(v) for k, v in self.points_distribution.items()
        }
        
        super().save(*args, **kwargs)
    
    def get_default_points_distribution(self):
        """Return the default points distribution"""
        return {
            1: self.max_points,
            2: int(self.max_points * 0.8),
            3: int(self.max_points * 0.6),
            4: int(self.max_points * 0.4),
            5: int(self.max_points * 0.2)
        }
    
    def get_points_for_placement(self, placement):
        """Safe method to get points for placement"""
        if not self.points_distribution:
            self.save()  # Force creation of points_distribution
        return self.points_distribution.get(int(placement), 0)
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

class Participation(models.Model):
    PARTICIPATION_STATUS = [
        ('registered', 'Registered'),
        ('confirmed', 'Confirmed'),
        ('participated', 'Participated'),
        ('absent', 'Absent'),
        ('disqualified', 'Disqualified'),
    ]
    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='participations')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='participations')
    status = models.CharField(max_length=20, choices=PARTICIPATION_STATUS, default='registered')
    team_name = models.CharField(max_length=100, blank=True)
    
    # ENHANCED: Store as list of dictionaries for more flexibility
    participants = models.JSONField(
        default=list, 
        blank=True,
        help_text="Store as: [{'name': 'John Doe', 'grade': '10', 'is_captain': true}]"
    )
    
    registered_at = models.DateTimeField(auto_now_add=True)
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['activity', 'house']
        verbose_name = "Participation"
        verbose_name_plural = "Participations"
    
    def __str__(self):
        return f"{self.house.name} in {self.activity.name}"
    
    # ENHANCED: Helper methods
    @property
    def participant_count(self):
        return len(self.participants)
    
    @property
    def captain(self):
        """Get team captain"""
        for participant in self.participants:
            if participant.get('is_captain', False):
                return participant['name']
        return None
    
    @property
    def participant_names(self):
        """Get just the names as a list"""
        return [p['name'] for p in self.participants if 'name' in p]
    
    def add_participant(self, name, grade=None, is_captain=False):
        """Add a participant to the team"""
        participant_data = {'name': name.strip()}
        if grade:
            participant_data['grade'] = grade
        if is_captain:
            participant_data['is_captain'] = True
        
        # Remove captain status from others if this is captain
        if is_captain:
            for p in self.participants:
                p['is_captain'] = False
        
        self.participants.append(participant_data)
        self.save()
    
    def remove_participant(self, name):
        """Remove a participant by name"""
        self.participants = [p for p in self.participants if p['name'] != name]
        self.save()
class Score(models.Model):
    PLACEMENT = [
        (1, '1st'),
        (2, '2nd'),
        (3, '3rd'),
        (4, '4th'),
        (5, '5th')
    ]
    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='scores')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='scores')
    participation = models.ForeignKey(Participation, on_delete=models.CASCADE, null= False, related_name="scores")
    placement = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)],
        choices=PLACEMENT,
        help_text="Select the placement (1st, 2nd, 3rd, etc.)"
    )
    points_earned = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        editable=False
    )
    notes = models.TextField(blank=True)
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        """Validate before saving"""
        if self.placement:
            # Ensure activity has points_distribution
            if not self.activity.points_distribution:
                self.activity.save()  # Force creation
            
            # Check if placement exists in distribution, if not, add it
            if self.placement not in self.activity.points_distribution:
                # Auto-create the missing placement
                default_points = self.activity.get_default_points_distribution()
                if self.placement in default_points:
                    self.activity.points_distribution[self.placement] = default_points[self.placement]
                    self.activity.save()
    
    def save(self, *args, **kwargs):
        # Ensure activity has complete points_distribution
        if self.activity:
            if not self.activity.points_distribution:
                self.activity.save()
            else:
                # Check if all placements 1-5 exist
                for placement in range(1, 6):
                    if placement not in self.activity.points_distribution:
                        default_points = self.activity.get_default_points_distribution()
                        self.activity.points_distribution[placement] = default_points[placement]
                        self.activity.save()
        
        # AUTO-CALCULATE points based on placement
        if self.placement:
            # Use default distribution if placement still missing
            if self.placement not in self.activity.points_distribution:
                default_points = self.activity.get_default_points_distribution()
                self.points_earned = default_points.get(self.placement, 0)
            else:
                self.points_earned = self.activity.points_distribution.get(self.placement, 0)
        
        # If no placement specified, ensure points_earned is set
        elif not self.points_earned:
            raise ValidationError('Points earned must be set if no placement is specified')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.placement:
            placement_display = dict(self.PLACEMENT).get(self.placement, f"{self.placement}th")
            return f"{self.house.name} - {placement_display} place in {self.activity.name} ({self.points_earned} pts)"
        else:
            return f"{self.house.name} - {self.points_earned} pts in {self.activity.name}"
    
    class Meta:
        ordering = ['-created_at']
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Score"
        verbose_name_plural = "Scores"
