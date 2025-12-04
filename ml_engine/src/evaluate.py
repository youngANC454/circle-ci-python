import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
    mean_squared_error, mean_absolute_error, r2_score
)
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluate trained ML models"""
    
    def __init__(self):
        self.results = {}
    
    def evaluate_classifier(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_pred_proba: np.ndarray = None,
        model_name: str = "Classifier"
    ) -> Dict:
        """
        Evaluate classification model
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Predicted probabilities (optional)
            model_name: Name of the model
        
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info(f"Evaluating {model_name}...")
        
        # Basic metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average='binary', zero_division=0)
        recall = recall_score(y_true, y_pred, average='binary', zero_division=0)
        f1 = f1_score(y_true, y_pred, average='binary', zero_division=0)
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()
        
        results = {
            'model_name': model_name,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'true_positives': int(tp),
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'confusion_matrix': cm
        }
        
        # Print results
        logger.info(f"\n{'='*50}")
        logger.info(f"{model_name} Evaluation Results")
        logger.info(f"{'='*50}")
        logger.info(f"Accuracy:  {accuracy:.4f}")
        logger.info(f"Precision: {precision:.4f}")
        logger.info(f"Recall:    {recall:.4f}")
        logger.info(f"F1 Score:  {f1:.4f}")
        logger.info(f"\nConfusion Matrix:")
        logger.info(f"  TN: {tn:4d} | FP: {fp:4d}")
        logger.info(f"  FN: {fn:4d} | TP: {tp:4d}")
        
        # Classification report
        logger.info(f"\nDetailed Classification Report:")
        logger.info(f"\n{classification_report(y_true, y_pred)}")
        
        self.results[model_name] = results
        return results
    
    def evaluate_regressor(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_name: str = "Regressor"
    ) -> Dict:
        """
        Evaluate regression model
        
        Args:
            y_true: True values
            y_pred: Predicted values
            model_name: Name of the model
        
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info(f"Evaluating {model_name}...")
        
        # Calculate metrics
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
        
        results = {
            'model_name': model_name,
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2_score': r2,
            'mape': mape
        }
        
        # Print results
        logger.info(f"\n{'='*50}")
        logger.info(f"{model_name} Evaluation Results")
        logger.info(f"{'='*50}")
        logger.info(f"MSE:        {mse:.2f}")
        logger.info(f"RMSE:       {rmse:.2f}")
        logger.info(f"MAE:        {mae:.2f}")
        logger.info(f"R² Score:   {r2:.4f}")
        logger.info(f"MAPE:       {mape:.2f}%")
        
        self.results[model_name] = results
        return results
    
    def plot_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        save_path: str = None
    ):
        """Plot confusion matrix"""
        cm = confusion_matrix(y_true, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=['Success', 'Failure'],
            yticklabels=['Success', 'Failure']
        )
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Confusion matrix saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_prediction_distribution(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        save_path: str = None
    ):
        """Plot prediction vs actual distribution (for regression)"""
        plt.figure(figsize=(10, 6))
        
        plt.subplot(1, 2, 1)
        plt.scatter(y_true, y_pred, alpha=0.5)
        plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
        plt.xlabel('Actual Values')
        plt.ylabel('Predicted Values')
        plt.title('Predictions vs Actual')
        
        plt.subplot(1, 2, 2)
        residuals = y_true - y_pred
        plt.hist(residuals, bins=30, edgecolor='black')
        plt.xlabel('Residuals')
        plt.ylabel('Frequency')
        plt.title('Residual Distribution')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Prediction distribution saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def save_results(self, output_dir: str = "data/models"):
        """Save evaluation results to file"""
        os.makedirs(output_dir, exist_ok=True)
        
        results_file = os.path.join(output_dir, "evaluation_results.txt")
        
        with open(results_file, 'w') as f:
            f.write("="*60 + "\n")
            f.write("MODEL EVALUATION RESULTS\n")
            f.write("="*60 + "\n\n")
            
            for model_name, results in self.results.items():
                f.write(f"\n{model_name}:\n")
                f.write("-"*40 + "\n")
                
                for metric, value in results.items():
                    if metric not in ['confusion_matrix', 'model_name']:
                        f.write(f"{metric:20s}: {value}\n")
                
                f.write("\n")
        
        logger.info(f"Evaluation results saved to {results_file}")


def evaluate_failure_model(
    model_path: str = "data/models/failure_model.pkl",
    test_data_path: str = "data/processed/test_data.csv"
):
    """Evaluate failure prediction model"""
    logger.info("Loading failure prediction model...")
    
    # Load model
    if not os.path.exists(model_path):
        logger.error(f"Model not found: {model_path}")
        return
    
    model_data = joblib.load(model_path)
    model = model_data['model']
    scaler = model_data['scaler']
    
    # Load test data
    if not os.path.exists(test_data_path):
        logger.error(f"Test data not found: {test_data_path}")
        return
    
    test_df = pd.read_csv(test_data_path)
    
    # Prepare features
    feature_cols = [
        'recent_success_rate', 'recent_failure_count', 'error_count',
        'warning_count', 'total_lines', 'error_compilation',
        'error_runtime', 'error_test', 'error_timeout', 'error_memory'
    ]
    
    X_test = test_df[feature_cols].fillna(0)
    y_test = test_df['is_failed']
    
    # Scale features
    X_test_scaled = scaler.transform(X_test)
    
    # Make predictions
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    # Evaluate
    evaluator = ModelEvaluator()
    evaluator.evaluate_classifier(y_test, y_pred, y_pred_proba, "Failure Predictor")
    
    # Plot confusion matrix
    evaluator.plot_confusion_matrix(
        y_test, y_pred,
        save_path="data/models/failure_confusion_matrix.png"
    )
    
    # Save results
    evaluator.save_results()


def evaluate_duration_model(
    model_path: str = "data/models/duration_model.pkl",
    test_data_path: str = "data/processed/test_data.csv"
):
    """Evaluate duration prediction model"""
    logger.info("Loading duration prediction model...")
    
    # Load model
    if not os.path.exists(model_path):
        logger.error(f"Model not found: {model_path}")
        return
    
    model_data = joblib.load(model_path)
    model = model_data['model']
    scaler = model_data['scaler']
    
    # Load test data
    if not os.path.exists(test_data_path):
        logger.error(f"Test data not found: {test_data_path}")
        return
    
    test_df = pd.read_csv(test_data_path)
    test_df = test_df[test_df['duration'].notna()]
    
    # Prepare features
    feature_cols = [
        'avg_duration', 'recent_build_count', 'recent_success_rate',
        'total_lines', 'error_count', 'warning_count'
    ]
    
    X_test = test_df[feature_cols].fillna(0)
    y_test = test_df['duration']
    
    # Scale features
    X_test_scaled = scaler.transform(X_test)
    
    # Make predictions
    y_pred = model.predict(X_test_scaled)
    
    # Evaluate
    evaluator = ModelEvaluator()
    evaluator.evaluate_regressor(y_test, y_pred, "Duration Predictor")
    
    # Plot predictions
    evaluator.plot_prediction_distribution(
        y_test, y_pred,
        save_path="data/models/duration_predictions.png"
    )
    
    # Save results
    evaluator.save_results()


if __name__ == "__main__":
    print("Evaluating models...")
    
    # Evaluate both models
    evaluate_failure_model()
    evaluate_duration_model()
    
    print("\nEvaluation complete!")
