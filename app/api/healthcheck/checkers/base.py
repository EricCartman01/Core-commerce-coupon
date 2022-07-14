class Base:
    def __init__(self, name="Checker Name"):
        self.name = name

    async def check(self, session=None):
        raise NotImplementedError
