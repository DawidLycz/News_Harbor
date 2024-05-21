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


class CustomEditorCreationForm(UserCreationForm):
    email = forms.EmailField(label='Email', required=False)
    is_editor = forms.BooleanField(label='Is Editor', required=False, widget=forms.CheckboxInput(attrs={'style': 'width:100%'}))
    is_editor_in_chief = forms.BooleanField(label='Is Editor in Chief', required=False, widget=forms.CheckboxInput(attrs={'style': 'width:100%'}))


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

class ImageRenameForm(forms.ModelForm):

    class Meta:
        model = Image
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['class'] = 'custom-form-field'

class ImageAssignForm(forms.ModelForm):

    class Meta:
        model = Image
        fields = ['articles']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['articles'].widget.attrs['class'] = 'custom-form-field'

class ImageCreateForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['photo']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].widget.attrs['class'] = 'custom-form-field'


class ArticleEditForm(forms.Form):
    title = forms.CharField(max_length=255)
    paragraphs = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paragraphs'].label = 'Paragraphs'

    def save(self, article):
        article.title = self.cleaned_data['title']
        article.save()

        paragraphs_data = self.cleaned_data['paragraphs'].split('\n')
        paragraphs = article.paragraphs.all()
        for i, paragraph_data in enumerate(paragraphs_data):
            if i < len(paragraphs):
                paragraph = paragraphs[i]
            else:
                paragraph = Paragraph(article=article)
            paragraph.text = paragraph_data.strip()
            paragraph.save()

        if len(paragraphs) > len(paragraphs_data):
            paragraphs.filter(id__gt=len(paragraphs_data)).delete()