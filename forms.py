from django import forms

class WeeksToCheckForm(forms.Form):
    weeks_to_check=forms.IntegerField(min_value=1)

class WeeksToCheckDropdown(forms.Form):
    weeks_to_check = forms.ChoiceField(choices=[(x, x) for x in range(1, 21)])