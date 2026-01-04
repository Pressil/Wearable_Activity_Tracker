import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
import joblib

print("Loading dataset...")
df = pd.read_csv('dataset.csv')


WINDOW_SIZE = 30  
print(f"Grouping data into windows of {WINDOW_SIZE} readings...")

X_windows = []
y_windows = []

for i in range(0, len(df) - WINDOW_SIZE, WINDOW_SIZE):
    window = df.iloc[i : i + WINDOW_SIZE]

    features = [
        window['acceleration_x'].mean(), window['acceleration_x'].std(),
        window['acceleration_y'].mean(), window['acceleration_y'].std(),
        window['acceleration_z'].mean(), window['acceleration_z'].std(),
        window['gyro_x'].mean(),         window['gyro_x'].std(),
        window['gyro_y'].mean(),         window['gyro_y'].std(),
        window['gyro_z'].mean(),         window['gyro_z'].std()
    ]

    X_windows.append(features)

    label = window['activity'].mode()[0]
    y_windows.append(label)

X = np.array(X_windows)
y = np.array(y_windows)

print(f"Created {len(X)} windows.")
print("Unique labels in activity:", np.unique(y))

print("Splitting into train and test sets...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Training Random Forest Classifier (lightweight)...")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=None,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred, labels=np.unique(y))

print(f"Model Accuracy: {acc * 100:.2f}%")
print("Confusion Matrix (rows=true, cols=pred):")
print("Labels order:", np.unique(y))
print(cm)

joblib.dump(model, 'activity_model.pkl')
joblib.dump(np.unique(y), 'activity_labels.pkl')

print("Model saved as 'activity_model.pkl'")
print("Label set saved as 'activity_labels.pkl'")
print("Training complete.")
