from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Department

class StudentRegistrationForm(UserCreationForm):
    """
    Form for registering a new student.
    """
    first_name = forms.CharField(max_length=30, required=True)
    middle_name = forms.CharField(max_length=30, required=False, help_text="Optional")
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)
    
    # Custom fields for student
    student_id = forms.CharField(max_length=20, required=True, help_text='Your University/College ID Number')
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True)
    year_of_study = forms.ChoiceField(choices=CustomUser.YEAR_CHOICES, required=True)
    profile_image = forms.ImageField(required=False, help_text="Upload a professional profile picture")

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Enforce exactly this order: first, middle, last
        fields = ('username', 'email', 'first_name', 'middle_name', 'last_name', 'student_id', 'department', 'year_of_study', 'profile_image')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Simplify the messy Django password help text
        if 'password' in self.fields:
            self.fields['password'].help_text = "Your password must be at least 8 characters long."
        # Optional: simplify confirm password text if desired, but usually it's fine.

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_student = True
        user.middle_name = self.cleaned_data.get('middle_name')
        user.department = self.cleaned_data.get('department')
        user.year_of_study = self.cleaned_data.get('year_of_study')
        user.profile_image = self.cleaned_data.get('profile_image')
        if commit:
            user.save()
        return user
class StudentProfileUpdateForm(forms.ModelForm):
    """
    Form for updating existing student profiles.
    """
    middle_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    age = forms.IntegerField(required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    year_of_study = forms.ChoiceField(choices=CustomUser.YEAR_CHOICES, required=False)
    semester = forms.ChoiceField(choices=CustomUser.SEMESTER_CHOICES, required=False)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'middle_name', 'email', 'student_id', 'date_of_birth', 'age', 'department', 'year_of_study', 'semester', 'profile_image')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student Roll ID'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age', 'readonly': 'readonly'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'year_of_study': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['middle_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Middle Name'})


class TeacherProfileUpdateForm(forms.ModelForm):
    """
    Form for updating existing teacher profiles.
    """
    middle_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    subjects = forms.ModelChoiceField(queryset=None, required=False, label="Primary Subject")

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'middle_name', 'email', 'date_of_birth', 'department', 'subjects', 'profile_image')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically set subjects queryset from Course model
        from exams.models import Course
        self.fields['subjects'].queryset = Course.objects.all()
        self.fields['department'].widget.attrs.update({'class': 'form-control'})
        self.fields['subjects'].widget.attrs.update({'class': 'form-control'})
        self.fields['middle_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Middle Name'})

    def save(self, commit=True):
        user = super().save(commit=False)
        # Handle subjects as a single selection for the ManyToMany field
        if commit:
            user.save()
            subject = self.cleaned_data.get('subjects')
            if subject:
                user.subjects.set([subject])
            else:
                user.subjects.clear()
        return user

