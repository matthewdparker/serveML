from os import listdir, remove
from os.path import isfile, join
import dill

from flask import Flask, request, jsonify, abort

import logging
logger = logging.getLogger(__name__)


# Initialize values and create the Flask app
save_dir = '' # Directory models and args_tests from products will be saved to
next_product_key = 1
models = {}
args_tests = {}
load_from_dir = True
app = Flask(__name__)


def sync_product_keys():
    """
    Checks to make sure keys for models and args_tests dicts are kept in sync
    """
    if set(models.keys()) != set(args_tests.keys()):
        raise RuntimeError("Product keys for models and args_tests are mis-matched; there exist product keys for models which are not product keys for args tests, or vice versa")

    next_product_key = max(models.keys()+[1])


def save_product(product_key, model, args_test):
    """
    Save a product's model and args_test to disk
    """
    sync_product_keys()

    model_fp = save_dir + '{}_model.pkl'.format(product_key)
    args_test_fp = save_dir + '{}_argstest.pkl'.format(product_key)

    for (obj, fp) in [(model, model_fp), (args_test, args_test_fp)]:
        if not isfile(fp):
            with open(fp, 'w') as f:
                dill.dump(obj, f)


@app.before_first_request
def load_products():
    """
    Load any products which have already been saved to save_dir
    """
    files = [f for f in listdir(save_dir) if isfile(join(save_dir, f))]

    for f in files:
        if f[-9:] == 'model.pkl':
            with open(f, 'r') as f_:
                models[int(f.split('_')[0])] = dill.load(f_)

        elif f[-12:] == 'argstest.pkl':
            with open(f, 'r') as f_:
                args_tests[int(f.split('_')[0])] = dill.load(f_)

    sync_product_keys()


@app.route('/<product_key>', methods=['POST'])
def serve_request(product_key):
    """
    Serves a POST request for inference from a model, indexed by product_key

    :param product_key: integer identifying which model and args_test to use
    """
    model, args_test = models[product_key], args_tests[product_key]

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
    sync_product_keys()

    data = request.json
    models[next_product_key] = dill.loads(data['model'])
    args_tests[next_product_key] = dill.loads(data['args_test'])

    sync_product_keys()
    save_product()

    return jsonify({'new_product_key' : new_product_key})


@app.route('/remove_product/{product_key}', methods=['POST'])
def remove_product(product_key):
    """
    Remove a product from the API. Deletes from both memory and disk.
    """
    sync_product_keys()

    if product_key not in models.keys():
        abort(400)

    else:
        # Delete model and args_test from memory
        del models[product_key]
        del args_tests[product_key]

        # Delete model and args_test from disk
        remove(save_dir + '{}_model.pkl'.format(product_key))
        remove(save_dir + '{}_argstest.pkl'.format(product_key))

        sync_product_keys()
        return jsonify({'deleted_product_key' : product_key})


# start the flask app, allow remote connections
app.run(host='0.0.0.0', port=5000, debug=True)
