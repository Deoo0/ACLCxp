from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import Participation, Activity, House_Cup_Year, House, Score

admin.site.register(House_Cup_Year)
admin.site.register(House)
admin.site.register(Score)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['name', 'activity_type', 'date', 'status', 'points_distribution_preview']
    list_filter = ['activity_type', 'status', 'house_cup_year']
    actions = ['fix_points_distribution']
    
    def fix_points_distribution(self, request, queryset):
        for activity in queryset:
            activity.save()  # This will trigger the fixed save method
        self.message_user(request, f"Fixed points distribution for {queryset.count()} activities.")
    fix_points_distribution.short_description = "Fix points distribution"
    
    def points_distribution_preview(self, obj):
        if obj.points_distribution:
            return ", ".join([f"{k}: {v}" for k, v in sorted(obj.points_distribution.items())])
        return "Not set"
    points_distribution_preview.short_description = "Points Distribution"
    
class ParticipationAdminForm(forms.ModelForm):
    # Simple text area for quick participant entry
    participants_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Enter one participant per line:\nJohn Doe - Grade 10 (Captain)\nJane Smith - Grade 11\nBob Johnson - Grade 10'
        }),
        help_text="Enter one participant per line. Add '(Captain)' to mark team captain."
    )
    
    class Meta:
        model = Participation
        fields = '__all__'

@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    form = ParticipationAdminForm
    list_display = ['activity', 'house', 'status', 'participant_count', 'team_captain', 'registered_at']
    list_filter = ['status', 'activity', 'house']
    readonly_fields = ['participant_list_display']
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('activity', 'house', 'status', 'team_name')
        }),
        ('Team Management', {
            'fields': ('participants_text', 'participant_list_display')
        }),
        ('Administration', {
            'fields': ('confirmed_by', 'confirmed_at'),  # REMOVED: registered_at
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Process participants_text into JSON data
        participants_text = form.cleaned_data.get('participants_text', '')
        if participants_text:
            obj.participants = self.parse_participants_text(participants_text)
        
        super().save_model(request, obj, form, change)
    
    def parse_participants_text(self, text):
        """Convert text input to structured JSON"""
        participants = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            participant = {'name': line}
            
            # Simple parsing logic
            if '(Captain)' in line or '(captain)' in line:
                participant['is_captain'] = True
                participant['name'] = participant['name'].replace('(Captain)', '').replace('(captain)', '').strip()
            
            if 'Grade' in line:
                # Extract grade: "John Doe - Grade 10" → grade 10
                import re
                grade_match = re.search(r'Grade\s*(\d+)', line)
                if grade_match:
                    participant['grade'] = grade_match.group(1)
                    participant['name'] = re.sub(r'\s*-\s*Grade\s*\d+', '', participant['name']).strip()
            
            participants.append(participant)
        
        return participants
    
    def participant_count(self, obj):
        return len(obj.participants)
    participant_count.short_description = 'Members'
    
    def team_captain(self, obj):
        captain = obj.captain
        return captain if captain else '—'
    team_captain.short_description = 'Captain'
    
    def participant_list_display(self, obj):
        if not obj.participants:
            return "No participants registered"
        
        html = '<div class="participant-list">'
        for participant in obj.participants:
            captain_badge = ' <span style="color: #eab308;">👑</span>' if participant.get('is_captain') else ''
            grade_info = f" <small>(Grade {participant.get('grade')})</small>" if participant.get('grade') else ''
            html += f'<div style="padding: 4px 0; border-bottom: 1px solid #eee;">{participant["name"]}{grade_info}{captain_badge}</div>'
        html += f'<div style="margin-top: 8px; font-weight: bold;">Total: {len(obj.participants)} participants</div>'
        html += '</div>'
        return format_html(html)
    participant_list_display.short_description = "Current Team Members"
