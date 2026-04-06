from ..models.response import ChartConfig


def build_chart_config(intent: dict, columns: list) -> ChartConfig:
    chart_type = "bar" if intent.get("metric") == "volume" else "line"
    if intent.get("output_type") == "pie":
        chart_type = "pie"
    x_key = next((c for c in columns if c in ("date", "ts", "period") or "date" in c or "ts" in c), columns[0])
    # After pivot, remaining columns are the symbol names (the series to plot)
    series = [c for c in columns if c != x_key]
    return ChartConfig(chart_type=chart_type, x_key=x_key, series=series)


def needs_chart(intent: dict) -> bool:
    return intent.get("output_type") in ("chart", "both")
