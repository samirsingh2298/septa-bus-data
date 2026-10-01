import plotly.graph_objects as go
import streamlit as st
from db import require_database
from queries import route_list, route_shape, stop_lateness_for_route

st.set_page_config(page_title="SEPTA Bus Lateness", page_icon="🚌", layout="wide")
require_database()

st.title("SEPTA Bus Lateness")
st.caption(
    "Hover over a stop on the map to see its name and average lateness, "
    "computed over all data collected so far. Negative = running ahead of "
    "schedule."
)

routes_df = route_list()
if routes_df.empty:
    st.info("No routes yet - let the pipeline run at least one poll cycle.")
    st.stop()

selected_route = st.selectbox(
    "Route",
    options=routes_df["route_id"],
    format_func=lambda rid: (
        f"{rid} - {routes_df.loc[routes_df.route_id == rid, 'route_long_name'].iloc[0] or ''}"
    ),
)

shape_df = route_shape(selected_route)
stops_df = stop_lateness_for_route(selected_route)

fig = go.Figure()

if not shape_df.empty:
    # A route commonly has multiple shape_ids (inbound/outbound/branches).
    # Insert a None between each shape's points so Plotly breaks the line
    # instead of connecting the end of one shape to the start of the next.
    lats, lons = [], []
    for _, group in shape_df.groupby("shape_id", sort=False):
        if lats:
            lats.append(None)
            lons.append(None)
        lats.extend(group["shape_pt_lat"])
        lons.extend(group["shape_pt_lon"])

    fig.add_trace(
        go.Scattermap(
            lat=lats,
            lon=lons,
            mode="lines",
            line={"width": 3, "color": "#6b7280"},
            name="Route path",
            hoverinfo="skip",
        )
    )
else:
    st.caption("No GTFS shape for this route (likely an ad-hoc/unscheduled route).")

if not stops_df.empty:
    hover_text = [
        f"{row.stop_name}<br>Avg late: "
        + (f"{row.avg_minutes_late:.1f} min" if row.avg_minutes_late is not None else "no data yet")
        for row in stops_df.itertuples()
    ]
    fig.add_trace(
        go.Scattermap(
            lat=stops_df["lat"],
            lon=stops_df["lon"],
            mode="markers",
            marker={
                "size": 12,
                "color": stops_df["avg_minutes_late"].fillna(0),
                "colorscale": "RdBu_r",
                "cmid": 0,
                "showscale": True,
                "colorbar": {"title": "Avg min. late"},
            },
            name="Stops",
            text=hover_text,
            hovertemplate="%{text}<extra></extra>",
        )
    )
    center_lat, center_lon = stops_df["lat"].mean(), stops_df["lon"].mean()
else:
    # Unreachable in practice: route_list() only offers routes that have at
    # least one row in dim_stop. Kept as a defensive fallback.
    center_lat, center_lon = 39.9526, -75.1652  # Philadelphia City Hall

fig.update_layout(
    map={"style": "open-street-map", "center": {"lat": center_lat, "lon": center_lon}, "zoom": 11},
    margin={"l": 0, "r": 0, "t": 0, "b": 0},
    height=600,
    showlegend=False,
)

# Plain render, no on_select: a click-driven detail panel would need a
# Streamlit rerun, which hits a confirmed Streamlit bug (unresolved as of
# 1.38+) where any widget interaction resets the map's pan/zoom regardless
# of uirevision. Hover tooltips show the same info without that round-trip.
st.plotly_chart(fig, use_container_width=True)
