from ultralytics import YOLO

# Load trained model
model = YOLO("best.pt")

# Test image
image_path = "cnc_anomoly_f1.jpg"

# Predict
results = model(image_path)

# Display results
for result in results:
    print("\nPrediction Results:")
    
    if hasattr(result, "probs") and result.probs is not None:
        probs = result.probs.data.tolist()
        class_names = result.names

        predicted_class = probs.index(max(probs))

        print(f"Predicted Class: {class_names[predicted_class]}")
        print(f"Confidence: {max(probs):.4f}")