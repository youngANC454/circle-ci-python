from pydantic import BaseModel,Field
from typing import List,Optional,Dict,Any
from datetime import datetime
from enum import Enum



class BuildStatus(str,Enum):
    SUCCESS = "success"
    FAILED= "failed"
    RUNNING = "running"
    CANCELED = "canceled"
    NOT_RUN = "not_run"

class Build(BaseModel):
    build_num:int
    project_slug:str
    branch:str
    status:BuildStatus
    duration:Optional[int]=None

    created_at:datetime
    stopped_at:Optional[datetime]=None
    commit_sha:Optional[str]=None
    commit_message:Optional[str]=None
    author:Optional[str]=None
    workflow_name:Optional[str]=None
    job_name:Optional[str]=None

class PredictionRequest(BaseModel):
   project_slug:str
   branch:str
   commit_message:Optional[str]=None
   author:Optional[str]=None
   workflow_name:Optional[str]=None
   recent_build_count:int=10

class BuildLog(BaseModel):
    build_num:int 
    project_slug:str 
    log_content:str
    timestamp:datetime= Field(default_factory=datetime.utcnow)

class FailurePrediction(BaseModel):
    build_num:int 
    project_slug:str 
    failure_probability:float=Field(...,ge=0.0,le=1.0)
    prediction_status:str
    confidence:float= Field(...,ge=0.0,le=1.0) 
    risk_level:str
    factors:List[Dict[str,Any]]=[]
    timestamp:datetime= Field(default_factory=datetime.utcnow)


class DurationPrediction(BaseModel):
    build_num:int 
    project_slug:str 
    predicted_duration:int
    duration_range:Dict[str,int]
    confidence:float = Field(...,ge=0.0,le=1.0) 
   
    timestamp:datetime= Field(default_factory=datetime.utcnow)


class BuildMetrics(BaseModel):
    project_slug:str
    total_builds:int
    average_duration:int
    success_rate:float
    failure_count:int
    success_count:int
    date_range:Dict[str,datetime]

class HealthResponse(BaseModel):
    status:str
    service:str
    version:str
    timestamp:datetime= Field(default_factory=datetime.utcnow)    

class ErrorResponse(BaseModel):
    detail:str
    error:Optional[str]=None
    timestamp:datetime= Field(default_factory=datetime.utcnow)
