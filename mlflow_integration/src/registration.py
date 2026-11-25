"""Conditional MLflow model registration for the Weather Intelligence Platform.

The comparison function is deliberately independent of MLflow so its rules can
be unit-tested without contacting the tracking server or changing the registry.
"""

from __future__ import annotations
import mlflow
import numpy as np
from mlflow.exceptions import MlflowException
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

# GLOBAL PRODUCTION MODEL SELECTION

GLOBAL_PRODUCTION_MODEL = "weather-production-model"
GLOBAL_CHAMPION_ALIAS = "champion"
GLOBAL_SELECTION_POLICY = "lowest_mae_then_lowest_rmse_then_highest_r2"


def get_eligible_production_candidates(
    *,
    client: Any,
    validation_dataset_id: str,
    evaluation_protocol: str,
    evaluation_run_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Return READY registered versions evaluated on the specified dataset
    and protocol, where the source evaluation run was eligible for registration.
    """
    if not validation_dataset_id or not evaluation_protocol:
        raise ValueError(
            "Validation dataset ID and evaluation protocol are required."
        )

    eligible: list[dict[str, Any]] = []

    for model_key, model_name in MODEL_REGISTRY.items():
        versions = client.search_model_versions(f"name='{model_name}'")

        for version in versions:
            version_tags = version.tags or {}

            if version.status != "READY":
                continue

            if (
                version_tags.get("validation_dataset_id")
                != validation_dataset_id
            ):
                continue

            if (
                version_tags.get("evaluation_protocol")
                != evaluation_protocol
            ):
                continue

            evaluation_run_id = version_tags.get(
                "source_evaluation_run_id"
            )
            if not evaluation_run_id:
                continue

            if (
                evaluation_run_ids is not None
                and evaluation_run_id not in evaluation_run_ids
            ):
                continue

            run = client.get_run(evaluation_run_id)
            run_tags = run.data.tags or {}

            if run.info.status != "FINISHED":
                continue

            if run_tags.get("evaluation_type") != "candidate_evaluation":
                continue

            if run_tags.get("registration_eligible", "").lower() != "true":
                continue

            if run_tags.get("model_key") != model_key:
                continue

            if run_tags.get("registered_model_name") != model_name:
                continue

            if run_tags.get("validation_dataset_id") != validation_dataset_id:
                continue

            if run_tags.get("evaluation_protocol") != evaluation_protocol:
                continue

            if str(version.run_id) != str(evaluation_run_id):
                continue

            run_metrics = run.data.metrics or {}
            metric_values = {
                "mae": run_metrics.get("candidate_mae"),
                "rmse": run_metrics.get("candidate_rmse"),
                "r2": run_metrics.get("candidate_r2"),
            }

            if any(value is None for value in metric_values.values()):
                continue

            try:
                metrics = _normalise_metrics(
                    metric_values,
                    f"{model_key} version {version.version}",
                )
            except ValueError:
                continue

            eligible.append({
                "model_key": model_key,
                "registered_model_name": model_name,
                "version": str(version.version),
                "run_id": evaluation_run_id,
                "validation_dataset_id": validation_dataset_id,
                "evaluation_protocol": evaluation_protocol,
                "metrics": metrics,
                "source": version.source,
            })

    return eligible


def select_global_champion(
    *,
    client: Any,
    validation_dataset_id: str,
    evaluation_protocol: str,
    evaluation_run_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Select the best eligible candidate without changing the registry."""
    candidates = get_eligible_production_candidates(
        client=client,
        validation_dataset_id=validation_dataset_id,
        evaluation_protocol=evaluation_protocol,
        evaluation_run_ids=evaluation_run_ids,
    )

    if not candidates:
        raise RuntimeError(
            "No eligible registered candidates found for the requested "
            "validation dataset and evaluation protocol."
        )

    candidates.sort(
        key=lambda candidate: (
            candidate["metrics"]["mae"],
            candidate["metrics"]["rmse"],
            -candidate["metrics"]["r2"],
            candidate["registered_model_name"],
            -int(candidate["version"]),
        )
    )

    selected = candidates[0].copy()
    selected["eligible_candidate_count"] = len(candidates)
    selected["selection_policy"] = GLOBAL_SELECTION_POLICY
    return selected


def compare_global_candidate_to_champion(
    *,
    client: Any,
    selected_candidate: Mapping[str, Any],
) -> ComparisonResult:
    """Compare a selected candidate against the current global champion."""

    try:
        incumbent = client.get_model_version_by_alias(
            GLOBAL_PRODUCTION_MODEL,
            GLOBAL_CHAMPION_ALIAS,
        )
    except Exception as exc:
        raise RuntimeError(
            "The global production champion alias is unavailable. "
            "Refusing to promote without an incumbent."
        ) from exc

    if incumbent.status != "READY":
        raise RuntimeError(
            f"Global champion version {incumbent.version} is not READY."
        )

    incumbent_tags = incumbent.tags or {}

    if incumbent_tags.get("registration_type") != "global_production":
        raise RuntimeError(
            "The current champion is not tagged as a global production model."
        )

    required_tags = (
        "validation_dataset_id",
        "evaluation_protocol",
        "selected_mae",
        "selected_rmse",
        "selected_r2",
    )

    missing_tags = [
        tag for tag in required_tags
        if not incumbent_tags.get(tag)
    ]

    if missing_tags:
        raise RuntimeError(
            "The current global champion is missing required metadata: "
            + ", ".join(missing_tags)
        )

    return compare_metrics(
        candidate_metrics=selected_candidate["metrics"],
        incumbent_metrics={
            "mae": incumbent_tags["selected_mae"],
            "rmse": incumbent_tags["selected_rmse"],
            "r2": incumbent_tags["selected_r2"],
        },
        candidate_dataset_id=selected_candidate["validation_dataset_id"],
        incumbent_dataset_id=incumbent_tags["validation_dataset_id"],
        candidate_protocol=selected_candidate["evaluation_protocol"],
        incumbent_protocol=incumbent_tags["evaluation_protocol"],
    )



def validate_global_model_version(
    *,
    client: Any,
    version: str,
    feature_sample: Any,
    expected_feature_columns: list[str],
) -> dict[str, Any]:
    """Validate a global model's registry state, signature and inference."""

    if not version:
        raise ValueError("A global model version is required.")

    if feature_sample is None or feature_sample.empty:
        raise ValueError("Inference validation requires a non-empty feature sample.")

    if not expected_feature_columns:
        raise ValueError("Expected feature columns must be provided.")

    actual_columns = list(feature_sample.columns)

    if actual_columns != expected_feature_columns:
        raise ValueError(
            "Feature sample columns or order do not match the expected schema."
        )

    candidate = client.get_model_version(
        name=GLOBAL_PRODUCTION_MODEL,
        version=str(version),
    )

    if candidate.status != "READY":
        raise RuntimeError(
            f"Global model version {version} is not READY."
        )

    tags = candidate.tags or {}

    if tags.get("registration_type") != "global_production":
        raise RuntimeError(
            "Model version is not registered as a global production model."
        )

    model_uri = f"models:/{GLOBAL_PRODUCTION_MODEL}/{version}"
    model_info = mlflow.models.get_model_info(model_uri)
    signature = model_info.signature

    if signature is None or signature.inputs is None:
        raise RuntimeError("Global model is missing an input signature.")

    signature_columns = signature.inputs.input_names()

    if signature_columns != expected_feature_columns:
        raise RuntimeError(
            "Model signature does not match the expected 27-feature schema."
        )

    model = mlflow.pyfunc.load_model(model_uri)
    predictions = np.asarray(
        model.predict(feature_sample)
    ).reshape(-1)

    if len(predictions) != len(feature_sample):
        raise RuntimeError(
            "Inference output row count does not match the input row count."
        )

    if not np.isfinite(predictions).all():
        raise RuntimeError(
            "Inference produced non-finite predictions."
        )

    return {
        "model_name": GLOBAL_PRODUCTION_MODEL,
        "version": str(version),
        "model_uri": model_uri,
        "feature_count": len(expected_feature_columns),
        "inference_rows": len(feature_sample),
        "prediction_count": len(predictions),
        "signature_valid": True,
        "inference_valid": True,
    }


def register_global_champion(
    *,
    client: Any,
    selected_candidate: Mapping[str, Any],
) -> Any:
    """Register the selected source model version under the global model name."""
    required_fields = (
        "registered_model_name",
        "version",
        "run_id",
        "validation_dataset_id",
        "evaluation_protocol",
        "metrics",
    )

    if any(not selected_candidate.get(field) for field in required_fields):
        raise ValueError("Selected candidate is missing required metadata.")

    source_name = str(selected_candidate["registered_model_name"])
    source_version = str(selected_candidate["version"])
    source = client.get_model_version(
        name=source_name,
        version=source_version,
    )

    if source.status != "READY":
        raise RuntimeError("Selected source model version is not READY.")

    source_tags = source.tags or {}

    if (
        source_tags.get("validation_dataset_id")
        != selected_candidate["validation_dataset_id"]
    ):
        raise RuntimeError("Source model validation dataset does not match.")

    if (
        source_tags.get("evaluation_protocol")
        != selected_candidate["evaluation_protocol"]
    ):
        raise RuntimeError("Source model evaluation protocol does not match.")

    if (
        source_tags.get("source_evaluation_run_id")
        != selected_candidate["run_id"]
    ):
        raise RuntimeError("Source evaluation run does not match.")

    existing_versions = client.search_model_versions(
        f"name='{GLOBAL_PRODUCTION_MODEL}'"
    )

    for existing in existing_versions:
        tags = existing.tags or {}
        if (
            tags.get("source_model_name") == source_name
            and tags.get("source_model_version") == source_version
            and tags.get("source_evaluation_run_id")
            == selected_candidate["run_id"]
        ):
            return existing

    try:
        client.get_registered_model(GLOBAL_PRODUCTION_MODEL)
    except MlflowException:
        client.create_registered_model(GLOBAL_PRODUCTION_MODEL)

    model_uri = source.source
    if not model_uri:
        raise RuntimeError("Selected source model has no model URI.")

    create_kwargs = {
        "name": GLOBAL_PRODUCTION_MODEL,
        "source": model_uri,
        "run_id": selected_candidate["run_id"],
        "tags": {
            "registration_type": "global_production",
            "source_model_name": source_name,
            "source_model_version": source_version,
            "source_evaluation_run_id": selected_candidate["run_id"],
            "validation_dataset_id": selected_candidate[
                "validation_dataset_id"
            ],
            "evaluation_protocol": selected_candidate[
                "evaluation_protocol"
            ],
            "selection_policy": GLOBAL_SELECTION_POLICY,
            "selected_model_key": selected_candidate.get("model_key", ""),
            "selected_mae": str(selected_candidate["metrics"]["mae"]),
            "selected_rmse": str(selected_candidate["metrics"]["rmse"]),
            "selected_r2": str(selected_candidate["metrics"]["r2"]),
        },
        "await_creation_for": 300,
    }

    if model_uri.startswith("models:/m-"):
        create_kwargs["model_id"] = (
            model_uri.removeprefix("models:/").split("/", 1)[0]
        )

    return client.create_model_version(**create_kwargs)


def promote_global_champion(
    *,
    client: Any,
    version: str,
) -> Any:
    """Assign and verify the global production champion alias."""
    if not version:
        raise ValueError("A global production model version is required.")

    candidate = client.get_model_version(
        name=GLOBAL_PRODUCTION_MODEL,
        version=str(version),
    )

    if candidate.status != "READY":
        raise RuntimeError(
            f"Cannot promote global version {version}: "
            f"status is {candidate.status}."
        )

    tags = candidate.tags or {}
    if tags.get("registration_type") != "global_production":
        raise RuntimeError(
            "The requested version is not registered as a global production model."
        )

    client.set_registered_model_alias(
        name=GLOBAL_PRODUCTION_MODEL,
        alias=GLOBAL_CHAMPION_ALIAS,
        version=str(version),
    )

    promoted = client.get_model_version_by_alias(
        GLOBAL_PRODUCTION_MODEL,
        GLOBAL_CHAMPION_ALIAS,
    )

    if (
        promoted.name != GLOBAL_PRODUCTION_MODEL
        or str(promoted.version) != str(version)
        or promoted.status != "READY"
    ):
        raise RuntimeError("Global champion alias verification failed.")

    return promoted
