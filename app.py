import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "problems.json"

TOPICS = [
    "Arrays",
    "Strings",
    "Hashing",
    "Searching",
    "Sorting",
    "Recursion",
]
DIFFICULTIES = ["Basic", "Easy", "Medium", "Hard"]
PLATFORMS = ["LeetCode", "GeeksforGeeks", "HackerRank", "Practice"]
REQUIRED_FIELDS = ("title", "topic", "difficulty", "platform", "date")


def load_records(data_path: Path = DATA_FILE) -> tuple[pd.DataFrame, list[str]]:
    """Load and validate problem records from problems.json into a DataFrame."""
    warnings: list[str] = []

    if not data_path.exists():
        warnings.append(
            f"Data file not found at `{data_path.name}`. Add a problem with `tracker.py` to get started."
        )
        return pd.DataFrame(columns=list(REQUIRED_FIELDS) + ["parsed_date"]), warnings

    raw_text = data_path.read_text(encoding="utf-8").strip()
    if not raw_text:
        return pd.DataFrame(columns=list(REQUIRED_FIELDS) + ["parsed_date"]), warnings

    try:
        payload: Any = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        warnings.append(f"Malformed JSON in `{data_path.name}`: {exc}")
        return pd.DataFrame(columns=list(REQUIRED_FIELDS) + ["parsed_date"]), warnings

    if not isinstance(payload, list):
        warnings.append(
            f"Expected a JSON list in `{data_path.name}`, got `{type(payload).__name__}`."
        )
        return pd.DataFrame(columns=list(REQUIRED_FIELDS) + ["parsed_date"]), warnings

    valid_rows: list[dict[str, Any]] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            warnings.append(f"Record #{index} is not a JSON object and was skipped.")
            continue

        missing = [
            field for field in REQUIRED_FIELDS
            if field not in item or not str(item[field]).strip()
        ]
        if missing:
            warnings.append(
                f"Record #{index} is missing required field(s): {', '.join(missing)}."
            )
            continue

        row = {field: str(item[field]).strip() for field in REQUIRED_FIELDS}
        parsed_date = pd.to_datetime(row["date"], format="%Y-%m-%d", errors="coerce")
        if pd.isna(parsed_date):
            parsed_date = pd.to_datetime(row["date"], errors="coerce")
        if pd.isna(parsed_date):
            warnings.append(
                f"Record #{index} ('{row['title']}') has an invalid date '{row['date']}'."
            )
        row["parsed_date"] = parsed_date
        valid_rows.append(row)

    if not valid_rows:
        return pd.DataFrame(columns=list(REQUIRED_FIELDS) + ["parsed_date"]), warnings

    return pd.DataFrame(valid_rows), warnings


def _extract_valid_dates(df: pd.DataFrame) -> pd.Series:
    """Return a Series of valid pandas Timestamps from parsed_date or date."""
    if df.empty:
        return pd.Series(dtype="datetime64[ns]")
    if "parsed_date" in df.columns:
        return pd.to_datetime(df["parsed_date"], errors="coerce").dropna()
    if "date" in df.columns:
        return pd.to_datetime(df["date"], errors="coerce").dropna()
    return pd.Series(dtype="datetime64[ns]")


def calculate_streaks(
    df: pd.DataFrame,
    reference_date: date | None = None,
) -> tuple[int, int]:
    """Calculate (current_streak, longest_streak) in consecutive calendar days."""
    valid_dates = _extract_valid_dates(df)
    solved_dates = set(valid_dates.dt.date)

    if not solved_dates:
        return 0, 0

    today = reference_date or date.today()
    yesterday = today - timedelta(days=1)

    if today in solved_dates:
        current_day: date | None = today
    elif yesterday in solved_dates:
        current_day = yesterday
    else:
        current_day = None

    current_streak = 0
    while current_day is not None and current_day in solved_dates:
        current_streak += 1
        current_day -= timedelta(days=1)

    longest_streak = 0
    streak = 0
    previous_day: date | None = None
    for solved_day in sorted(solved_dates):
        if previous_day is not None and (solved_day - previous_day).days == 1:
            streak += 1
        else:
            streak = 1
        longest_streak = max(longest_streak, streak)
        previous_day = solved_day

    return current_streak, longest_streak


def build_category_counts(
    df: pd.DataFrame,
    column: str,
    default_order: list[str],
) -> pd.Series:
    """Count rows for a category column while preserving expected categories."""
    counts = df[column].value_counts() if not df.empty else pd.Series(dtype="int64")
    extras = [val for val in counts.index if val not in default_order]
    ordered_labels = [*default_order, *sorted(extras)]
    return counts.reindex(ordered_labels, fill_value=0).astype(int)


def build_daily_activity(df: pd.DataFrame) -> pd.Series:
    """Group valid dates and count solved problems per day."""
    valid_dates = _extract_valid_dates(df)
    if valid_dates.empty:
        return pd.Series(dtype="int64")

    daily = valid_dates.dt.date.value_counts().sort_index()
    daily.index = pd.Index([d.isoformat() for d in daily.index], name="Date")
    return daily.astype(int)


def build_heatmap_figure(
    df: pd.DataFrame,
    reference_date: date | None = None,
) -> go.Figure:
    """Create a 365-day Plotly date-by-weekday activity heatmap figure."""
    today = reference_date or date.today()
    start_date = today - timedelta(days=364)

    valid_dates = _extract_valid_dates(df)
    daily_activity = (
        valid_dates.dt.date.value_counts().to_dict()
        if not valid_dates.empty
        else {}
    )

    all_dates = [start_date + timedelta(days=i) for i in range(365)]
    weekdays = [d.weekday() for d in all_dates]
    activity_values = [int(daily_activity.get(d, 0)) for d in all_dates]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=all_dates,
            y=weekdays,
            mode="markers",
            marker=dict(
                symbol="square",
                size=13,
                color=activity_values,
                colorscale=[
                    [0, "#E5E7EB"],
                    [0.25, "#9BE9A8"],
                    [0.50, "#40C463"],
                    [0.75, "#30A14E"],
                    [1, "#216E39"],
                ],
                cmin=0,
                cmax=max(1, max(activity_values)),
                showscale=True,
                colorbar=dict(title="Questions"),
            ),
            text=[f"{count} question(s) solved" for count in activity_values],
            hovertemplate="%{x|%d %b %Y}<br>%{text}<extra></extra>",
        )
    )

    fig.update_layout(
        height=230,
        xaxis=dict(
            title="",
            tickformat="%b",
            dtick="M1",
            showgrid=False,
        ),
        yaxis=dict(
            title="",
            tickmode="array",
            tickvals=[0, 1, 2, 3, 4, 5, 6],
            ticktext=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            autorange="reversed",
            showgrid=False,
        ),
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


def render_dashboard() -> None:
    """Render the Streamlit DSA Progress Dashboard."""
    st.set_page_config(
        page_title="DSA Practice Dashboard",
        page_icon="📊",
        layout="wide",
    )

    st.title("DSA Practice Dashboard")
    st.caption(
        "Visual reporting layer for your DSA progress tracked in `problems.json`."
    )

    df, warnings = load_records()
    for warning in warnings:
        st.warning(warning)

    difficulty_counts = build_category_counts(df, "difficulty", DIFFICULTIES)
    total_count = len(df)

    # 1. Summary metrics
    st.subheader("Summary Metrics")
    metric_cols = st.columns(5)
    metric_cols[0].metric("Total", total_count)
    for idx, difficulty in enumerate(DIFFICULTIES, start=1):
        metric_cols[idx].metric(difficulty, int(difficulty_counts.get(difficulty, 0)))

    # 2. Streak metric cards
    current_streak, longest_streak = calculate_streaks(df)
    st.divider()
    st.header("Consistency Tracker")
    col1, col2 = st.columns(2)
    col1.metric("Current Streak", f"{current_streak} Days")
    col2.metric("Longest Streak", f"{longest_streak} Days")

    if df.empty:
        st.info(
            "No completed questions recorded yet. Run `python tracker.py` to log your first solved problem, then rerun this dashboard."
        )

    # 3. Topic-wise progress & 4. Difficulty distribution
    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("Topic-wise Progress")
        topic_counts = build_category_counts(df, "topic", TOPICS)
        st.bar_chart(topic_counts)

    with right_col:
        st.subheader("Difficulty Distribution")
        st.bar_chart(difficulty_counts)

    # 5. Daily activity chart
    st.subheader("Daily Activity")
    daily_counts = build_daily_activity(df)
    if daily_counts.empty:
        st.info("No valid activity dates to plot yet.")
    else:
        st.line_chart(daily_counts)

    # 6. Activity heatmap (365-day view)
    st.subheader("Activity Heatmap (Last 365 Days)")
    heatmap_fig = build_heatmap_figure(df)
    st.plotly_chart(heatmap_fig, width="stretch")

    # 7. Platform statistics
    st.subheader("Platform Statistics")
    platform_counts = build_category_counts(df, "platform", PLATFORMS)
    st.bar_chart(platform_counts)

    # 8. Solved questions table with topic filter
    st.subheader("Solved Questions")
    available_topics = sorted(
        set(TOPICS) | (set(df["topic"].dropna().unique()) if not df.empty else set())
    )
    selected_topic = st.selectbox(
        "Filter by topic",
        options=["All", *available_topics],
        index=0,
    )

    display_df = (
        df[list(REQUIRED_FIELDS)].copy()
        if not df.empty
        else pd.DataFrame(columns=list(REQUIRED_FIELDS))
    )
    if selected_topic != "All" and not display_df.empty:
        display_df = display_df[display_df["topic"] == selected_topic]

    if not display_df.empty:
        display_df = display_df.sort_values(by="date", ascending=False).reset_index(
            drop=True
        )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
    )


if __name__ == "__main__":
    render_dashboard()
