import pandas as pd 
import numpy as np 

from sklearn.ensemble import RandomForestClassifier.RandomForestRegressor
from sklearn.model_selection import train_test_split,GridSearchCV
from sklearn.preprocessing import StandardScaler

from sklearn.metrics import mean_squared_error,classification_report,accuracy_score,r2_score

import joblib
import logging
import os 
from datetime import datetime

logger=logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self,data_path:str="data/processed/training_data.csv"):

        self.data_path=data_path
        self.failure_model=None
        self.duration_model=None
        self.scaler_failure=StandardScaler()
        self.scaler_duration=StandardScaler()


    def load_data(self)->pd.DataFrame:
        if not os.path.exists(self.data_path):
            logger.error(f"Data file not found at {self.data_path}")
            return None

        df=pd.read_csv(self.data_path)
        logger.info(f"Loaded data from {self.data_path}")
        return df
    
    def prepare_feature_data(self,df:pd.DataFrame):
        feature_cols=[
            'success_rate',
            'failure_count',
            'recent_build_count',
            'error_count',
            'warning_count',
            'total_lines',
            'error_compilation',
            'error_runtime',
            'error_test',
            'error_timeout',
            'error_memory'
        ]
        X=df[feature_cols].fillna(0)
        y=(df['status']=='failed').astype(int)
        return X,y
    
    def prepare_duration_data(self,df:pd.DataFrame):
        feature_cols = [
            'average_duration',
            'recent_build_count',
            'success_rate',
            'total_lines',
            'error_count',
            'warning_count'
        ]

        df_without_duration=df[df['duration'].notna()].copy()
        X=df_without_duration[feature_cols].fillna(0)
        y=df_without_duration['duration']
        return X,y
    
    def train_failure_model(self,X,y):
        logger.info("Training failure model")
        X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
       
        X_train_scaled=self.scaler_failure.transform(X_train)
        X_test_scaled=self.scaler_failure.transform(X_test)
        
        rf=RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        rf.fit(X_train_scaled,y_train)
        
        y_pred=rf.predict(X_test_scaled)
        accuracy=accuracy_score(y_test,y_pred)
        logger.info(f"Failure model accuracy: {accuracy:.4f}")
        logger.info(classification_report(y_test,y_pred))
        feature_importance=pd.DataFrame({
            "feature":X.columns,
            "importance":rf.feature_importances_
        }).sort_values(by="importance",ascending=False)
        logger.info("Feature importance:\n",feature_importance.head(10))
        self.failure_model=rf
        return rf,accuracy

    def train_duration_model(self,X,y):
        logger.info("Training duration model")
        X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42)
        X_train_scaled=self.scaler_duration.transform(X_train)
        X_test_scaled=self.scaler_duration.transform(X_test)
        rf=RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        rf.fit(X_train_scaled,y_train)
        y_pred=rf.predict(X_test_scaled)
        mse=mean_squared_error(y_test,y_pred)
        r2=r2_score(y_test,y_pred)
        logger.info(f"Duration model RMSE: {mse:.4f}")
        logger.info(f"Duration model R2: {r2:.4f}")
        feature_importance=pd.DataFrame({
            "feature":X.columns,
            "importance":rf.feature_importances_
        }).sort_values(by="importance",ascending=False)
        logger.info("Feature importance:\n",feature_importance.head(10))
        self.duration_model=rf
        return rf,r2

    def save_models(self):
        os.makedirs("data/models",exist_ok=True)
        if self.failure_model:
            failure_path="data/models/failure_model.pkl"
            joblib.dump({
                'model':self.failure_model,
                'scaler':self.scaler_failure,
                'timestamp':datetime.now().isoformat()
            },failure_path)
            logger.info(f"Saved failure model to {failure_path}")
        
        if self.duration_model:
            duration_path="data/models/duration_model.pkl"
            joblib.dump({
                'model':self.duration_model,
                'scaler':self.scaler_duration,
                'timestamp':datetime.now().isoformat()
            },duration_path)
            logger.info(f"Saved duration model to {duration_path}")

    def train_all(self):
        df=self.load_data()
        if df in None or len(df)==0:
            logger.error("No data available for training")
            return
        try:
            X_fail, y_fail = self.prepare_failure_data(df)
            self.train_failure_model(X_fail, y_fail)
        except Exception as e:
            logger.error(f"Error training failure model: {e}")
        
        # Train duration model
        try:
            X_dur, y_dur = self.prepare_duration_data(df)
            self.train_duration_model(X_dur, y_dur)
        except Exception as e:
            logger.error(f"Error training duration model: {e}")
        
        # Save models
        self.save_models()


if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_all()
