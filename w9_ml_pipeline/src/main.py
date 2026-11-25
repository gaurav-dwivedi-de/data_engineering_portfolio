
from .load_model import load_model
from .load_features import load_features
from .predict import predict
from .save_predictions import save_predictions
from .evaluate_predictions import evaluate_predictions


def main():
    """
    Execute the Week 9 MLflow production inference pipeline.
    """

    try:
        print("\nLoading MLflow production champion...")
        model, feature_columns = load_model()

        print("\nLoading feature dataset...")
        features_df = load_features()

        print("\nGenerating predictions...")
        prediction_df = predict(
            model,
            features_df,
            feature_columns,
        )

        print("\nEvaluating predictions...")
        metrics = evaluate_predictions(prediction_df)

        print("\nSaving prediction files...")
        save_predictions(prediction_df)

        print("\n" + "=" * 60)
        print("WEEK 9 PIPELINE SUMMARY")
        print("=" * 60)

        print(f"Prediction Records : {len(prediction_df)}")
        print(f"MAE                : {metrics['MAE']:.2f}")
        print(f"RMSE               : {metrics['RMSE']:.2f}")
        print(f"R²                 : {metrics['R2']:.2f}")

        print("\nFirst Five Predictions")
        print(prediction_df.head())

        print("\nWeek 9 ML Pipeline completed successfully.")

    except Exception as error:
        print("\nPipeline failed.")
        print(error)
        raise


if __name__ == "__main__":
    main()
