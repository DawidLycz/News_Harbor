from django import forms 
from .models import Article, Image, Paragraph
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm, PasswordChangeForm
from django.contrib.auth.models import User

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'custom-form-field'
        self.fields['password'].widget.attrs['class'] = 'custom-form-field'


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label='Email', required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'custom-form-field'
        self.fields['username'].label = 'Login'
        self.fields['username'].help_text = ''

        self.fields['email'].widget.attrs['class'] = 'custom-form-field'

        self.fields['password1'].widget.attrs['class'] = 'custom-form-field'
        self.fields['password1'].label = 'Password'
        self.fields['password1'].help_text = ''

        self.fields['password2'].widget.attrs['class'] = 'custom-form-field'
        self.fields['password2'].label = 'Confirm Password'
        self.fields['password2'].help_text = ''

class CustomUserEditForm(UserChangeForm):

    password = None
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['class'] = 'custom-form-field'
        self.fields['last_name'].widget.attrs['class'] = 'custom-form-field'
        self.fields['email'].widget.attrs['class'] = 'custom-form-field'

class CustomPasswordChangeForm(PasswordChangeForm):

    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs['class'] = 'custom-form-field'
        self.fields['old_password'].help_text = ''
        self.fields['new_password1'].widget.attrs['class'] = 'custom-form-field'
        self.fields['new_password1'].help_text = ''
        self.fields['new_password2'].widget.attrs['class'] = 'custom-form-field'