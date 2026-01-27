from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

MONTHS_PER_YEAR = 12
CURRENCY_FORMAT = "${x:,.0f}"


@dataclass(frozen=True)
class Budget:
    monthly_income: float
    tax_rate: float
    monthly_expenses: Dict[str, float]  # e.g. {"Rent": 1000, "Food": 2500, ...}

    @property
    def monthly_taxes(self) -> float:
        return self.monthly_income * self.tax_rate

    @property
    def monthly_total_expenses(self) -> float:
        return sum(self.monthly_expenses.values()) + self.monthly_taxes

    @property
    def monthly_savings(self) -> float:
        return self.monthly_income - self.monthly_total_expenses

    @property
    def yearly_income(self) -> float:
        return self.monthly_income * MONTHS_PER_YEAR

    @property
    def yearly_expenses(self) -> float:
        return self.monthly_total_expenses * MONTHS_PER_YEAR

    @property
    def yearly_savings(self) -> float:
        return self.yearly_income - self.yearly_expenses


def _colors_for_categories(categories: List[str]) -> List[str]:
    """Simple rule: Income/Savings = green, everything else = red."""
    positives = {"Income", "Savings"}
    return ["green" if c in positives else "red" for c in categories]


def _plot_bar(ax: plt.Axes, title: str, categories: List[str], amounts: List[float]) -> None:
    colors = _colors_for_categories(categories)
    ax.bar(categories, amounts, color=colors)
    ax.set_title(title)
    ax.set_ylabel("Amount ($)")
    ax.yaxis.set_major_formatter(StrMethodFormatter(CURRENCY_FORMAT))
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.5)

    # Optional: label values on bars
    for i, value in enumerate(amounts):
        ax.text(i, value, f"{value:,.0f}", ha="center", va="bottom", fontsize=9)


def build_plot_data(budget: Budget) -> Tuple[List[str], List[float], List[str], List[float]]:
    monthly_categories = ["Income", *budget.monthly_expenses.keys(), "Taxes"]
    monthly_amounts = [
        budget.monthly_income,
        *budget.monthly_expenses.values(),
        budget.monthly_taxes,
    ]

    yearly_categories = ["Income", "Expenses", "Savings"]
    yearly_amounts = [budget.yearly_income, budget.yearly_expenses, budget.yearly_savings]

    return monthly_categories, monthly_amounts, yearly_categories, yearly_amounts


def main() -> None:
    budget = Budget(
        monthly_income=10_000,
        tax_rate=0.22,
        monthly_expenses={
            "Rent": 1_000,
            "Food": 2_500,
            "Other": 2_000,
        },
    )

    monthly_categories, monthly_amounts, yearly_categories, yearly_amounts = build_plot_data(budget)

    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(10, 6))

    _plot_bar(axs[0], "Monthly Financial Overview", monthly_categories, monthly_amounts)
    axs[0].tick_params(axis="x", rotation=45)

    _plot_bar(axs[1], "Yearly Financial Overview", yearly_categories, yearly_amounts)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
