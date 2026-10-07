from src.evaluate import evaluate_model
from src.prepare_data import prepare_data
from src.train_linear_regression import train_linear_regression
from src.train_random_forest import train_random_forest


def main():
    print("=" * 60)
    print("P2-W7 Spark MLlib Pipeline")
    print("=" * 60)

    print("\n[1/4] Preparing MLlib dataset...")
    prepare_data()

    print("\n[2/4] Training Linear Regression...")
    train_linear_regression()

    print("\n[3/4] Training Random Forest...")
    train_random_forest()

    print("\n[4/4] Evaluating MLlib models...")
    evaluate_model()

    print("\n" + "=" * 60)
    print("P2-W7 Spark MLlib pipeline completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()