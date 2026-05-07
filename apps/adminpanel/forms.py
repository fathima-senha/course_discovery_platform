from django import forms
from apps.courses.models import Category, Tag
 
 
class CategoryForm(forms.ModelForm):
    class Meta:
        model  = Category
        fields = ['name', 'description', 'parent', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
 
 
class TagForm(forms.ModelForm):
    class Meta:
        model  = Tag
        fields = ['name']
