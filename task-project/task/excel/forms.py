from django import forms
from .models import Cards,CARD_STATUS
from .utils import *


class CardAdminForms(forms.ModelForm):
    class Meta:
        model = Cards
        fields = "__all__"

    def clean_card_number(self):
        card_number_data = self.cleaned_data.get('card_number')
        print(f"DEBUG FORM: clean_card_number received: '{card_number_data}'") 
        if card_number_data:
            try:
                cleaned_number = validate_UZB_card_numbers(card_number_data)
                print(f"DEBUG : clean_card_number returning valid: '{cleaned_number}'") 
                return cleaned_number 
            except ValueError as e:
                print(f"DEBUG: ValidationError in clean_card_number: {e}") 
                raise forms.ValidationError(str(e)) 
            except Exception as e:
                print(f"DEBUG : Unexpected error in clean_card_number: {e}") 
                raise forms.ValidationError(f"An unexpected error occurred during card number validation: {e}")
        print(f"DEBUG : clean_card_number returning original (empty): '{card_number_data}'") 
        return card_number_data 

    def clean_expire(self):
        expire_data = self.cleaned_data.get('expire')
        print(f"Expire data has been received: '{expire_data}'")
        if expire_data:
            try:
                sorted_expire_data = expire_date_sorting(expire_data)
                print(f"DEBUG FORM: Parsed expiry date object: {sorted_expire_data} (type={type(sorted_expire_data)})")

                self.cleaned_data['_sorted_expiry_date'] = sorted_expire_data

                final_return_value = sorted_expire_data.strftime("%m/%y")
                print(f"DEBUG FORM: clean_expire - card_status in cleaned_data AFTER validate_card_expiry: {self.cleaned_data.get('card_status')}")
                return final_return_value
            except ValueError as e:
                print(f"DEBUG: Value error caught in clean_expire: {e}")
                raise forms.ValidationError(str(e))
            except Exception as e:
                print(f"DEBUG FORM: General Exception caught in clean_expire: {e}") 
                raise forms.ValidationError(f"An unexpected error occurred during expiry date validation: {e}")
        return expire_data  


 
    def clean_phone_number(self):
        phone_number_data = self.cleaned_data.get('phone_number')
        print(f"The phone number has been received. {phone_number_data}")

        if phone_number_data:
            try:
                clean_phone = phone_number(phone_number_data)
                if clean_phone:
                    print(f"DEBUG: Phone number has been cleaned. Validating the phone number...")
                    is_uzbek = validate_UZB_phone_number(clean_phone)
                    if is_uzbek:
                        print(f"DEBUG: This phone number:{clean_phone} is uzbekistan phone number.")
                        return clean_phone
                    print(f"DEBUG: {clean_phone} phone number is not uzbekistan number or either has incorrect format.")
            except ValueError as e:
                raise forms.ValidationError(str(e))
    def clean(self):
        cleaned_data = super().clean()
        print(f"DEBUG FORM: In clean() method - Initial cleaned_data (after super().clean()): {cleaned_data}")
        
       
        sorted_expiry_date_obj = self.cleaned_data.get('_sorted_expiry_date')
        
        if sorted_expiry_date_obj:
            validate_card_expiry(sorted_expiry_date_obj, cleaned_data)
            
          
            del self.cleaned_data['_sorted_expiry_date']
            
        print(f"DEBUG FORM: In clean() method - final card_status in cleaned_data: {cleaned_data.get('card_status')}")
        
        return cleaned_data

       

