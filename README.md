# serveML
Flask app designed for serving pretrained ML models. To launch `serveML`:
1. `cd` to `serveML` directory
2. run: `docker build --tag serve-ml .`
3. run: `docker run -p 5000:5000 serve-ml`


**Note:** when dill serializes an object the serialization seems to end at when the
definition of the object does; in particular, an object which uses import
statements or functions which are defined outside of that object will fail to
perform properly.

One workaround is to import within the definition of the object,
and define functions within the context of the object (or assign them to
attributes, in the case of a class definition).
