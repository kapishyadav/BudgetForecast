import pandas as pd
import logging
from .llm_providers import BaseLLMProvider
from ..models import HistoricalSpend, ForecastRun

logger = logging.getLogger(__name__)


class PrescriptiveAnalysisService:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    def generate_and_save_insight(self, task_id: str, total_current_spend: float, total_forecast_spend: float,
                                  historical_months: int, forecast_months: int) -> str:
        try:
            prompt = self._construct_finops_prompt(total_current_spend, total_forecast_spend,
                                                   historical_months, forecast_months)
            logger.info(f"[AI_DEBUG] Constructed Prompt:\n{prompt}")

            insight = self.llm_provider.generate_text(prompt)
            logger.info(f"[AI_DEBUG] Service received insight: '{insight}'")

            self._save_to_db(task_id, insight)
            return insight

        except Exception as e:
            logger.error(f"[AI_DEBUG] Insight orchestration failed: {e}")
            return "Prescriptive analysis temporarily unavailable."

    def _construct_finops_prompt(self, total_current_spend: float, total_forecast_spend: float,
                                 historical_months: int, forecast_months: int) -> str:

        total_current_spend_float = float(total_current_spend)
        total_forecast_spend_float = float(total_forecast_spend)

        variance = total_forecast_spend_float - total_current_spend_float
        logger.info(f"DEBUG : total_current_spend : {total_current_spend_float}")
        logger.info(f"DEBUG : total_forecast_spend : {total_forecast_spend_float}")
        logger.info(f"DEBUG : historical_months : {historical_months}")
        logger.info(f"DEBUG : forecast_months : {forecast_months}")

        if variance > 0:
            trend = f"an increase of ${abs(variance):,.2f}"
        else:
            trend = f"a decrease of ${abs(variance):,.2f}"

        return f"""
            System: You are a FinOps expert analyzing cloud infrastructure costs. 
            
            Data:
            - Last {historical_months} Months Spend: ${total_current_spend:.2f}
            - Forecasted Next {forecast_months} Months Spend: ${total_forecast_spend:.2f}
            - Trend: This is {trend} compared to the historical period.
            
            Task: Write a concise, 3-sentence summary for a C-suite executive. State the financial trend and recommend one specific architectural action to optimize the bill.
            
            Summary:
            """

    def _save_to_db(self, task_id: str, insight: str):
        ForecastRun.objects.filter(task_id=task_id).update(prescriptive_insight=insight)