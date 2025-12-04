import pandas as pd
import numpy as np
import re
from typing import Dict, List, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Extract and engineer features from build and log data"""
    
    def __init__(self):
        self.error_patterns = self._compile_error_patterns()
    
    def _compile_error_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for error detection"""
        patterns = {
            'compilation': re.compile(r'compil.*error|syntax.*error', re.IGNORECASE),
            'runtime': re.compile(r'runtime.*error|exception|traceback', re.IGNORECASE),
            'test': re.compile(r'test.*fail|assertion.*fail', re.IGNORECASE),
            'timeout': re.compile(r'timeout|timed out', re.IGNORECASE),
            'memory': re.compile(r'out of memory|oom|memory error', re.IGNORECASE),
            'network': re.compile(r'connection.*fail|network.*error', re.IGNORECASE)
        }
        return patterns
    
    def extract_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract basic features from build data"""
        logger.info("Extracting basic features...")
        
        features = df.copy()
        
        # Convert datetime strings to datetime objects
        if 'created_at' in features.columns:
            features['created_at'] = pd.to_datetime(features['created_at'], errors='coerce')
        
        if 'stopped_at' in features.columns:
            features['stopped_at'] = pd.to_datetime(features['stopped_at'], errors='coerce')
        
        # Extract time-based features
        if 'created_at' in features.columns:
            features['hour_of_day'] = features['created_at'].dt.hour
            features['day_of_week'] = features['created_at'].dt.dayofweek
            features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Duration features
        if 'duration' in features.columns:
            features['duration_minutes'] = features['duration'] / 60
            features['is_long_build'] = (features['duration'] > 600).astype(int)  # > 10 min
        
        # Status encoding
        if 'status' in features.columns:
            features['is_failed'] = (features['status'] == 'failed').astype(int)
            features['is_success'] = (features['status'] == 'success').astype(int)
        
        logger.info(f"Basic features extracted. Shape: {features.shape}")
        return features
    
    def extract_log_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features from log content"""
        logger.info("Extracting log features...")
        
        features = df.copy()
        
        if 'log_content' not in features.columns:
            logger.warning("No log_content column found")
            # Add default values
            features['error_count'] = 0
            features['warning_count'] = 0
            features['total_lines'] = 0
            for error_type in self.error_patterns.keys():
                features[f'error_{error_type}'] = 0
            return features
        
        # Initialize error type columns
        for error_type in self.error_patterns.keys():
            features[f'error_{error_type}'] = 0
        
        # Process each log
        for idx, row in features.iterrows():
            log_content = row.get('log_content', '')
            
            if not log_content or pd.isna(log_content):
                continue
            
            # Split into lines
            lines = str(log_content).split('\n')
            features.at[idx, 'total_lines'] = len(lines)
            
            # Count errors and warnings
            error_count = 0
            warning_count = 0
            
            for line in lines:
                line_lower = line.lower()
                
                # Check for errors
                if 'error' in line_lower or 'fail' in line_lower:
                    error_count += 1
                
                # Check for warnings
                if 'warning' in line_lower or 'warn' in line_lower:
                    warning_count += 1
                
                # Classify error types
                for error_type, pattern in self.error_patterns.items():
                    if pattern.search(line):
                        features.at[idx, f'error_{error_type}'] += 1
            
            features.at[idx, 'error_count'] = error_count
            features.at[idx, 'warning_count'] = warning_count
        
        # Fill NaN values
        features['error_count'] = features['error_count'].fillna(0)
        features['warning_count'] = features['warning_count'].fillna(0)
        features['total_lines'] = features['total_lines'].fillna(0)
        
        logger.info(f"Log features extracted. Shape: {features.shape}")
        return features
    
    def extract_historical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features based on historical build data"""
        logger.info("Extracting historical features...")
        
        features = df.copy()
        
        # Sort by project and date
        if 'project_slug' in features.columns and 'created_at' in features.columns:
            features = features.sort_values(['project_slug', 'created_at'])
        
        # Calculate rolling statistics per project
        if 'project_slug' in features.columns:
            # Success rate (last 10 builds)
            features['recent_success_rate'] = features.groupby('project_slug')['is_success'].transform(
                lambda x: x.rolling(window=10, min_periods=1).mean()
            )
            
            # Failure count (last 10 builds)
            features['recent_failure_count'] = features.groupby('project_slug')['is_failed'].transform(
                lambda x: x.rolling(window=10, min_periods=1).sum()
            )
            
            # Average duration (last 10 builds)
            if 'duration' in features.columns:
                features['avg_duration'] = features.groupby('project_slug')['duration'].transform(
                    lambda x: x.rolling(window=10, min_periods=1).mean()
                )
        
        # Build frequency
        if 'created_at' in features.columns and 'project_slug' in features.columns:
            features['builds_per_day'] = features.groupby('project_slug').apply(
                lambda x: len(x) / max((x['created_at'].max() - x['created_at'].min()).days, 1)
            ).reindex(features['project_slug']).values
        
        logger.info(f"Historical features extracted. Shape: {features.shape}")
        return features
    
    def extract_commit_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features from commit messages"""
        logger.info("Extracting commit features...")
        
        features = df.copy()
        
        if 'commit_message' not in features.columns:
            features['commit_message_length'] = 0
            features['has_fix_keyword'] = 0
            features['has_feature_keyword'] = 0
            return features
        
        # Commit message length
        features['commit_message_length'] = features['commit_message'].apply(
            lambda x: len(str(x)) if pd.notna(x) else 0
        )
        
        # Keywords
        fix_keywords = ['fix', 'bug', 'patch', 'hotfix', 'repair']
        feature_keywords = ['feature', 'add', 'new', 'implement']
        
        features['has_fix_keyword'] = features['commit_message'].apply(
            lambda x: 1 if any(kw in str(x).lower() for kw in fix_keywords) else 0
        )
        
        features['has_feature_keyword'] = features['commit_message'].apply(
            lambda x: 1 if any(kw in str(x).lower() for kw in feature_keywords) else 0
        )
        
        logger.info(f"Commit features extracted. Shape: {features.shape}")
        return features
    
    def create_training_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create complete feature set for training"""
        logger.info("Creating complete training feature set...")
        
        # Apply all feature extraction steps
        features = self.extract_basic_features(df)
        features = self.extract_log_features(features)
        features = self.extract_historical_features(features)
        features = self.extract_commit_features(features)
        
        logger.info(f"Complete feature set created. Shape: {features.shape}")
        logger.info(f"Columns: {list(features.columns)}")
        
        return features
    
    def get_feature_columns(self) -> List[str]:
        """Get list of feature columns for model training"""
        return [
            # Time features
            'hour_of_day',
            'day_of_week',
            'is_weekend',
            
            # Duration features
            'duration_minutes',
            'is_long_build',
            'avg_duration',
            
            # Log features
            'error_count',
            'warning_count',
            'total_lines',
            'error_compilation',
            'error_runtime',
            'error_test',
            'error_timeout',
            'error_memory',
            'error_network',
            
            # Historical features
            'recent_success_rate',
            'recent_failure_count',
            'builds_per_day',
            
            # Commit features
            'commit_message_length',
            'has_fix_keyword',
            'has_feature_keyword'
        ]
    
    def prepare_for_training(
        self,
        df: pd.DataFrame,
        target_column: str = 'is_failed'
    ) -> tuple:
        """
        Prepare features and target for model training
        
        Returns:
            X (features), y (target)
        """
        feature_cols = self.get_feature_columns()
        
        # Filter to available columns
        available_features = [col for col in feature_cols if col in df.columns]
        
        if len(available_features) < len(feature_cols):
            missing = set(feature_cols) - set(available_features)
            logger.warning(f"Missing feature columns: {missing}")
        
        # Extract features
        X = df[available_features].fillna(0)
        
        # Extract target
        if target_column not in df.columns:
            logger.error(f"Target column '{target_column}' not found")
            return None, None
        
        y = df[target_column]
        
        logger.info(f"Prepared {len(X)} samples with {len(available_features)} features")
        return X, y


if __name__ == "__main__":
    # Test feature engineering
    from data_loader import load_data_for_training
    
    df = load_data_for_training(days=30)
    
    if not df.empty:
        engineer = FeatureEngineer()
        features = engineer.create_training_features(df)
        
        print(f"\nFeature Engineering Complete!")
        print(f"Total Features: {len(features.columns)}")
        print(f"Total Samples: {len(features)}")
        print(f"\nFeature Columns:")
        for col in engineer.get_feature_columns():
            if col in features.columns:
                print(f"  ✓ {col}")
            else:
                print(f"  ✗ {col} (missing)")
    else:
        print("No data available for feature engineering")
