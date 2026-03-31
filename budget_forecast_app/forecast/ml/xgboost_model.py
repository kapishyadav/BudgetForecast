import xgboost as xgb
from .tree_model import TreeForecaster


class XGBoostForecaster(TreeForecaster):

    def _format_categorical(self, df, cat_features):
        for col in cat_features:
            df[col] = df[col].astype('category')
        return df

    def _fit_model(self, X_train, y_train, cat_features):
        model = xgb.XGBRegressor(
            n_estimators=int(self.hyperparameters.get('n_estimators', 100)),
            learning_rate=float(self.hyperparameters.get('learning_rate', 0.1)),
            max_depth=int(self.hyperparameters.get('max_depth', 3)),
            objective='reg:squarederror',
            enable_categorical=True,
            tree_method='hist'
        )
        model.fit(X_train, y_train)
        return model