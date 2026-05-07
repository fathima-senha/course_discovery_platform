from django import forms
from .models import Course, Category, Tag
 
 
class CourseForm(forms.ModelForm):
    """
    Form for providers to create and edit courses.
    """
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
 
    class Meta:
        model  = Course
        fields = [
            'title', 'short_description', 'description',
            'thumbnail', 'price', 'discount_price', 'is_free',
            'level', 'duration_hours', 'duration_weeks',
            'language', 'categories', 'tags',
        ]
        widgets = {
            'description':       forms.Textarea(attrs={'rows': 6}),
            'short_description': forms.Textarea(attrs={'rows': 3}),
        }