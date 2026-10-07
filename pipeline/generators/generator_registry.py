class GeneratorRegistry:
    """Factory registry for registering and instantiating asset generators."""

    _generators = {}

    @classmethod
    def register(cls, archetype: str):
        """Decorator to register a generator class with a specific archetype name."""

        def wrapper(generator_class):
            cls._generators[archetype] = generator_class
            return generator_class

        return wrapper

    @classmethod
    def create(cls, archetype: str, **kwargs):
        """Instantiate an asset generator by its archetype."""
        if archetype not in cls._generators:
            raise ValueError(f"Unknown archetype: {archetype}")
        return cls._generators[archetype](**kwargs)
