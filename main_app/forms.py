from django import forms

from .models import Booking, Group, Purchase, Room


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['item', 'price', 'notes']
        widgets = {
            'item': forms.TextInput(attrs={
                'placeholder': 'e.g. Rice, dish soap, gas cylinder',
                'autofocus': True,
            }),
            'price': forms.NumberInput(attrs={
                'placeholder': 'e.g. 350',
                'min': '0',
                'step': '1',
            }),
            'notes': forms.TextInput(attrs={
                'placeholder': 'Optional — quantity, vendor, etc.',
            }),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['number', 'type', 'rate', 'status']
        widgets = {
            'number': forms.TextInput(attrs={'placeholder': 'e.g. 104', 'autofocus': True}),
            'type': forms.TextInput(attrs={'placeholder': 'e.g. Deluxe, Suite, Standard'}),
            'rate': forms.NumberInput(attrs={'placeholder': 'e.g. 8000', 'min': '0', 'step': '1'}),
        }
        error_messages = {
            'number': {'unique': 'A room with this number already exists.'},
        }


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['guest_name', 'phone', 'room', 'check_in', 'check_out', 'guests']
        widgets = {
            'guest_name': forms.TextInput(attrs={'placeholder': 'Full name', 'autofocus': True}),
            'phone': forms.TextInput(attrs={'placeholder': '03xx-xxxxxxx'}),
            'room': forms.RadioSelect(),
            'check_in': forms.DateInput(attrs={'type': 'date'}),
            'check_out': forms.DateInput(attrs={'type': 'date'}),
            'guests': forms.NumberInput(attrs={'min': '1'}),
        }

    def __init__(self, *args, **kwargs):
        available_rooms = kwargs.pop('available_rooms', None)
        super().__init__(*args, **kwargs)
        if available_rooms is not None:
            self.fields['room'].queryset = available_rooms

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get('check_in')
        check_out = cleaned.get('check_out')
        if check_in and check_out and check_out <= check_in:
            raise forms.ValidationError('Check-out must be after check-in.')
        return cleaned


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['group_name', 'contact', 'phone', 'members', 'rate_per_person', 'check_in', 'check_out', 'rooms']
        widgets = {
            'group_name': forms.TextInput(attrs={'placeholder': 'e.g. Ahmed family, XYZ Tours', 'autofocus': True}),
            'contact': forms.TextInput(attrs={'placeholder': 'Name'}),
            'phone': forms.TextInput(attrs={'placeholder': '03xx-xxxxxxx'}),
            'members': forms.NumberInput(attrs={'min': '1', 'placeholder': 'e.g. 12'}),
            'rate_per_person': forms.NumberInput(attrs={'min': '0', 'step': '1', 'placeholder': 'e.g. 2500'}),
            'check_in': forms.DateInput(attrs={'type': 'date'}),
            'check_out': forms.DateInput(attrs={'type': 'date'}),
            'rooms': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        available_rooms = kwargs.pop('available_rooms', None)
        super().__init__(*args, **kwargs)
        if available_rooms is not None:
            self.fields['rooms'].queryset = available_rooms
        self.fields['rooms'].required = False

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get('check_in')
        check_out = cleaned.get('check_out')
        if check_in and check_out and check_out <= check_in:
            raise forms.ValidationError('Check-out must be after check-in.')
        return cleaned
