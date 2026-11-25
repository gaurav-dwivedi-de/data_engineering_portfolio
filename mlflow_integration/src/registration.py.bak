"""Conditional MLflow model registration for the Weather Intelligence Platform.

The comparison function is deliberately independent of MLflow so its rules can
be unit-tested without contacting the tracking server or changing the registry.
"""

from __future__ import annotations
import mlflow
import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping

MODEL_REGISTRY = {
    "sklearn_linear_regression": "weather-intelligence-sklearn-linear-regression",
    "sklearn_random_forest": "weather-intelligence-sklearn-random-forest",
    "spark_linear_regression": "weather-intelligence-spark-linear-regression",
    "spark_random_forest": "weather-intelligence-spark-random-forest",
}

REQUIRED_METRICS = ("mae", "rmse", "r2")
MAE_MIN_IMPROVEMENT = 0.01
RMSE_MAX_INCREASE = 0.0
R2_MAX_DECREASE = 0.005


@dataclass(frozen=True)
class ComparisonResult:
    accepted: bool
    reasons: tuple[str, ...]
    candidate_metrics: dict[str, float]
    incumbent_metrics: dict[str, float]
    mae_improvement: float | None
    rmse_change: float | None
    r2_change: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalise_metrics(metrics: Mapping[str, Any], label: str) -> dict[str, float]:
    """Validate and normalise the three metrics required by the policy."""
    normalised: dict[str, float] = {}
    for metric in REQUIRED_METRICS:
        if metric not in metrics:
            raise ValueError(f"{label} is missing required metric: {metric}")
        try:
            value = float(metrics[metric])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} metric {metric} must be numeric") from exc
        if not math.isfinite(value):
            raise ValueError(f"{label} metric {metric} must be finite")
        if metric in {"mae", "rmse"} and value < 0:
            raise ValueError(f"{label} metric {metric} cannot be negative")
        normalised[metric] = value
    return normalised


def compare_metrics(
    candidate_metrics: Mapping[str, Any],
    incumbent_metrics: Mapping[str, Any],
    *,
    candidate_dataset_id: str,
    incumbent_dataset_id: str,
    candidate_protocol: str,
    incumbent_protocol: str,
) -> ComparisonResult:
    """Apply the registration gate to metrics measured on identical validation data.

    Acceptance requires:
    - candidate MAE to improve by at least 1%;
    - candidate RMSE not to increase;
    - candidate R² not to decrease by more than 0.005.

    Dataset and protocol identifiers are mandatory to prevent comparison of
    metrics produced using different validation data or evaluation procedures.
    """
    candidate = _normalise_metrics(candidate_metrics, "Candidate")
    incumbent = _normalise_metrics(incumbent_metrics, "Incumbent")
    reasons: list[str] = []

    if not candidate_dataset_id or not incumbent_dataset_id:
        reasons.append("Validation dataset identifiers must both be provided")
    elif candidate_dataset_id != incumbent_dataset_id:
        reasons.append("Candidate and incumbent were not evaluated on the same dataset")

    if not candidate_protocol or not incumbent_protocol:
        reasons.append("Evaluation protocol identifiers must both be provided")
    elif candidate_protocol != incumbent_protocol:
        reasons.append("Candidate and incumbent used different evaluation protocols")

    mae_improvement = (
        (incumbent["mae"] - candidate["mae"]) / incumbent["mae"]
        if incumbent["mae"] > 0
        else (0.0 if candidate["mae"] == 0 else -math.inf)
    )
    rmse_change = candidate["rmse"] - incumbent["rmse"]
    r2_change = candidate["r2"] - incumbent["r2"]

    if mae_improvement < MAE_MIN_IMPROVEMENT:
        reasons.append(
            f"MAE improvement {mae_improvement:.2%} is below the required "
            f"{MAE_MIN_IMPROVEMENT:.0%}"
        )
    if rmse_change > RMSE_MAX_INCREASE + 1e-12:
        reasons.append("RMSE increased")
    if r2_change < -R2_MAX_DECREASE - 1e-12:
        reasons.append(
            f"R² decreased by {-r2_change:.6f}, exceeding the allowed "
            f"{R2_MAX_DECREASE:.6f}"
        )

    return ComparisonResult(
        accepted=not reasons,
        reasons=tuple(reasons) if reasons else ("All registration conditions passed",),
        candidate_metrics=candidate,
        incumbent_metrics=incumbent,
        mae_improvement=mae_improvement,
        rmse_change=rmse_change,
        r2_change=r2_change,
    )


def register_candidate(
    *,
    client: Any,
    registered_model_name: str,
    model_uri: str,
    evaluation_run_id: str,
    comparison: ComparisonResult,
    validation_dataset_id: str,
    evaluation_protocol: str,
) -> Any | None:
    """Register a logged candidate model only when the comparison was accepted.

    `model_uri` must point to a model already logged to MLflow. This function
    does not train or log the model. A source evaluation run can create at most
    one registered version through this helper.
    """
    if not comparison.accepted:
        return None

    if not all((
        registered_model_name,
        model_uri,
        evaluation_run_id,
        validation_dataset_id,
        evaluation_protocol,
    )):
        raise ValueError("Registration identifiers and model_uri are required")

    existing_versions = client.search_model_versions(
        f"name='{registered_model_name}'"
    )

    for version in existing_versions:
        if version.tags.get("source_evaluation_run_id") == evaluation_run_id:
            return version

    model_id = None

    if model_uri.startswith("models:/m-"):
        model_id = model_uri.removeprefix("models:/").split("/", 1)[0]

    version = client.create_model_version(
        name=registered_model_name,
        source=model_uri,
        run_id=evaluation_run_id,
        tags={
            "registration_type": "conditional",
            "source_evaluation_run_id": evaluation_run_id,
            "validation_dataset_id": validation_dataset_id,
            "evaluation_protocol": evaluation_protocol,
            "comparison_policy": "mae_1pct_rmse_non_increasing_r2_tolerance_0.005",
        },
        model_id=model_id,
        await_creation_for=300,
    )

    return version
@dataclass
class RegisteredModel:
    model_key: str
    registered_model_name: str
    version: str
    run_id: str | None
    model_uri: str
    model: Any

def get_latest_registered_version(
    client: Any,
    registered_model_name: str,
) -> Any:
    """Retrieve the latest READY version of a registered model."""
    versions = client.search_model_versions(
        f"name='{registered_model_name}'"
    )

    ready_versions = [
        version for version in versions
        if version.status == "READY"
    ]

    if not ready_versions:
        raise RuntimeError(
            f"No READY versions found for {registered_model_name}"
        )

    return max(ready_versions, key=lambda version: int(version.version))

def get_champion_version(
    client: Any,
    registered_model_name: str,
) -> Any:
    """Retrieve the READY production version assigned the champion alias."""
    try:
        version = client.get_model_version_by_alias(
            registered_model_name,
            "champion",
        )
    except Exception as exc:
        raise RuntimeError(
            f"No champion alias found for {registered_model_name}"
        ) from exc

    if version.status != "READY":
        raise RuntimeError(
            f"Champion version {version.version} for "
            f"{registered_model_name} is not READY"
        )

    return version


def load_incumbent_model(
    *,
    client: Any,
    model_key: str,
    spark: Any = None,
) -> RegisteredModel:
    """Load the champion production model using its framework-specific flavor."""
    if model_key not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model key: {model_key}")

    registered_model_name = MODEL_REGISTRY[model_key]

    version = get_champion_version(
        client,
        registered_model_name,
    )

    model_uri = f"models:/{registered_model_name}/{version.version}"

    if model_key.startswith("sklearn_"):
        model = mlflow.sklearn.load_model(model_uri)

    elif model_key.startswith("spark_"):
        if spark is None:
            raise ValueError(
                "An active SparkSession must be supplied for Spark models"
            )
        model = mlflow.spark.load_model(model_uri)

    else:
        raise ValueError(f"Unsupported model framework: {model_key}")

    return RegisteredModel(
        model_key=model_key,
        registered_model_name=registered_model_name,
        version=version.version,
        run_id=version.run_id,
        model_uri=model_uri,
        model=model,
    )
def promote_candidate(
    *,
    client: Any,
    registered_model_name: str,
    version: str,
    comparison: ComparisonResult,
) -> Any:
    """Promote an accepted READY model version to the champion alias."""

    if not comparison.accepted:
        raise ValueError(
            "Cannot promote a candidate that failed the comparison policy"
        )

    if not registered_model_name or not version:
        raise ValueError(
            "Registered model name and version are required"
        )

    candidate = client.get_model_version(
        name=registered_model_name,
        version=str(version),
    )

    if candidate.name != registered_model_name:
        raise RuntimeError(
            "Retrieved model version does not match the requested model"
        )

    if str(candidate.version) != str(version):
        raise RuntimeError(
            "Retrieved model version does not match the requested version"
        )

    if candidate.status != "READY":
        raise RuntimeError(
            f"Cannot promote model version {version}: "
            f"status is {candidate.status}"
        )

    client.set_registered_model_alias(
        name=registered_model_name,
        alias="champion",
        version=str(version),
    )

    promoted = client.get_model_version_by_alias(
        registered_model_name,
        "champion",
    )

    if (
        promoted.name != registered_model_name
        or str(promoted.version) != str(version)
        or promoted.status != "READY"
    ):
        raise RuntimeError(
            "Champion alias verification failed after promotion"
        )

    return promoted