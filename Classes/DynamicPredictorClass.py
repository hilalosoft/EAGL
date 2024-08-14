import joblib
import sklearn


class DynamicPredictor:

    def __init__(self):
        self.model = None
        self.X_train = None
        self.y_train = None
        self.X_test = None
        self.y_test = None

    def fit(self, X_train, y_train):
        self.X_train = X_train
        self.y_train = y_train
        self.model.fit(self.X_train, self.y_train)

    def predict(self, X_test):
        self.X_test = X_test
        return self.model.predict(self.X_test)

    def evaluate(self, X_test, y_test):
        self.X_test = X_test
        self.y_test = y_test
        return self.model.evaluate(self.X_test, self.y_test)

    def set_model(self, model):
        self.model = model

    def load_model(self, path):
        self.model = joblib.load(path)

    def predict_probability(self, element_features):
        return self.model.predict_proba(element_features)

