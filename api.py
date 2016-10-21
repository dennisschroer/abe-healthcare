from base64 import b64encode

import bottle
from bottle import route, template, post, request

from shared.implementations.rd13_implementation import RD13Implementation


class EnableCors(object):
    name = 'enable_cors'
    api = 2

    def apply(self, fn, context):
        def _enable_cors(*args, **kwargs):
            # set CORS headers
            bottle.response.headers['Access-Control-Allow-Origin'] = '*'
            bottle.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
            bottle.response.headers[
                'Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

            if bottle.request.method != 'OPTIONS':
                # actual request; reply with the actual response
                return fn(*args, **kwargs)

        return _enable_cors


@route('/')
def index(name):
    return template('Hello world!', name=name)


@route('/attribute_authorities/generate_keys', method=['POST' , 'OPTIONS'])
def attribute_authorities_generate_keys():
    attributes = request.json['attributes'] or []
    attributes = list(map(lambda attribute: "%s@TEST" % attribute, attributes))
    attribute_authority.setup(central_authority, attributes, 1)
    return {
        'attributes': attributes,
        'publicKeys': b64encode(implementation.serializer.serialize_authority_public_keys(attribute_authority.public_keys(1))),
        'secretKeys': b64encode(implementation.serializer.serialize_authority_secret_keys(attribute_authority.secret_keys(1)))
    }

if __name__ == '__main__':
    implementation = RD13Implementation()
    central_authority = implementation.create_central_authority()
    attribute_authority = implementation.create_attribute_authority('TEST')

    central_authority.central_setup()

    app = bottle.app()
    app.install(EnableCors())
    app.run(host='0.0.0.0', port=80)
