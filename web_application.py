from flask import Flask, render_template, request, url_for, redirect
from flask_bootstrap import Bootstrap
from forms import Enter_Order, Replace_Order, Cancel_Order, Submit_Order
import threading
import time
import json
from src.client import Client

app = Flask(__name__)
app.secret_key = "abcdefgh"
bootstrap = Bootstrap(app)

mything = 5

order_number_index = 1

normalisedList = []

@app.route("/", methods = ["GET", "POST"])
def home():
    form = Submit_Order()
    if form.validate_on_submit():
        send()
        return render_template("completed.html")
    return render_template('dashboard.html', form=form)

def send():
    outbound = {
        'actions': normalisedList
    }
    with open('test_inputs/client_100.json', 'w') as fp:
        json.dump(outbound, fp)

    Client(path='test_inputs/client_100.json')

def normalise_enter(form_info):
    global normalisedList
    normalised = {
        'message_type': str(form_info['message_type']),
        'order_token': int(form_info['order_token']),
        'client_reference': str(form_info['client_reference']),
        'buy_sell_indicator': str(form_info['indicator']),
        'quantity': int(form_info['quantity']),
        'orderbook_id': int(form_info['orderbook_id']),
        'group': str(form_info['group']),
        'price': float(form_info['price']),
        'time_in_force': int(form_info['time_in_force']),
        'firm_id': int(form_info['firm_id']),
        'display': str(form_info['display']),
        'capacity': str(form_info['capacity']),
        'minimum_quantity': int(form_info['minimum_quantity']),
        'order_classification': str(form_info['order_classification']),
        'cash_margin_type': str(form_info['cash_margin_type'])
    }
    normalisedList.append(normalised)


def normalised_replace(form_info):
    global normalisedList
    normalised = {
        'message_type': str(form_info['message_type']),
        'existing_order_token': int(form_info['existing_order_token']),
        'replacement_order_token': int(form_info['replacement_order_token']),
        'quantity': int(form_info['quantity']),
        'price': float(form_info['price']),
        'time_in_force': int(form_info['time_in_force']),
        'display': str(form_info['display']),
        'minimum_quantity': int(form_info['minimum_quantity']),
    }
    normalisedList.append(normalised)


def normalised_cancel(form_info):
    global normalisedList
    normalised = {
        'message_type': str(form_info['message_type']),
        'order_token': int(form_info['order_token']),
        'quantity': int(form_info['quantity']),
    }
    normalisedList.append(normalised)


@app.route('/enter_order', methods = ['GET', 'POST'])
def enter_order_page():
    global order_number_index
    form = Enter_Order()
    if form.validate_on_submit():
        order_number_index += 1
        form_info = request.form
        normalise_enter(form_info)
        return redirect(url_for('enter_order_page'))

    return render_template('enter.html', form = form, num = order_number_index)

@app.route('/replace_order', methods = ['GET', 'POST'])
def replace_order_page():
    global order_number_index
    form = Replace_Order()
    if form.validate_on_submit():
        order_number_index += 1
        form_info = request.form
        normalised_replace(form_info)
        return redirect(url_for('replace_order_page'))

    return render_template('replace.html', form = form, num = order_number_index)

@app.route('/cancel_order', methods = ['GET', 'POST'])
def cancel_order_page():
    global order_number_index
    form = Cancel_Order()
    if form.validate_on_submit():
        order_number_index +=1
        form_info = request.form
        normalised_cancel(form_info)
        return redirect(url_for('cancel_order_page'))

    return render_template('cancel.html', form = form, num = order_number_index)

@app.route('/dashboard', methods=  ['GET', 'POST'])
def dashboard():
    print("hello")
    return render_template('dashboard.html')


def testing():
    pass


if __name__ == '__main__':
    # a = threading.Thread(target = app.run, daemon=True)
    # b = threading.Thread(target = testing, daemon=True)
    # a.start()
    # b.start()
    app.run(debug=True)
    print("Press enter to exit.")
