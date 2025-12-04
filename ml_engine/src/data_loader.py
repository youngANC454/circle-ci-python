import pandas as pd
import numpy as np
from pymongo import MongoClient
from typing import Dict, List, Any, Optional
import logging
import os
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """Load and prepare data from MongoDB for ML training"""
    
    def __init__(self, mongodb_url: str = None):
        self.mongodb_url = mongodb_url or os.getenv(
            "MONGODB_URL", 
            "mongodb://mongodb:27017"
        )
        self.db_name = "cicd_optimizer"
        self.client = None
        self.db = None
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_url)
            self.db = self.client[self.db_name]
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")
    
    def load_builds(
        self, 
        project_slug: Optional[str] = None,
        days: int = 90,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Load build data from MongoDB
        
        Args:
            project_slug: Filter by project (None for all projects)
            days: Number of days to look back
            limit: Maximum number of records to load
        
        Returns:
            DataFrame with build data
        """
        if not self.db:
            self.connect()
        
        # Build query
        query = {}
        
        if project_slug:
            query["project_slug"] = project_slug
        
        # Date filter
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query["created_at"] = {"$gte": cutoff_date.isoformat()}
        
        logger.info(f"Loading builds with query: {query}")
        
        # Fetch data
        cursor = self.db.builds.find(query)
        
        if limit:
            cursor = cursor.limit(limit)
        
        builds = list(cursor)
        logger.info(f"Loaded {len(builds)} builds from database")
        
        if not builds:
            logger.warning("No builds found in database")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(builds)
        
        # Remove MongoDB _id field
        if '_id' in df.columns:
            df = df.drop('_id', axis=1)
        
        return df
    
    def load_logs(
        self,
        project_slug: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Load build logs from MongoDB"""
        if not self.db:
            self.connect()
        
        query = {}
        if project_slug:
            query["project_slug"] = project_slug
        
        cursor = self.db.logs.find(query)
        
        if limit:
            cursor = cursor.limit(limit)
        
        logs = list(cursor)
        logger.info(f"Loaded {len(logs)} log entries from database")
        
        if not logs:
            return pd.DataFrame()
        
        df = pd.DataFrame(logs)
        
        if '_id' in df.columns:
            df = df.drop('_id', axis=1)
        
        return df
    
    def merge_builds_and_logs(
        self,
        builds_df: pd.DataFrame,
        logs_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge builds with their logs"""
        if builds_df.empty or logs_df.empty:
            logger.warning("Cannot merge empty dataframes")
            return builds_df
        
        # Merge on project_slug and build_num
        merged = builds_df.merge(
            logs_df,
            on=['project_slug', 'build_num'],
            how='left',
            suffixes=('', '_log')
        )
        
        logger.info(f"Merged data shape: {merged.shape}")
        return merged
    
    def load_training_data(
        self,
        project_slug: Optional[str] = None,
        days: int = 90,
        include_logs: bool = True
    ) -> pd.DataFrame:
        """
        Load complete training data with builds and logs
        
        Args:
            project_slug: Filter by project
            days: Days of history to load
            include_logs: Whether to include log data
        
        Returns:
            DataFrame ready for feature engineering
        """
        # Load builds
        builds_df = self.load_builds(project_slug=project_slug, days=days)
        
        if builds_df.empty:
            logger.error("No build data available")
            return pd.DataFrame()
        
        # Load and merge logs if requested
        if include_logs:
            logs_df = self.load_logs(project_slug=project_slug)
            if not logs_df.empty:
                builds_df = self.merge_builds_and_logs(builds_df, logs_df)
        
        logger.info(f"Loaded training data: {len(builds_df)} records")
        return builds_df
    
    def save_processed_data(
        self,
        df: pd.DataFrame,
        filename: str = "training_data.csv"
    ):
        """Save processed data to CSV"""
        output_path = f"data/processed/{filename}"
        os.makedirs("data/processed", exist_ok=True)
        
        df.to_csv(output_path, index=False)
        logger.info(f"Saved processed data to {output_path}")
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics of the data"""
        if df.empty:
            return {"error": "DataFrame is empty"}
        
        summary = {
            "total_records": len(df),
            "date_range": {
                "start": df['created_at'].min() if 'created_at' in df else None,
                "end": df['created_at'].max() if 'created_at' in df else None
            },
            "columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict()
        }
        
        # Build status distribution
        if 'status' in df.columns:
            summary["status_distribution"] = df['status'].value_counts().to_dict()
        
        # Project distribution
        if 'project_slug' in df.columns:
            summary["projects"] = df['project_slug'].unique().tolist()
        
        return summary


# Convenience function
def load_data_for_training(
    project_slug: Optional[str] = None,
    days: int = 90
) -> pd.DataFrame:
    """Quick function to load training data"""
    loader = DataLoader()
    try:
        df = loader.load_training_data(project_slug=project_slug, days=days)
        return df
    finally:
        loader.close()


if __name__ == "__main__":
    # Test the data loader
    loader = DataLoader()
    try:
        loader.connect()
        df = loader.load_training_data(days=30)
        
        if not df.empty:
            summary = loader.get_data_summary(df)
            print("\nData Summary:")
            print(f"Total Records: {summary['total_records']}")
            print(f"Columns: {len(summary['columns'])}")
            
            if 'status_distribution' in summary:
                print("\nStatus Distribution:")
                for status, count in summary['status_distribution'].items():
                    print(f"  {status}: {count}")
        else:
            print("No data available. Please sync builds from CircleCI first.")
    
    finally:
        loader.close()
