from django import forms

"""
These are the forms on the chart page to input how many weeks you want to see
"""

class WeeksToCheckForm(forms.Form):
    """
    Field to type in the integer
    """
    weeks_to_check=forms.IntegerField(min_value=1)

class WeeksToCheckDropdown(forms.Form):
    """
    Field that has a dropdown
    """
    weeks_to_check = forms.ChoiceField(choices=[(x, x) for x in range(1, 21)])