# ============================================================
# Weather Intelligence Platform
# Dashboard Layout
# ============================================================

import os

from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable
from dash_iconify import DashIconify

from dashboard.styles import (
    PAGE_STYLE,
    CONTENT_STYLE,

    HEADER_STYLE,
    HEADER_TITLE_STYLE,
    HEADER_SUBTITLE_STYLE,

    NAV_ITEM_STYLE,
    ACTIVE_NAV_STYLE,

    KPI_CARD_STYLE,
    MODEL_CARD_STYLE,

    SECTION_STYLE,
    SECTION_TITLE_STYLE,
    SECTION_SUBTITLE_STYLE,

    HERO_STYLE,
    HERO_TITLE_STYLE,
    HERO_ACCENT_STYLE,
    HERO_TEXT_STYLE,
    HERO_SMALL_TEXT_STYLE,

    BADGE_STYLE,
    ICON_BOX_STYLE,

    KPI_LABEL_STYLE,
    KPI_VALUE_STYLE,
    KPI_DESCRIPTION_STYLE,

    MODEL_LABEL_STYLE,
    MODEL_VALUE_STYLE,
    MODEL_NAME_STYLE,

    LABEL_STYLE,

    DROPDOWN_STYLE,
    DATE_STYLE,

    TABLE_STYLE,
    TABLE_CELL_STYLE,
    TABLE_HEADER_STYLE,

    GRAPH_STYLE,

    FOOTER_STYLE,

    DROPDOWN_CSS,
)


# ============================================================
# Environment Configuration
# ============================================================

AIRFLOW_URL = os.getenv(
    "AIRFLOW_URL",
    "/airflow/",
)


# ============================================================
# Reusable Components
# ============================================================


def icon(name, color="#46c8ff", size=18):
    return DashIconify(
        icon=name,
        width=size,
        height=size,
        color=color,
    )


def section_header(title, subtitle):
    return html.Div(
        [
            html.H2(
                title,
                style=SECTION_TITLE_STYLE,
            ),
            html.Div(
                subtitle,
                style=SECTION_SUBTITLE_STYLE,
            ),
        ]
    )


def kpi_card(
    title,
    description,
    component_id,
    icon_name,
):
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            icon(
                                icon_name,
                                color="#46c8ff",
                                size=18,
                            ),
                        ],
                        style=ICON_BOX_STYLE,
                    ),

                    html.Div(
                        [
                            html.Div(
                                title,
                                style=KPI_LABEL_STYLE,
                            ),

                            html.Div(
                                id=component_id,
                                style=KPI_VALUE_STYLE,
                            ),

                            html.Div(
                                description,
                                style=KPI_DESCRIPTION_STYLE,
                            ),
                        ],
                        style={
                            "marginLeft": "11px",
                            "flex": "1",
                            "minWidth": "0",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "height": "100%",
                },
            ),
        ],
        style=KPI_CARD_STYLE,
    )


def metric_card(
    title,
    component_id,
    icon_name,
):
    return html.Div(
        [
            html.Div(
                [
                    icon(
                        icon_name,
                        color="#8ea7c4",
                        size=13,
                    ),

                    html.Span(
                        title,
                        style={
                            "marginLeft": "5px",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    **MODEL_LABEL_STYLE,
                },
            ),

            html.Div(
                id=component_id,
                style=MODEL_VALUE_STYLE,
            ),
        ],
        style=MODEL_CARD_STYLE,
    )


# ============================================================
# Top Navigation
# ============================================================


def nav_item(
    label,
    icon_name,
    href="#",
    active=False,
    external=False,
):
    """
    Create a top navigation item.

    Parameters
    ----------
    label : str
        Text displayed in the navigation item.

    icon_name : str
        Dash Iconify icon name.

    href : str
        Destination URL/path.

    active : bool
        Whether this item is currently active.

    external : bool
        Whether the destination should open in a new tab.
    """

    return html.A(
        [
            icon(
                icon_name,
                color="#ffffff" if active else "#8ea7c4",
                size=15,
            ),

            html.Span(
                label,
                style={
                    "marginLeft": "7px",
                    "whiteSpace": "nowrap",
                },
            ),
        ],

        href=href,

        # Open external resources in a new browser tab
        target="_blank" if external else None,

        # Security attribute for external links
        rel="noopener noreferrer" if external else None,

        style={
            **(
                ACTIVE_NAV_STYLE
                if active
                else NAV_ITEM_STYLE
            ),
            "display": "inline-flex",
            "alignItems": "center",
            "justifyContent": "center",
            "textDecoration": "none",
            "borderRadius": "10px",
            "padding": "9px 13px",
            "margin": "0",
        },
    )


# ============================================================
# Top Navigation Bar
# ============================================================


top_navigation = html.Div(
    [
        # ====================================================
        # Brand
        # ====================================================

        html.Div(
            [
                html.Div(
                    [
                        icon(
                            "mdi:cloud-outline",
                            color="#dceaff",
                            size=28,
                        ),

                        html.Div(
                            [
                                html.Div(
                                    "Weather Intelligence",
                                    style={
                                        "fontSize": "14px",
                                        "fontWeight": "700",
                                        "color": "#ffffff",
                                        "lineHeight": "1.05",
                                    },
                                ),

                                html.Div(
                                    "Platform",
                                    style={
                                        "fontSize": "14px",
                                        "fontWeight": "700",
                                        "color": "#46c8ff",
                                        "lineHeight": "1.05",
                                    },
                                ),
                            ],
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "9px",
                    },
                ),

                html.Div(
                    "DATA ENGINEERING | ML | CLOUD",
                    style={
                        "fontSize": "8px",
                        "letterSpacing": "1px",
                        "color": "#59728d",
                        "marginTop": "7px",
                    },
                ),
            ],
            style={
                "flexShrink": "0",
            },
        ),

        # ====================================================
        # Navigation Links
        # ====================================================

        html.Div(
            [
                # Dashboard
                nav_item(
                    "Dashboard",
                    "mdi:view-dashboard-outline",
                    href="/",
                    active=True,
                ),

                # Airflow
                nav_item(
                    "Airflow",
                    "simple-icons:apacheairflow",
                    href=AIRFLOW_URL,
                ),

                # MLflow
                nav_item(
                    "MLflow",
                    "mdi:graph-outline",
                ),

                # Architecture
                # Opens architecture.png from assets/
                # in a new browser tab.
                nav_item(
                    "Architecture",
                    "mdi:graph-outline",
                    href="/assets/architecture.png",
                    external=True,
                ),

                # About
                # Opens the GitHub repository
                # in a new browser tab.
                nav_item(
                    "About",
                    "mdi:information-outline",
                    href=(
                        "https://github.com/"
                        "gaurav-dwivedi-de/"
                        "data_engineering_portfolio"
                    ),
                    external=True,
                ),
            ],

            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "flex-end",
                "gap": "4px",
                "flexWrap": "wrap",
            },
        ),
    ],

    id="weather-dashboard-navigation",

    style={
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "gap": "20px",
        "width": "100%",
        "padding": "14px 28px",
        "backgroundColor": "#061321",
        "borderBottom": "1px solid #142b40",
        "boxSizing": "border-box",
        "position": "relative",
        "zIndex": "1000",
        "flexWrap": "wrap",
    },
)


# ============================================================
# Header
# ============================================================


header = html.Div(
    [
        html.Div(
            [
                html.H1(
                    "Weather Intelligence Platform",
                    style=HEADER_TITLE_STYLE,
                ),

                html.Div(
                    "Real-time weather insights, forecasts, "
                    "and cloud-native data engineering.",
                    style=HEADER_SUBTITLE_STYLE,
                ),
            ]
        ),
    ],
    style=HEADER_STYLE,
)


# ============================================================
# Hero
# ============================================================


hero = html.Div(
    [
        html.Div(
            "Weather Intelligence Platform",
            style={
                "fontSize": "11px",
                "fontWeight": "600",
                "color": "#8fbce5",
                "letterSpacing": "0.5px",
                "marginBottom": "8px",
            },
        ),

        html.H1(
            [
                "From Data to ",

                html.Span(
                    "Forecasts",
                    style=HERO_ACCENT_STYLE,
                ),
            ],
            style=HERO_TITLE_STYLE,
        ),

        html.Div(
            "Real-time insights, smarter forecasts, "
            "and a cloud-native data platform.",
            style=HERO_TEXT_STYLE,
        ),

        html.Div(
            "A complete data engineering and machine learning "
            "pipeline built around real weather data.",
            style=HERO_SMALL_TEXT_STYLE,
        ),

        html.Div(
            [
                icon(
                    "mdi:cloud-check-outline",
                    color="#46c8ff",
                    size=25,
                ),

                html.Div(
                    "Cloud-Native",
                    style={
                        "fontSize": "13px",
                        "fontWeight": "700",
                        "color": "#ffffff",
                    },
                ),

                html.Div(
                    "Data → ML → API → Dashboard",
                    style={
                        "fontSize": "8px",
                        "color": "#7891ad",
                    },
                ),
            ],
            style={
                "textAlign": "center",
                "marginTop": "8px",
            },
        ),
    ],

    id="weather-dashboard-hero",

    style=HERO_STYLE,
)


# ============================================================
# Live Prediction
# ============================================================


live_prediction_section = html.Div(
    [
        section_header(
            "Live Prediction",
            "FastAPI-powered next-hour prediction",
        ),

        html.Label(
            "Select City",
            style=LABEL_STYLE,
        ),

        dcc.Dropdown(
            id="city-dropdown",
            placeholder="Select a city",
            clearable=False,
            className="weather-dropdown",
            style=DROPDOWN_STYLE,
        ),

        html.Div(
            style={
                "height": "12px",
            }
        ),

        # ====================================================
        # Bootstrap Responsive KPI Grid
        #
        # xs=12 → one card per row on mobile
        # md=4  → three cards per row on desktop/tablet
        # ====================================================

        dbc.Row(
            [
                dbc.Col(
                    kpi_card(
                        "Current Temperature",
                        "Observed temperature",
                        "current-temperature",
                        "mdi:thermometer",
                    ),
                    xs=12,
                    md=4,
                ),

                dbc.Col(
                    kpi_card(
                        "Predicted Temperature",
                        "Next-hour prediction",
                        "predicted-temperature",
                        "mdi:weather-sunny",
                    ),
                    xs=12,
                    md=4,
                ),

                dbc.Col(
                    kpi_card(
                        "Prediction Difference",
                        "Prediction vs current",
                        "prediction-difference",
                        "mdi:triangle-outline",
                    ),
                    xs=12,
                    md=4,
                ),
            ],
            className="g-3",
        ),

        html.Div(
            [
                html.Span(
                    "Latest observation: ",
                    style={
                        "fontWeight": "600",
                    },
                ),

                html.Span(
                    id="latest-update",
                ),
            ],
            style={
                **KPI_DESCRIPTION_STYLE,
                "marginTop": "8px",
            },
        ),
    ],
    style=SECTION_STYLE,
)


# ============================================================
# Model Performance
# ============================================================


model_performance_section = html.Div(
    [
        section_header(
            "Model Performance",
            "Latest model evaluation metrics",
        ),

        # ====================================================
        # Bootstrap Responsive Model Grid
        #
        # xs=12 → 1 per row
        # sm=6  → 2 per row
        # lg=3  → 4 per row
        # ====================================================

        dbc.Row(
            [
                dbc.Col(
                    metric_card(
                        "R² SCORE",
                        "model-r2",
                        "mdi:chart-bell-curve",
                    ),
                    xs=12,
                    sm=6,
                    lg=3,
                ),

                dbc.Col(
                    metric_card(
                        "RMSE",
                        "model-rmse",
                        "mdi:chart-line",
                    ),
                    xs=12,
                    sm=6,
                    lg=3,
                ),

                dbc.Col(
                    metric_card(
                        "MAE",
                        "model-mae",
                        "mdi:chart-line",
                    ),
                    xs=12,
                    sm=6,
                    lg=3,
                ),

                dbc.Col(
                    metric_card(
                        "DATASET",
                        "model-dataset",
                        "mdi:database-outline",
                    ),
                    xs=12,
                    sm=6,
                    lg=3,
                ),
            ],
            className="g-3",
        ),

        html.Div(
            [
                html.Span(
                    "MODEL ",
                    style={
                        "fontWeight": "700",
                    },
                ),

                html.Span(
                    id="model-name",
                ),

                html.Span(
                    "  •  LAST TRAINED ",
                    style={
                        "fontWeight": "700",
                        "marginLeft": "10px",
                    },
                ),

                html.Span(
                    id="model-trained-at",
                ),
            ],
            style=MODEL_NAME_STYLE,
        ),
    ],
    style=SECTION_STYLE,
)


# ============================================================
# Historical Analysis
# ============================================================


historical_analysis_section = html.Div(
    [
        section_header(
            "Historical Analysis",
            "Filter historical predictions and inspect model performance",
        ),

        html.Label(
            "Select City",
            style=LABEL_STYLE,
        ),

        dcc.Dropdown(
            id="history-city-dropdown",
            placeholder="Select a city",
            clearable=False,
            className="weather-dropdown",
            style=DROPDOWN_STYLE,
        ),

        html.Div(
            style={
                "height": "10px",
            }
        ),

        html.Label(
            "Select Date",
            style=LABEL_STYLE,
        ),

        dcc.DatePickerSingle(
            id="history-date-picker",
            display_format="DD MMM YYYY",
            placeholder="All Dates",
            style=DATE_STYLE,
        ),

        html.Div(
            style={
                "height": "14px",
            }
        ),

        # ====================================================
        # Historical Dataset
        # ====================================================

        html.Div(
            [
                html.Div(
                    [
                        icon(
                            "mdi:table",
                            color="#46c8ff",
                            size=14,
                        ),

                        html.Span(
                            "Historical Prediction Records",
                            style={
                                "fontSize": "13px",
                                "fontWeight": "650",
                                "color": "#dceaff",
                                "marginLeft": "6px",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "marginBottom": "9px",
                    },
                ),

                DataTable(
                    id="prediction-table",

                    columns=[
                        {
                            "name": "Date & Time",
                            "id": "time",
                        },
                        {
                            "name": "City",
                            "id": "city",
                        },
                        {
                            "name": "Actual Temperature (°C)",
                            "id": "target_temp_next_hour",
                        },
                        {
                            "name": "Predicted Temperature (°C)",
                            "id": "predicted_temperature",
                        },
                        {
                            "name": "Prediction Error (°C)",
                            "id": "prediction_error",
                        },
                    ],

                    data=[],

                    page_size=10,

                    sort_action="native",

                    style_table=TABLE_STYLE,

                    style_cell=TABLE_CELL_STYLE,

                    style_header=TABLE_HEADER_STYLE,
                ),
            ]
        ),

        html.Div(
            style={
                "height": "14px",
            }
        ),

        # ====================================================
        # Graphs
        # ====================================================

        html.Div(
            [
                dcc.Graph(
                    id="actual-vs-predicted-chart",
                    config={
                        "displayModeBar": False,
                        "responsive": True,
                    },
                    style=GRAPH_STYLE,
                ),

                dcc.Graph(
                    id="prediction-error-chart",
                    config={
                        "displayModeBar": False,
                        "responsive": True,
                    },
                    style=GRAPH_STYLE,
                ),
            ]
        ),
    ],
    style=SECTION_STYLE,
)


# ============================================================
# Footer
# ============================================================


footer = html.Div(
    "Weather Intelligence Platform • "
    "Data Engineering • Machine Learning • Kubernetes • Cloud",
    style=FOOTER_STYLE,
)


# ============================================================
# Main Dashboard Content
# ============================================================


main_content = html.Div(
    [
        header,
        hero,
        live_prediction_section,
        model_performance_section,
        historical_analysis_section,
        footer,
    ],

    id="weather-dashboard-content",

    style=CONTENT_STYLE,
)


# ============================================================
# Complete Responsive Dashboard
# ============================================================


layout = html.Div(
    [
        # ====================================================
        # Inject custom Dashboard component CSS
        # ====================================================

        dcc.Markdown(
            DROPDOWN_CSS,
            dangerously_allow_html=True,
        ),

        # ====================================================
        # Top Navigation
        # ====================================================

        top_navigation,

        # ====================================================
        # Main Dashboard Content
        # ====================================================

        main_content,
    ],

    id="weather-dashboard-main",

    style={
        **PAGE_STYLE,
        "width": "100%",
        "minHeight": "100vh",
        "overflowX": "hidden",
    },
)


# ============================================================
# Layout Factory
# ============================================================


def create_layout():
    """
    Return the dashboard layout.
    """

    return layout