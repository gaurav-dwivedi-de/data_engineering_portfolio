# W8 - MODEL EVALUATION SCRIPT
# Goal:
# Generate evaluation visualizations for the
# selected model using the test dataset.
#
# This script:
# - Loads the saved best model and scaler
# - Recreates the test dataset
# - Generates prediction visualizations
# - Saves evaluation figures


# IMPORT LIBRARIES


import pandas as pd
import matplotlib.pyplot as plt
import joblib

from .config import (
    DATA_PATH,
    TARGET_COLUMN,
    RANDOM_STATE,
    TEST_SIZE,
    CANDIDATE_BEST_MODEL_PATH,
    CANDIDATE_SCALER_PATH,
    ACTUAL_VS_PREDICTED_FIGURE,
    RESIDUAL_DISTRIBUTION_FIGURE
)


# LOAD DATASET
# Read the processed Week 7 feature dataset.


print("Loading dataset...")

df = pd.read_parquet(DATA_PATH)

print("Dataset loaded successfully.")

print("\nDataset Shape:")
print(df.shape)


# REMOVE MISSING VALUES
# Remove incomplete records before evaluation.


df = df.dropna()

print("\nDataset Shape After Dropping Nulls:")
print(df.shape)



# PREPARE CHRONOLOGICAL TRAIN / TEST DATA
# Recreate the same chronological split used
# during model training.

print("\nPreparing chronological train/test split...")

df["time"] = pd.to_datetime(df["time"])

df = df.sort_values(
    "time"
).reset_index(drop=True)

# Get unique timestamps
timestamps = (
    df["time"]
    .drop_duplicates()
    .sort_values()
    .reset_index(drop=True)
)

# Calculate split boundary
split_index = int(
    len(timestamps) * (1 - TEST_SIZE)
)

if split_index == 0 or split_index >= len(timestamps):
    raise ValueError(
        "Insufficient timestamps for chronological splitting."
    )

# Separate training and testing timestamps
train_timestamps = timestamps.iloc[:split_index]
test_timestamps = timestamps.iloc[split_index:]

# Create training and testing datasets
train_df = df[
    df["time"].isin(train_timestamps)
].copy()

test_df = df[
    df["time"].isin(test_timestamps)
].copy()

# Separate features and target
X_train = train_df.drop(
    columns=[
        TARGET_COLUMN,
        "time"
    ]
)

X_test = test_df.drop(
    columns=[
        TARGET_COLUMN,
        "time"
    ]
)

y_test = test_df[TARGET_COLUMN]

# Validate chronological separation
if train_df["time"].max() >= test_df["time"].min():
    raise ValueError(
        "Chronological split validation failed."
    )

print("\nChronological Split Recreated")

print("Training Period:")
print(
    train_df["time"].min(),
    "to",
    train_df["time"].max()
)

print("Testing Period:")
print(
    test_df["time"].min(),
    "to",
    test_df["time"].max()
)

print(f"\nTraining Rows: {len(train_df)}")
print(f"Testing Rows : {len(test_df)}")

print(f"X_train Shape: {X_train.shape}")
print(f"X_test Shape : {X_test.shape}")
print(f"y_test Shape : {y_test.shape}")



# LOAD SCALER
# Load the saved scaler used during training.


print("\nLoading scaler...")

scaler = joblib.load(
    CANDIDATE_SCALER_PATH
)

print("Scaler loaded successfully.")


# SCALE FEATURES
# Apply the saved scaler to numerical features.


numerical_columns = X_train.select_dtypes(
    include=["number"]
).columns

X_train = X_train.copy()
X_test = X_test.copy()

X_train[numerical_columns] = scaler.transform(
    X_train[numerical_columns]
)

X_test[numerical_columns] = scaler.transform(
    X_test[numerical_columns]
)


# LOAD BEST MODEL
# Load the selected model for evaluation.


print("\nLoading best model...")

model = joblib.load(
    CANDIDATE_BEST_MODEL_PATH
)

print("Best model loaded successfully.")


# MAKE PREDICTIONS
# Generate predictions using the saved model.


predictions = model.predict(
    X_test
)

# ACTUAL VS PREDICTED PLOT
# Compare the predicted values against
# the actual target values.


plt.figure(figsize=(8, 6))

plt.scatter(
    y_test,
    predictions
)

plt.xlabel("Actual Values")

plt.ylabel("Predicted Values")

plt.title("Actual vs Predicted")

plt.tight_layout()

plt.savefig(
    ACTUAL_VS_PREDICTED_FIGURE,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(
    f"\nSaved: "
    f"{ACTUAL_VS_PREDICTED_FIGURE}"
)


# RESIDUAL DISTRIBUTION
# Visualize the prediction errors to
# assess model performance.


residuals = (
    y_test -
    predictions
)

plt.figure(figsize=(8, 6))

plt.hist(
    residuals,
    bins=30
)

plt.xlabel("Residual Error")

plt.ylabel("Frequency")

plt.title("Residual Distribution")

plt.tight_layout()

plt.savefig(
    RESIDUAL_DISTRIBUTION_FIGURE,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(
    f"Saved: "
    f"{RESIDUAL_DISTRIBUTION_FIGURE}"
)


# SUMMARY
# Confirm that the evaluation figures
# were generated successfully.


print("\n" + "=" * 60)
print("EVALUATION VISUALIZATIONS COMPLETED")
print("=" * 60)

print(f"Best Model               : {CANDIDATE_BEST_MODEL_PATH}")
print(f"Actual vs Predicted Plot : {ACTUAL_VS_PREDICTED_FIGURE}")
print(f"Residual Distribution    : {RESIDUAL_DISTRIBUTION_FIGURE}")

print("\nWeek 8 evaluation completed successfully.")
