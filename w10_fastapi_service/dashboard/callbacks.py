import dash
import plotly.graph_objects as go
import json

from dash import (
    Input,
    Output,
)

from app.config import MODEL_METRICS_PATH
from dashboard.api_client import request_prediction

from dashboard.live_prediction_loader import (
    load_live_prediction_data,
    get_available_cities,
    get_latest_record,
    prepare_api_payload,
)

from dashboard.prediction_loader import (
    load_prediction_data,
    filter_prediction_data,
)


# ============================================================
# Plotly Dark Theme
# ============================================================

DARK_PLOT_LAYOUT = {
    "paper_bgcolor": "#0b1b2d",
    "plot_bgcolor": "#0b1b2d",
    "font": {
        "color": "#e8f1ff",
    },
    "xaxis": {
        "gridcolor": "rgba(120, 180, 255, 0.10)",
        "linecolor": "rgba(120, 180, 255, 0.20)",
        "zerolinecolor": "rgba(120, 180, 255, 0.15)",
    },
    "yaxis": {
        "gridcolor": "rgba(120, 180, 255, 0.10)",
        "linecolor": "rgba(120, 180, 255, 0.20)",
        "zerolinecolor": "rgba(120, 180, 255, 0.15)",
    },
}


# ============================================================
# Load Dashboard Datasets
# ============================================================

FEATURE_DATA = load_live_prediction_data()

PREDICTION_DATA = load_prediction_data()


# ============================================================
# Load Model Metrics
# ============================================================

def load_model_metrics():
    """
    Load model evaluation metrics generated
    during Week 8 evaluation.
    """

    with open(
        MODEL_METRICS_PATH,
        "r",
    ) as file:

        return json.load(file)


# ============================================================
# Register Callbacks
# ============================================================

def register_callbacks(app):
    """
    Register all dashboard callbacks.
    """


    # ========================================================
    # Populate City Dropdowns
    # ========================================================

    @app.callback(

        Output(
            "city-dropdown",
            "options",
        ),

        Output(
            "history-city-dropdown",
            "options",
        ),

        Input(
            "city-dropdown",
            "id",
        ),

    )
    def populate_city_dropdowns(_):
        """
        Populate dashboard city dropdowns.
        """

        feature_data = load_live_prediction_data()

        cities = get_available_cities(
            feature_data
        )

        options = [

            {
                "label": city,
                "value": city,
            }

            for city in cities

        ]

        return (
            options,
            options,
        )


    # ========================================================
    # Live Prediction
    # ========================================================

    @app.callback(

        Output(
            "latest-update",
            "children",
        ),

        Output(
            "current-temperature",
            "children",
        ),

        Output(
            "predicted-temperature",
            "children",
        ),

        Output(
            "prediction-difference",
            "children",
        ),

        Input(
            "city-dropdown",
            "value",
        ),

    )
    def update_live_prediction(city):
        """
        Update the live prediction KPI cards for the
        selected city.
        """

        if city is None:

            raise dash.exceptions.PreventUpdate


        # Get latest feature record

        feature_data = load_live_prediction_data()

        record = get_latest_record(
            feature_data,
            city,
        )

        if record is None:

            return (
                "Unavailable",
                "N/A",
                "N/A",
                "N/A",
            )


        # Prepare FastAPI payload

        payload = prepare_api_payload(
            record
        )

        try:

            prediction = request_prediction(
                payload
            )

        except Exception:

            return (
                record["time"].strftime(
                    "%d %b %Y %H:%M"
                ),
                f"{record['temperature']:.1f} °C",
                "Unavailable",
                "Prediction API Offline",
            )


        current_temperature = float(
            record["temperature"]
        )

        prediction_difference = round(
            prediction - current_temperature,
            2,
        )

        latest_timestamp = (
            record["time"].strftime(
                "%d %b %Y %H:%M"
            )
        )

        return (

            latest_timestamp,

            f"{current_temperature:.1f} °C",

            f"{prediction:.1f} °C",

            f"{prediction_difference:+.2f} °C",

        )


    # ========================================================
    # Historical Prediction
    # ========================================================

    @app.callback(

        Output(
            "prediction-table",
            "data",
        ),

        Output(
            "actual-vs-predicted-chart",
            "figure",
        ),

        Output(
            "prediction-error-chart",
            "figure",
        ),

        Input(
            "history-city-dropdown",
            "value",
        ),

        Input(
            "history-date-picker",
            "date",
        ),

    )
    def update_historical_prediction(
        city,
        selected_date,
    ):
        """
        Update the historical prediction table
        and performance charts.
        """

        # ----------------------------------------------------
        # Initial state: no city selected
        # ----------------------------------------------------

        if city is None:

            empty_figure = go.Figure()

            empty_figure.update_layout(
                title="Select a city to view prediction data",
                **DARK_PLOT_LAYOUT,
            )

            return (
                [],
                empty_figure,
                empty_figure,
            )


        # ----------------------------------------------------
        # Filter prediction dataset
        # ----------------------------------------------------

        prediction_data = load_prediction_data()

        filtered_df = filter_prediction_data(
            prediction_data,
            city,
            selected_date,
        )


        # ----------------------------------------------------
        # No prediction data available
        # ----------------------------------------------------

        if filtered_df.empty:

            empty_figure = go.Figure()

            empty_figure.update_layout(
                title="No prediction data available",
                **DARK_PLOT_LAYOUT,
            )

            return (
                [],
                empty_figure,
                empty_figure,
            )


        # ----------------------------------------------------
        # Prediction Table
        # ----------------------------------------------------

        table_df = filtered_df.copy()

        table_df["time"] = (
            table_df["time"]
            .dt.strftime("%Y-%m-%d %H:%M")
        )

        table_data = table_df.to_dict(
            "records"
        )


        # ----------------------------------------------------
        # Actual vs Predicted Chart
        # ----------------------------------------------------

        actual_chart = go.Figure()

        actual_chart.add_trace(

            go.Scatter(

                x=filtered_df["time"],

                y=filtered_df[
                    "target_temp_next_hour"
                ],

                mode="lines",

                name="Actual",

                line={
                    "color": "#7dd3fc",
                    "width": 2,
                },

            )

        )

        actual_chart.add_trace(

            go.Scatter(

                x=filtered_df["time"],

                y=filtered_df[
                    "predicted_temperature"
                ],

                mode="lines",

                name="Predicted",

                line={
                    "color": "#fb923c",
                    "width": 2,
                },

            )

        )

        actual_chart.update_layout(

            title="Actual vs Predicted Temperature",

            xaxis_title="Date",

            yaxis_title="Temperature (°C)",

            hovermode="x unified",

            **DARK_PLOT_LAYOUT,

        )


        # ----------------------------------------------------
        # Prediction Error Chart
        # ----------------------------------------------------

        error_chart = go.Figure()

        error_chart.add_trace(

            go.Bar(

                x=filtered_df["time"],

                y=filtered_df[
                    "prediction_error"
                ],

                name="Prediction Error",

                marker={
                    "color": "#818cf8",
                },

            )

        )

        error_chart.update_layout(

            title="Prediction Error",

            xaxis_title="Date",

            yaxis_title="Error (°C)",

            **DARK_PLOT_LAYOUT,

        )


        # ----------------------------------------------------
        # Return Results
        # ----------------------------------------------------

        return (

            table_data,

            actual_chart,

            error_chart,

        )


    # ========================================================
    # Model Information
    # ========================================================

    @app.callback(

        Output(
            "model-name",
            "children",
        ),

        Output(
            "model-r2",
            "children",
        ),

        Output(
            "model-rmse",
            "children",
        ),

        Output(
            "model-mae",
            "children",
        ),

        Output(
            "model-dataset",
            "children",
        ),

        Output(
            "model-trained-at",
            "children",
        ),

        Input(
            "city-dropdown",
            "value",
        ),

    )
    def update_model_information(_):
        """
        Display model information from the latest
        Week 8 evaluation.
        """

        metrics = load_model_metrics()

        model_name = metrics["model_name"]

        r2_score = (
            f"{metrics['r2']:.2f}"
        )

        rmse = (
            f"{metrics['rmse']:.2f} °C"
        )

        mae = (
            f"{metrics['mae']:.2f} °C"
        )

        dataset = (
            f"{metrics['training_rows']:,} "
            "engineered feature records"
        )

        trained_at = (
            metrics["trained_at"]
        )

        return (
            model_name,
            r2_score,
            rmse,
            mae,
            dataset,
            trained_at,
        )