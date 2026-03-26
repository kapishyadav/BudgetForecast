
import unittest
from ..dto import CustomScenarioDTO
from ..ml.adapters import MLModelFactory, ProphetAdapter
from ..ml.strategies import ForecastStrategyFactory, OverallAggregateStrategy
from ..ml.enums import ForecastType


class TestDataTransferObjects(unittest.TestCase):

    def test_custom_scenario_dto_validates_fast(self):
        """Ensures DTO blocks bad data before it hits the service layer."""

        # 1. Should raise ValueError because dataset_id is empty
        with self.assertRaisesRegex(ValueError, "dataset_id is required"):
            CustomScenarioDTO(
                dataset_id="",
                model_name="prophet",
                hyperparameters={"changepoint_prior_scale": 0.05}
            )

        # 2. Should raise ValueError because hyperparameters is not a dictionary
        with self.assertRaisesRegex(ValueError, "Hyperparameters must be a JSON dictionary"):
            CustomScenarioDTO(
                dataset_id="123",
                model_name="prophet",
                hyperparameters="this-is-a-string-not-a-dict"  # Invalid type
            )


class TestMLFactories(unittest.TestCase):

    def test_strategy_factory_returns_correct_strategy(self):
        """Ensures the OCP factory routes correctly."""
        strategy = ForecastStrategyFactory.get_strategy(ForecastType.OVERALL_AGGREGATE)
        self.assertIsInstance(strategy, OverallAggregateStrategy)

    def test_ml_model_factory_instantiates_adapters(self):
        """Ensures the adapter pattern generates the right model wrapper."""
        adapter = MLModelFactory.get_model("prophet", hyperparameters={"seasonality_mode": "multiplicative"})

        self.assertIsInstance(adapter, ProphetAdapter)
        self.assertEqual(adapter.hyperparameters["seasonality_mode"], "multiplicative")

    def test_ml_model_factory_rejects_unknown_models(self):
        with self.assertRaisesRegex(ValueError, "Unsupported ML Model"):
            MLModelFactory.get_model("skynet_ai", {})