"""
ML Models Package
Contains failure and duration prediction models
"""

from .failure_predictor import FailurePredictor
from .duration_predictor import DurationPredictor

__all__ = ["FailurePredictor", "DurationPredictor"]
