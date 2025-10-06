from django.db import models


# Create your models here.

# class Activity(models.Model):
#     ACTIVITY_TYPE = [
#         ('sports', 'Sports'),
#         ('academic', 'Academic'),
#         ('arts', 'Arts'),
#         ('orther', 'Other'),
#     ]
#     name = models.CharField(max_length=255)
#     activity_type = models.CharField(max_length=20, choices= ACTIVITY_TYPE)
#     date = models.DateTimeField()
#     location = models.CharField(max_length=200)
#     description = models.TextField(black=True)
    
#     def __str__(self):
#         return self.name
    
#     def get_activity_type_color(self):
#         color_map = {
            
#         }
#         return color_map.get(self.activity_type, 'gray')
    
#     class Meta:
#         ordering = ['-date']
#         verbose_name_plural = "Activities"
