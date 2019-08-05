import sys
import dill
import json
import requests
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HOST = 'http://0.0.0.0:5000'



class TestModel(object):
    def infer(self, **kwargs):
        """
        Square input keyword arg 'x' and return

        :param float_x: coercable to np.array
        """
        import numpy as np
        return (np.array(kwargs['x']).astype(np.float64)**2).tolist()


def test_args_test(*args, **kwargs):
    """
    - Disallow non-keyword args
    - Require
        :keyword x: coercable to np.array
    - Allow any other keyword args
    """
    if args != ():
        return False
    elif 'x' not in kwargs.keys():
        return False
    else:
        return True


product = {'model' : dill.dumps(TestModel(), protocol=0),
           'args_test' : dill.dumps(test_args_test, protocol=0)}


if __name__ == '__main__':
    """
    Supported commands:
        $ python run test_serveML.py add_product
        $ python run test_serveML.py infer <product_key>
        $ python run test_serveML.py remove_product <product_key>
        $ python run test_serveML.py list_products
    """
    mode = sys.argv[1]

    if mode == 'add_product':
        r = requests.post(url=HOST+'/add_product', data=product)
        print('Server response : {}, {}'.format(r.status_code, r.reason))
        new_product_key = json.loads(r.content)['new_product_key']
        print('Product added. New product key: {} \n'.format(new_product_key))

    elif mode == 'infer':
        product_key = sys.argv[2]

        def test_infer(input, exp_response, i):
            test_data = {'x' : input}

            r = requests.post(
                    url=HOST+'/infer/{}'.format(product_key), data=test_data)

            if r.status_code == 200:
                inference = json.loads(r.content)
                print('Server response {}: {}, {}'.format(i, r.status_code, r.reason))
                print('Test {} data: {}'.format(i+1, test_data))
                print('Expected response {}: {}'.format(i, exp_response))
                print('Actual response {}: {}'.format(i, inference))

                if inference == exp_response:
                    print('Test {} : passed \n'.format(i))
                else:
                    print('Test {} : failed \n'.format(i))

            elif r.status_code == 400:
                msg = json.loads(r.content)['message']
                print 'Test {} response: 400 - {}'.format(i, msg)

        tests = [[[12], [144]], [[6, 8], [36., 64.]], [[-7], [49.]],
                 [[[3, 4], [5, 6]], [[9, 16], [25, 36]]]]
        for i, [input, exp_response] in enumerate(tests):
            test_infer(input, exp_response, i)

    elif mode == 'remove_product':
        product_key = sys.argv[2]
        r = requests.post(url=HOST+'/remove_product/{}'.format(product_key))
        print('Server response : {}, {}'.format(r.status_code, r.reason))
        deleted_product_key = json.loads(r.content)['deleted_product_key']
        print('Deleted product key: {} \n'.format(deleted_product_key))

    elif mode == 'list_products':
        r = requests.post(url=HOST+'/list_products')
        print('Server response : {}, {}'.format(r.status_code, r.reason))
        product_keys = json.loads(r.content)['active_product_keys']
        print 'Active product keys : {}'.format(product_keys)
