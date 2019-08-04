from os import listdir, remove
from os.path import isfile, join
import dill

from flask import Flask, request, jsonify, abort

import logging
logger = logging.getLogger(__name__)


# Initialize values and create the Flask app
save_dir = '' # Directory models and args_tests from products will be saved to
next_product_key = 1
products = {}
load_from_dir = True
app = Flask(__name__)


def save_product(product, product_key):
    """
    Save a product to disk
    """
    product_fp = save_dir + '{}_product.pkl'.format(product_key)

    if not isfile(product_fp):
        with open(product_fp, 'w') as f:
            dill.dump(products[product_key], f)


@app.before_first_request
def load_products():
    """
    Load any products which have already been saved to save_dir
    """
    files = [f for f in listdir(save_dir) if isfile(join(save_dir, f))]

    for f in files:
        if f[-11:] == 'product.pkl':
            with open(f, 'r') as f_:
                products[int(f.split('_')[0])] = dill.load(f_)


@app.route('/<product_key>', methods=['POST'])
def serve_request(product_key):
    """
    Serves a POST request for inference from a model, indexed by product_key

    :param product_key: integer identifying which model and args_test to use
    """
    model = products[product_key]['model']
    args_test = products[product_key]['args_test']

    if args_test(**request.json):
        return model.infer(**request.json)

    else:
        abort(400)


@app.route('/add_product', methods=['POST'])
def add_product():
    """
    Add a new product to the API. Adds to memory, and saves to disk.

    Request body should contain keys 'model' and 'args_test', which are
    dill-dumped strings of the new model to be used for inference in the new
    data product, and the (boolean) args_test function which will be called on
    all requests for model inference to determine validity of request args.

    Note: args_test should support keyword-args only.
    """
    data = request.json
    new_product = {'model' : dill.loads(data['model']),
                   'args_test' : dill.loads(data['args_test'])}

    # Save new product to memory and disk
    products[new_product_key] = new_product
    save_product(new_product_key, new_product)

    return jsonify({'new_product_key' : new_product_key})


@app.route('/remove_product/{product_key}', methods=['POST'])
def remove_product(product_key):
    """
    Remove a product from the API. Deletes from both memory and disk.
    """
    if product_key not in products.keys():
        abort(400)

    else:
        # Delete product from memory and disk
        del products[product_key]
        remove(save_dir + '{}_product.pkl'.format(product_key))

        return jsonify({'deleted_product_key' : product_key})


# start the flask app, allow remote connections
app.run(host='0.0.0.0', port=5000, debug=True)
