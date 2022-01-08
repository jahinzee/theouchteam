from flask import Flask, render_template, request, url_for, redirect
from flask_bootstrap import Bootstrap
from forms import Enter_Order, Replace_Order, Cancel_Order
import requests
import threading
import time
import json
from client import Client

app = Flask(__name__)
app.secret_key = "abcdefgh"
bootstrap = Bootstrap(app)

mything = 5
order_book = {}


@app.route("/")
def home():
    return render_template('dashboard.html', order_book=order_book)

def normalise_enter(form_info):
    normalised = {
        'message_type': str(form_info['message_type']),
        'order_token': int(form_info['order_token']),
        'client_reference': str(form_info['client_reference']),
        'buy_sell_indicator': str(form_info['indicator']),
        'quantity': int(form_info['quantity']),
        'orderbook_id': int(form_info['orderbook_id']),
        'group': str(form_info['group']),
        'price': int(form_info['price']),
        'time_in_force': int(form_info['time_in_force']),
        'firm_id': int(form_info['firm_id']),
        'display': str(form_info['display']),
        'capacity': str(form_info['capacity']),
        'minimum_quantity': int(form_info['minimum_quantity']),
        'order_classification': str(form_info['order_classification']),
        'cash_margin_type': str(form_info['cash_margin_type'])
    }

    outbound = {
        'actions': [normalised]
    }
    with open('test_inputs/client_100.json', 'w') as fp:
        json.dump(outbound, fp)

    Client(path='test_inputs/client_100.json')




@app.route('/enter_order', methods = ['GET', 'POST'])
def enter_order_page():
    form = Enter_Order()
    if form.validate_on_submit():
        form_info = request.form
        print("hello")
        normalise_enter(form_info)
        print("bye")
        return redirect(url_for('dashboard'))

    return render_template('enter.html', form = form, order_book=order_book)

@app.route('/replace_order', methods = ['GET', 'POST'])
def replace_order_page():
    print("this is from server" + str(mything))
    form = Replace_Order()
    if form.validate_on_submit():
        form_info = request.form
        print("hello")
        return redirect(url_for('dashboard'))

    return render_template('replace.html', form = form, order_book=order_book)

@app.route('/cancel_order', methods = ['GET', 'POST'])
def cancel_order_page():
    form = Cancel_Order()
    if form.validate_on_submit():
        form_info = request.form
        print("hello")
        return redirect(url_for('dashboard'))

    return render_template('cancel.html', form = form, order_book=order_book)

@app.route('/dashboard', methods=  ['GET', 'POST'])
def dashboard():
    print("hello")
    return render_template('dashboard.html', order_book=order_book)


def testing():
    pass


if __name__ == '__main__':
    a = threading.Thread(target = app.run)
    b = threading.Thread(target = testing)
    a.start()
    b.start()
    print('hi')