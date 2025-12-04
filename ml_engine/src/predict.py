#!/usr/bin/env python3
"""
Standalone prediction script
Make predictions without running the full API server
"""

import argparse
import json
import sys
from models.failure_predictor import FailurePredictor
from models.duration_predictor import DurationPredictor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def predict_failure(data: dict) -> dict:
    """Make failure prediction"""
    predictor = FailurePredictor()
    predictor.load_model()
    
    result = predictor.predict(data)
    return result


def predict_duration(data: dict) -> dict:
    """Make duration prediction"""
    predictor = DurationPredictor()
    predictor.load_model()
    
    result = predictor.predict(data)
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Make CI/CD build predictions'
    )
    
    parser.add_argument(
        'prediction_type',
        choices=['failure', 'duration', 'both'],
        help='Type of prediction to make'
    )
    
    parser.add_argument(
        '--project',
        required=True,
        help='Project slug (e.g., gh/org/repo)'
    )
    
    parser.add_argument(
        '--branch',
        default='main',
        help='Branch name'
    )
    
    parser.add_argument(
        '--success-rate',
        type=float,
        default=0.5,
        help='Recent success rate (0-1)'
    )
    
    parser.add_argument(
        '--failure-count',
        type=int,
        default=0,
        help='Recent failure count'
    )
    
    parser.add_argument(
        '--avg-duration',
        type=float,
        default=300.0,
        help='Average build duration in seconds'
    )
    
    parser.add_argument(
        '--error-count',
        type=int,
        default=0,
        help='Error count in recent builds'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    
    args = parser.parse_args()
    
    # Prepare input data
    input_data = {
        'project_slug': args.project,
        'branch': args.branch,
        'success_rate': args.success_rate,
        'failure_count': args.failure_count,
        'average_duration': args.avg_duration,
        'error_count': args.error_count,
        'warning_count': 0,
        'total_lines': 0,
        'error_types': {}
    }
    
    results = {}
    
    # Make predictions
    try:
        if args.prediction_type in ['failure', 'both']:
            logger.info("Making failure prediction...")
            failure_result = predict_failure(input_data)
            results['failure_prediction'] = failure_result
        
        if args.prediction_type in ['duration', 'both']:
            logger.info("Making duration prediction...")
            duration_result = predict_duration(input_data)
            results['duration_prediction'] = duration_result
        
        # Output results
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("\n" + "="*60)
            print("PREDICTION RESULTS")
            print("="*60)
            print(f"Project: {args.project}")
            print(f"Branch: {args.branch}")
            print()
            
            if 'failure_prediction' in results:
                fp = results['failure_prediction']
                print("FAILURE PREDICTION:")
                print(f"  Probability: {fp['failure_probability']:.2%}")
                print(f"  Predicted Status: {fp['predicted_status']}")
                print(f"  Confidence: {fp['confidence']:.2%}")
                print(f"  Risk Level: {fp['risk_level'].upper()}")
                
                if fp['factors']:
                    print("\n  Key Factors:")
                    for factor in fp['factors']:
                        print(f"    • {factor['factor']}: {factor['value']} ({factor['impact']})")
                print()
            
            if 'duration_prediction' in results:
                dp = results['duration_prediction']
                print("DURATION PREDICTION:")
                print(f"  Expected Duration: {dp['predicted_duration']:.0f} seconds ({dp['predicted_duration']/60:.1f} minutes)")
                print(f"  Range: {dp['min_duration']:.0f} - {dp['max_duration']:.0f} seconds")
                print(f"  Confidence: {dp['confidence']:.2%}")
                print()
            
            print("="*60)
    
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
