import pickle

class DummyModel:
    pass

with open('models/age_clock.pkl', 'rb') as f:
    pkg = pickle.load(f)
    print("Keys in pickle:", list(pkg.keys()))
    print("Type of model:", type(pkg["model"]))
    if "model" in pkg:
        model = pkg["model"]
        print("Model attributes:", dir(model))
