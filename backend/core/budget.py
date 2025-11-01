"""
Budget tracking and guardrail system.

This module provides budget tracking functionality to monitor and enforce
cost limits for OpenAI API usage. It tracks token usage and calculates costs
based on model pricing.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

from structlog import get_logger

from ..config import get_settings
from .exceptions import BudgetExceededError

logger = get_logger(__name__)


# OpenAI model pricing (USD per 1M tokens) as of 2024
# Format: {model_name: {"input": price_per_1M_input_tokens, "output": price_per_1M_output_tokens}}
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4-turbo-preview": {"input": 10.0, "output": 30.0},
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-32k": {"input": 60.0, "output": 120.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "gpt-3.5-turbo-16k": {"input": 3.0, "output": 6.0},
}


class BudgetTracker:
    """
    Tracks budget usage and enforces limits.

    This class tracks token usage and calculates costs for OpenAI API calls.
    It maintains daily and per-task budgets and raises exceptions when limits
    are exceeded.

    Attributes:
        daily_costs: Dictionary mapping dates to total costs
        task_costs: Dictionary mapping task IDs to costs
        total_tokens: Total tokens used across all requests
        lock: Async lock for thread-safe operations
    """

    def __init__(self):
        """Initialize budget tracker with empty state."""
        self.daily_costs: Dict[str, float] = {}
        self.task_costs: Dict[str, float] = {}
        self.total_tokens: Dict[str, int] = {"input": 0, "output": 0}
        self.lock = asyncio.Lock()
        self.settings = get_settings()

    def _get_today_key(self) -> str:
        """
        Get today's date as a string key.

        Returns:
            Date string in YYYY-MM-DD format.
        """
        return datetime.now().date().isoformat()

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Calculate cost for a given model and token usage.

        Args:
            model: OpenAI model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD

        Raises:
            ValueError: If model pricing is not available
        """
        pricing = MODEL_PRICING.get(model)
        if not pricing:
            logger.warning(
                "Unknown model pricing, using default",
                model=model,
                default_pricing="gpt-4-turbo-preview",
            )
            pricing = MODEL_PRICING["gpt-4-turbo-preview"]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    async def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_id: Optional[str] = None,
    ) -> float:
        """
        Record token usage and calculate cost.

        Args:
            model: OpenAI model name
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            task_id: Optional task ID for per-task tracking

        Returns:
            Cost in USD for this usage

        Raises:
            BudgetExceededError: If budget limits are exceeded
        """
        if not self.settings.budget.enable_tracking:
            return 0.0

        cost = self._calculate_cost(model, input_tokens, output_tokens)

        async with self.lock:
            # Update daily costs
            today = self._get_today_key()
            self.daily_costs[today] = self.daily_costs.get(today, 0.0) + cost

            # Update task costs
            if task_id:
                self.task_costs[task_id] = self.task_costs.get(task_id, 0.0) + cost

            # Update total tokens
            self.total_tokens["input"] += input_tokens
            self.total_tokens["output"] += output_tokens

            # Check daily budget
            daily_total = self.daily_costs[today]
            if daily_total > self.settings.budget.daily_limit:
                raise BudgetExceededError(
                    f"Daily budget limit exceeded: ${daily_total:.2f} > ${self.settings.budget.daily_limit:.2f}",
                    current_cost=daily_total,
                    limit=self.settings.budget.daily_limit,
                    limit_type="daily",
                )

            # Check task budget
            if task_id:
                task_total = self.task_costs[task_id]
                if task_total > self.settings.budget.task_limit:
                    raise BudgetExceededError(
                        f"Task budget limit exceeded: ${task_total:.2f} > ${self.settings.budget.task_limit:.2f}",
                        current_cost=task_total,
                        limit=self.settings.budget.task_limit,
                        limit_type="task",
                        context={"task_id": task_id},
                    )

            # Check warning threshold
            daily_warning_threshold = (
                self.settings.budget.daily_limit * self.settings.budget.warning_threshold
            )
            if daily_total >= daily_warning_threshold:
                logger.warning(
                    "Daily budget approaching limit",
                    daily_cost=daily_total,
                    limit=self.settings.budget.daily_limit,
                    threshold=daily_warning_threshold,
                )

        logger.debug(
            "Token usage recorded",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            task_id=task_id,
        )

        return cost

    async def get_daily_cost(self, date: Optional[str] = None) -> float:
        """
        Get total cost for a specific date.

        Args:
            date: Date string in YYYY-MM-DD format. If None, uses today.

        Returns:
            Total cost for the date in USD
        """
        if not date:
            date = self._get_today_key()
        return self.daily_costs.get(date, 0.0)

    async def get_task_cost(self, task_id: str) -> float:
        """
        Get total cost for a specific task.

        Args:
            task_id: Task identifier

        Returns:
            Total cost for the task in USD
        """
        return self.task_costs.get(task_id, 0.0)

    async def get_total_tokens(self) -> Dict[str, int]:
        """
        Get total token usage.

        Returns:
            Dictionary with 'input' and 'output' token counts
        """
        return self.total_tokens.copy()

    async def reset_daily_budget(self) -> None:
        """
        Reset daily budget tracking.

        This method clears old daily cost entries (older than 7 days)
        to prevent memory bloat.
        """
        async with self.lock:
            cutoff_date = datetime.now().date() - timedelta(days=7)
            cutoff_key = cutoff_date.isoformat()

            self.daily_costs = {
                k: v for k, v in self.daily_costs.items() if k >= cutoff_key
            }


# Global budget tracker instance
_budget_tracker: Optional[BudgetTracker] = None


def get_budget_tracker() -> BudgetTracker:
    """
    Get the global budget tracker instance.

    Returns:
        BudgetTracker: Singleton budget tracker instance

    This function creates a singleton instance of BudgetTracker that is
    shared across the entire application.
    """
    global _budget_tracker
    if _budget_tracker is None:
        _budget_tracker = BudgetTracker()
    return _budget_tracker

