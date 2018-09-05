from django import forms
from django.contrib.auth.models import User
from .models import Order, Price

Shares = Price.objects.values_list('share_name', flat=True)

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['share_name', 'quantity', 'price']

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        s = [(x,x) for x in Shares]
        self.fields['share_name'].widget = forms.Select(choices=s)


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'password']



