from import_export import fields
from import_export import resources
from .models import Cards,CARD_STATUS
from.utils import(
    card_number,
    phone_number,
    expire_date_sorting,
    balance_sorting,
    card_status,
    validate_card_expiry,
    validate_UZB_card_numbers,
    validate_UZB_phone_number
)
import logging 

logger = logging.getLogger('__name__')


class CardResource(resources.ModelResource):
    class Meta:
        model = Cards
        fields = ("card_number","owner","expire","phone_number","card_status","balance")
        import_id_fields = ('card_number',)


    def before_import_row(self, row, **kwargs):
        print("ROW TYPE:", type(row), "ROW:", row)
        if not isinstance(row, dict):
            dataset_headers = self.get_dataset_headers()
            row = dict(zip(dataset_headers, row))

        # Card number validation
        if row.get('card_number'):
            row['card_number'] = validate_UZB_card_numbers(str(row['card_number']))

        # Balance validation
        if row.get('balance'):
            row['balance'] = balance_sorting(str(row['balance']))


        # Expire date handling
        if row.get('expire'):
            try:

                sorted_expiry = expire_date_sorting(str(row['expire']))
            except ValueError:
                row['card_status'] = 'EXPIRE'
                return row
            validate_card_expiry(sorted_expiry, row)

        # Phone number validation
        if row.get('phone_number'):
            row['phone_number'] = validate_UZB_phone_number(str(row['phone_number']))

        # Return updated row (important!)
        return row