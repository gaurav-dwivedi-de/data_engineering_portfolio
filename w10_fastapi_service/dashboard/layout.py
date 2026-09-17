# ============================================================
# Weather Intelligence Platform
# Dashboard Layout
# ============================================================

import os

from dash import dcc, html
from dash.dash_table import DataTable
from dash_iconify import DashIconify

from dashboard.styles import (
    PAGE_STYLE,
    SIDEBAR_STYLE,
    MAIN_STYLE,
    CONTENT_STYLE,

    HEADER_STYLE,
    HEADER_TITLE_STYLE,
    HEADER_SUBTITLE_STYLE,

    NAV_SECTION_STYLE,
    NAV_ITEM_STYLE,
    ACTIVE_NAV_STYLE,

    CARD_STYLE,
    KPI_CARD_STYLE,
    MODEL_CARD_STYLE,

    KPI_ROW_STYLE,
    KPI_COLUMN_STYLE,

    MODEL_ROW_STYLE,
    MODEL_COLUMN_STYLE,

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
    SIDEBAR_FOOTER_STYLE,

    DROPDOWN_CSS,
)


# ============================================================
# Environment Configuration
# ============================================================

# Airflow URL changes depending on where the Dashboard runs.
#
# Docker Compose:
#   AIRFLOW_URL=http://localhost:8080/
#
# Local Kubernetes:
#   AIRFLOW_URL=http://localhost:30080/
#
# Oracle K3s + public Traefik Ingress:
#   AIRFLOW_URL=/airflow/
#
# Default:
#   /airflow/
#
# This allows the same Dashboard image/code to run in all
# environments without hard-coding one environment's URL.

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


def nav_item(label, icon_name, href="#", active=False):
    """
    Create a sidebar navigation item.

    href is configurable so the same Dashboard can use
    different Airflow URLs in different environments.
    """

    return html.A(
        [
            icon(
                icon_name,
                color="#ffffff" if active else "#8ea7c4",
                size=15,
            ),
            html.Span(label),
        ],
        href=href,
        style=ACTIVE_NAV_STYLE if active else NAV_ITEM_STYLE,
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
# Sidebar
# ============================================================


sidebar = html.Div(
    [
        # Logo / Brand
        html.Div(
            [
                html.Div(
                    [
                        icon(
                            "mdi:cloud-outline",
                            color="#dceaff",
                            size=25,
                        ),
                        html.Div(
                            [
                                html.Div(
                                    "Weather Intelligence",
                                    style={
                                        "fontSize": "11px",
                                        "fontWeight": "700",
                                        "color": "#ffffff",
                                    },
                                ),
                                html.Div(
                                    "Platform",
                                    style={
                                        "fontSize": "11px",
                                        "fontWeight": "700",
                                        "color": "#46c8ff",
                                    },
                                ),
                            ],
                            style={
                                "lineHeight": "1.15",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "8px",
                    },
                ),
                html.Div(
                    "DATA ENGINEERING | ML | CLOUD",
                    style={
                        "fontSize": "7px",
                        "letterSpacing": "0.8px",
                        "color": "#59728d",
                        "marginTop": "7px",
                    },
                ),
            ],
            style={
                "marginBottom": "18px",
            },
        ),

        # ====================================================
        # Main
        # ====================================================

        html.Div(
            "MAIN",
            style=NAV_SECTION_STYLE,
        ),

        nav_item(
            "Dashboard",
            "mdi:view-dashboard-outline",
            href="/",
            active=True,
        ),

        # ====================================================
        # Platform Apps
        # ====================================================

        html.Div(
            "PLATFORM APPS",
            style=NAV_SECTION_STYLE,
        ),

        nav_item(
            "Airflow",
            "simple-icons:apacheairflow",
            href=AIRFLOW_URL,
        ),

        nav_item(
            "MLflow",
            "mdi:graph-outline",
        ),

        # ====================================================
        # System
        # ====================================================

        html.Div(
            "SYSTEM",
            style=NAV_SECTION_STYLE,
        ),

        nav_item(
            "Architecture",
            "mdi:graph",
        ),

        nav_item(
            "About",
            "mdi:information-outline",
        ),

        # ====================================================
        # Sidebar Footer
        # ====================================================

        html.Div(
            [
                html.Div(
                    "Platform",
                    style={
                        "fontSize": "8px",
                        "color": "#617892",
                    },
                ),
                html.Div(
                    "Public deployment",
                    style={
                        "fontSize": "10px",
                        "fontWeight": "600",
                        "color": "#dceaff",
                        "marginTop": "2px",
                    },
                ),
                html.Div(
                    "Kubernetes • Cloud • ML",
                    style={
                        "fontSize": "8px",
                        "color": "#617892",
                        "marginTop": "2px",
                    },
                ),
            ],
            style=SIDEBAR_FOOTER_STYLE,
        ),
    ],
    style=SIDEBAR_STYLE,
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
                html.Span(
                    "Real Data",
                    style=BADGE_STYLE,
                ),
                html.Span(
                    "Machine Learning",
                    style=BADGE_STYLE,
                ),
                html.Span(
                    "Scalable Infrastructure",
                    style=BADGE_STYLE,
                ),
                html.Span(
                    "Real-World Impact",
                    style=BADGE_STYLE,
                ),
            ]
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

        # City selector FIRST
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

        # KPI cards — EXPLICIT FLEX ROW
        html.Div(
            [
                html.Div(
                    kpi_card(
                        "Current Temperature",
                        "Observed temperature",
                        "current-temperature",
                        "mdi:thermometer",
                    ),
                    style=KPI_COLUMN_STYLE,
                ),

                html.Div(
                    kpi_card(
                        "Predicted Temperature",
                        "Next-hour prediction",
                        "predicted-temperature",
                        "mdi:weather-sunny",
                    ),
                    style=KPI_COLUMN_STYLE,
                ),

                html.Div(
                    kpi_card(
                        "Prediction Difference",
                        "Prediction vs current",
                        "prediction-difference",
                        "mdi:triangle-outline",
                    ),
                    style=KPI_COLUMN_STYLE,
                ),
            ],
            style=KPI_ROW_STYLE,
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

        # Model metrics — EXPLICIT FLEX ROW
        html.Div(
            [
                html.Div(
                    metric_card(
                        "R² SCORE",
                        "model-r2",
                        "mdi:chart-bell-curve",
                    ),
                    style=MODEL_COLUMN_STYLE,
                ),

                html.Div(
                    metric_card(
                        "RMSE",
                        "model-rmse",
                        "mdi:chart-line",
                    ),
                    style=MODEL_COLUMN_STYLE,
                ),

                html.Div(
                    metric_card(
                        "MAE",
                        "model-mae",
                        "mdi:chart-line",
                    ),
                    style=MODEL_COLUMN_STYLE,
                ),

                html.Div(
                    metric_card(
                        "DATASET",
                        "model-dataset",
                        "mdi:database-outline",
                    ),
                    style=MODEL_COLUMN_STYLE,
                ),
            ],
            style=MODEL_ROW_STYLE,
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

        # City FIRST
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

        # Date SECOND
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

        # Historical dataset THIRD
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

        # Graphs FOURTH
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
# Complete Dashboard
# ============================================================


layout = html.Div(
    [
        # Inject custom dashboard CSS
        dcc.Markdown(
            DROPDOWN_CSS,
            dangerously_allow_html=True,
        ),

        sidebar,

        html.Div(
            [
                html.Div(
                    [
                        header,
                        hero,
                        live_prediction_section,
                        model_performance_section,
                        historical_analysis_section,
                        footer,
                    ],
                    style=CONTENT_STYLE,
                ),
            ],
            style=MAIN_STYLE,
        ),
    ],
    style=PAGE_STYLE,
)


# ============================================================
# Layout Factory
# ============================================================


def create_layout():
    """
    Return the dashboard layout.
    """

    return layout