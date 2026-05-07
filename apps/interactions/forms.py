from django import forms
from .models import Review
 
 
class ReviewForm(forms.ModelForm):
    """Form for students to write a course review."""
    class Meta:
        model   = Review
        fields  = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
            'rating':  forms.Select(choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]),
        }