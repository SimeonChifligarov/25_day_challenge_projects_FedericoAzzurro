from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple, Union

import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

MONTHS_PER_YEAR = 12
CURRENCY_FORMAT = "${x:,.0f}"

DEFAULT_CONFIG: Dict[str, Any] = {
    "seed": 42,
    "monthly_income": 10_000,
    "tax_rate": 0.22,
    # Each expense can be a fixed number OR a {"min": ..., "max": ...} range.
    "monthly_expenses": {
        "Rent": {"min": 800, "max": 1_500},
        "Food": {"min": 2_000, "max": 3_000},
        "Other": {"min": 1_500, "max": 2_500},
    },
}

Number = Union[int, float]
ExpenseSpec = Union[Number, Mapping[str, Number]]


@dataclass(frozen=True)
class Budget:
    monthly_income: float
    tax_rate: float
    monthly_expenses: Dict[str, float]

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


def load_config(path: str | Path | None) -> Dict[str, Any]:
    """
    Load config from JSON or YAML. If path is None, returns DEFAULT_CONFIG.

    JSON: built-in support
    YAML: requires PyYAML (pip install pyyaml)
    """
    if path is None:
        return dict(DEFAULT_CONFIG)

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    suffix = config_path.suffix.lower()
    if suffix == ".json":
        return json.loads(config_path.read_text(encoding="utf-8"))

    if suffix in {".yml", ".yaml"}:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "YAML config requested but PyYAML is not installed. "
                "Install it with: pip install pyyaml"
            ) from exc
        return yaml.safe_load(config_path.read_text(encoding="utf-8"))

    raise ValueError(f"Unsupported config extension: {suffix} (use .json or .yml/.yaml)")


def _as_float(value: Any, *, field_name: str) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    raise TypeError(f"{field_name} must be a number, got: {type(value).__name__}")


def generate_monthly_expenses(expense_specs: Mapping[str, ExpenseSpec]) -> Dict[str, float]:
    """
    Generate monthly expenses from config specs.

    Each spec can be:
      - number (fixed)
      - {"min": number, "max": number} (random uniform)
    """
    expenses: Dict[str, float] = {}

    for name, spec in expense_specs.items():
        if isinstance(spec, (int, float)):
            expenses[name] = float(spec)
            continue

        if isinstance(spec, Mapping):
            if "min" not in spec or "max" not in spec:
                raise ValueError(f"Expense '{name}' range must include 'min' and 'max'.")
            min_v = _as_float(spec["min"], field_name=f"{name}.min")
            max_v = _as_float(spec["max"], field_name=f"{name}.max")
            if min_v > max_v:
                raise ValueError(f"Expense '{name}' has min > max ({min_v} > {max_v}).")
            expenses[name] = random.uniform(min_v, max_v)
            continue

        raise TypeError(
            f"Expense '{name}' must be a number or a dict with min/max; got {type(spec).__name__}."
        )

    return expenses


def _apply_plot_style() -> None:
    # Minimal, matplotlib-only styling.
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
        }
    )


def _colors_for_categories(categories: List[str]) -> List[str]:
    positives = {"Income", "Savings"}
    # Prettier palette than plain 'red/green' while keeping intent.
    return ["#2E7D32" if c in positives else "#C62828" for c in categories]


def _plot_bar(ax: plt.Axes, title: str, categories: List[str], amounts: List[float]) -> None:
    colors = _colors_for_categories(categories)
    bars = ax.bar(categories, amounts, color=colors, edgecolor="black", linewidth=0.4, alpha=0.9)

    ax.set_title(title, pad=10)
    ax.set_ylabel("Amount ($)")
    ax.yaxis.set_major_formatter(StrMethodFormatter(CURRENCY_FORMAT))
    ax.set_axisbelow(True)

    # Add headroom for labels
    max_amount = max(amounts) if amounts else 0
    ax.set_ylim(0, max_amount * 1.18 if max_amount > 0 else 1)

    # Value labels
    for bar, value in zip(bars, amounts):
        ax.annotate(
            f"{value:,.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )


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
    config = load_config(path=None)

    seed = config.get("seed")
    if seed is not None:
        random.seed(int(seed))

    monthly_income = _as_float(config["monthly_income"], field_name="monthly_income")
    tax_rate = _as_float(config["tax_rate"], field_name="tax_rate")

    expense_specs = config["monthly_expenses"]
    if not isinstance(expense_specs, Mapping):
        raise TypeError("monthly_expenses must be an object/dict in the config.")

    monthly_expenses = generate_monthly_expenses(expense_specs)

    budget = Budget(
        monthly_income=monthly_income,
        tax_rate=tax_rate,
        monthly_expenses=monthly_expenses,
    )

    monthly_categories, monthly_amounts, yearly_categories, yearly_amounts = build_plot_data(budget)

    _apply_plot_style()
    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(11, 5), constrained_layout=True)
    fig.suptitle("Financial Overview", fontsize=14, y=1.02)

    _plot_bar(axs[0], "Monthly", monthly_categories, monthly_amounts)
    axs[0].tick_params(axis="x", rotation=35)

    _plot_bar(axs[1], "Yearly", yearly_categories, yearly_amounts)

    plt.show()


if __name__ == "__main__":
    main()
