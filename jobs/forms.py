from django import forms
from .models import Job, JobCategory

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company', 'description', 'location', 'salary_range', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_salary_range(self):
        salary_range = self.cleaned_data.get('salary_range')
        # 验证薪资范围格式
        if not salary_range:
            raise forms.ValidationError('请输入薪资范围')
        if 'k' not in salary_range.lower():
            raise forms.ValidationError('请使用"k"作为薪资单位，例如：15k-25k')
        return salary_range

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 50:
            raise forms.ValidationError('职位描述太短，请至少输入50个字符')
        return description