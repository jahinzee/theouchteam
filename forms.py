from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,IntegerField
from wtforms.validators import InputRequired


class Enter_Order(FlaskForm):
    message_type = StringField('Message Type', validators=[])
    order_token = IntegerField('Order Token', validators=[])
    client_reference = StringField('Client Reference', validators=[])
    indicator = StringField('Buy/Sell Indicator', validators=[])
    quantity = IntegerField('Quantity', validators=[])
    orderbook_id = IntegerField('Orderbook Identifier', validators=[])
    group = StringField('Group', validators=[])
    price = IntegerField('Price ', validators=[])
    time_in_force = IntegerField('Time in force', validators=[])
    firm_id = IntegerField('Firm ID', validators=[])
    display = StringField('Display', validators=[])
    capacity = StringField('Capacity', validators=[])
    minimum_quantity = IntegerField('Minimum Quantity', validators=[])
    order_classification = StringField('Order Classification', validators=[])
    cash_margin_type = StringField('Cash Margin Type', validators=[])
    submit = SubmitField('Submit')

class Replace_Order(FlaskForm):
    message_type = StringField('Message Type', validators=[InputRequired()])
    existing_order_token = IntegerField('Existing Order Token', validators=[])
    replacement_order_token = IntegerField('Replacement Order Token', validators=[])
    quantity = IntegerField('Quantity', validators=[])
    price = IntegerField('Price', validators=[])
    time_in_force = IntegerField('Time in force', validators=[])
    display = StringField('Display', validators=[InputRequired()])
    minimum_quantity = IntegerField('Minimum Quantity', validators=[])
    submit = SubmitField('Submit')

class Cancel_Order(FlaskForm):
    message_type = StringField('Message Type', validators=[InputRequired()])
    order_token = IntegerField('Order Token', validators=[])
    quantity = IntegerField('Quantity', validators=[])
    submit = SubmitField('Submit')

class Submit_Order(FlaskForm):
    submit = SubmitField('Submit your Order')
