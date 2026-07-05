from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


CSV_PATH = Path(__file__).with_name("MY D&D Books - Sheet1.csv")


@st.cache_data
def load_books(csv_path: Path) -> pd.DataFrame:
    books = pd.read_csv(csv_path, dtype={"Books": "string", "Owned": "string"})
    books.columns = [column.strip() for column in books.columns]

    required_columns = {"Books", "Owned"}
    missing_columns = required_columns - set(books.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required CSV column(s): {missing}")

    books = books[["Books", "Owned"]].copy()
    books["Books"] = books["Books"].fillna("").str.strip()
    books["Owned"] = books["Owned"].fillna("").str.strip()
    books = books[books["Books"] != ""].reset_index(drop=True)
    books["Status"] = books["Owned"].eq("1").map({True: "Owned", False: "Not owned"})
    return books


def book_table(frame: pd.DataFrame) -> None:
    st.dataframe(
        frame[["Books", "Status"]],
        hide_index=True,
        width="stretch",
        column_config={
            "Books": st.column_config.TextColumn("Book"),
            "Status": st.column_config.TextColumn("Status"),
        },
    )


def main() -> None:
    st.set_page_config(page_title="D&D Book Collection", page_icon=":books:", layout="wide")
    st.title("D&D Book Collection")

    try:
        df = load_books(CSV_PATH)
    except Exception as exc:
        st.error(f"Could not load `{CSV_PATH.name}`.")
        st.exception(exc)
        st.stop()

    owned = df[df["Status"] == "Owned"]
    not_owned = df[df["Status"] == "Not owned"]

    total_count = len(df)
    owned_count = len(owned)
    not_owned_count = len(not_owned)
    owned_percent = (owned_count / total_count * 100) if total_count else 0

    metric_columns = st.columns(3)
    metric_columns[0].metric("Total books", total_count)
    metric_columns[1].metric("Owned", owned_count)
    metric_columns[2].metric("Not owned", not_owned_count)

    tabs = st.tabs(["Owned", "Not owned", "Search", "Trends", "CSV"])

    with tabs[0]:
        st.subheader("Books I Own")
        book_table(owned)

    with tabs[1]:
        st.subheader("Books I Do Not Own")
        book_table(not_owned)

    with tabs[2]:
        st.subheader("Search")
        query = st.text_input("Find a book", placeholder="Type part of a title...")
        filtered = df
        if query.strip():
            filtered = df[df["Books"].str.contains(query.strip(), case=False, regex=False)]

        st.caption(f"{len(filtered)} result{'s' if len(filtered) != 1 else ''}")
        book_table(filtered)

    with tabs[3]:
        st.subheader("Trends")
        chart_data = pd.DataFrame(
            {
                "Status": ["Owned", "Not owned"],
                "Books": [owned_count, not_owned_count],
            }
        )

        chart_columns = st.columns([1, 2])
        with chart_columns[0]:
            st.metric("Percent owned", f"{owned_percent:.1f}%")
            st.metric("Percent not owned", f"{100 - owned_percent:.1f}%")
        with chart_columns[1]:
            fig = px.pie(
                chart_data,
                names="Status",
                values="Books",
                color="Status",
                color_discrete_map={"Owned": "#2f7d5c", "Not owned": "#c94f3d"},
                hole=0.3,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, width="stretch")

    with tabs[4]:
        st.subheader("Raw CSV")
        st.caption(f"Source: `{CSV_PATH.name}`")
        st.dataframe(df[["Books", "Owned"]], hide_index=True, width="stretch")


if __name__ == "__main__":
    main()
