from catboost import CatBoostRegressor
from .tree_model import TreeForecaster


class CatBoostForecaster(TreeForecaster):

    def _format_categorical(self, df, cat_features):
        for col in cat_features:
            df[col] = df[col].fillna('Unknown').astype(str)
        return df

    def _fit_model(self, X_train, y_train, cat_features):
        model = CatBoostRegressor(
            iterations=int(self.hyperparameters.get('n_estimators', 100)),
            learning_rate=float(self.hyperparameters.get('learning_rate', 0.1)),
            depth=int(self.hyperparameters.get('max_depth', 6)),
            verbose=False
        )
        model.fit(X_train, y_train, cat_features=cat_features)
        return model
