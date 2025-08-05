class Resolver:
    def __call__(self, path):
        parts = path.split(".")         # ["esai", "pipeline", "data", "tabular", "Tabular"]
        module = ".".join(parts[:-1])   # "esai.pipeline.data.tabular"
        m = __import__(module)          # import esai.pipeline.data.tabular  but m = esai, we need a class so,
        for comp in parts[1:]:
            m = getattr(m, comp)        # m = esai // m = esai.pipeline // m = esai.pipeline.data ...
        
        return m                        # <class 'esai.pipeline.data.tabular.Tabular'>