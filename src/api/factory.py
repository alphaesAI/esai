from ..util import Resolver

class APIFactory:
    @staticmethod
    def get(api):
        return Resolver()(api)

    @staticmethod
    def create(config, api):
        return APIFactory.get(api)(config)