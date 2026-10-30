from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class StyledFields:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class LoginForm(StyledFields, AuthenticationForm):
    pass


class SignUpForm(StyledFields, UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
