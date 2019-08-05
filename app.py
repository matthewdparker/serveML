import os
from os import listdir, remove
from os.path import isfile, join
import dill

from flask import Flask, request, jsonify, abort, make_response

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Initialize values and create the Flask app
save_dir = '/src/products/' # Location Docker will find products
next_product_key = 1
products = {}
load_from_dir = True
app = Flask(__name__)


def save_product(product_key, product):
    """
    Save a product to disk
    """
    product_fp = save_dir + 'product_{}.pkl'.format(product_key)

    if not isfile(product_fp):
        with open(product_fp, 'w') as f:
            dill.dump(products[product_key], f)


@app.errorhandler(400)
def custom400(error):
    return make_response(jsonify({'message': error.description}), 400)


@app.before_first_request
def load_products():
    """
    Load any products which have already been saved to save_dir
    """
    global products, next_product_key

    files = [f for f in listdir(save_dir) if isfile(join(save_dir, f)) \
             and f.split('_')[0] == 'product']

    # Extract keys now so we can sort files by keys later to load in order
    files_and_keys = [[f, int(f.split('_')[1].split('.')[0])] for f in files]

    if files_and_keys:
        for f, product_key in sorted(files_and_keys, key=lambda x: x[1]):
            with open(save_dir + f, 'r') as f_:
                products[product_key] = dill.load(f_)
            logger.info("Loaded product {} from disk".format(product_key))

        next_product_key = max(products.keys()) + 1


@app.route('/add_product', methods=['POST'])
def add_product():
    """
    Add a new product to the API. Adds to memory, and saves to disk.

    Request body should contain keys 'model' and 'args_test', which are
    dill-dumped strings of the new model to be used for inference in the new
    data product, and the (boolean) args_test function which will be called on
    all requests for model inference to determine validity of request args.

    Note: args_test should support keyword-args only.

    Required body keywords:
        :param model: model object to be used in serving future product requests
        :type model: str (dill-encoded model)
        :param args_test: args_test function to be used in validating requests
        :type args_test: str (dill-encoded function)
    """
    global products, next_product_key

    data = request.form
    new_product = {'model' : dill.loads(data['model']),
                   'args_test' : dill.loads(data['args_test'])}

    # Save new product to memory and disk
    new_product_key = next_product_key
    products[new_product_key] = new_product
    save_product(new_product_key, new_product)

    next_product_key += 1

    return jsonify({'new_product_key' : new_product_key})


@app.route('/infer/<product_key>', methods=['POST'])
def infer(product_key):
    """
    Serves a POST request for inference from a model, indexed by product_key

    :param product_key: integer identifying which model and args_test to use
    """
    product_key_ = int(product_key)
    global products

    if product_key_ in products.keys():

        model = products[product_key_]['model']
        args_test = products[product_key_]['args_test']

        if args_test(**request.form):
            return jsonify(model.infer(**request.form))

        else:
            abort(400, "Inference args failed to meet test standards")
    else:
        abort(400, "Product not found")


@app.route('/remove_product/<product_key>', methods=['POST'])
def remove_product(product_key):
    """
    Remove a product from the API. Deletes from both memory and disk.
    """
    global products
    product_key = int(product_key)

    if product_key not in products.keys():
        abort(400, "Product not found")

    else:
        # Delete product from memory and disk
        del products[product_key]

        f = save_dir + 'product_{}.pkl'.format(product_key)
        if isfile(f):
            remove(f)

        return jsonify({'deleted_product_key' : product_key})


@app.route('/list_products', methods=['POST'])
def list_products():
    return jsonify({'active_product_keys' : products.keys()})


# start the flask app, allow remote connections
app.run(host='0.0.0.0', port=5000, debug=True)
