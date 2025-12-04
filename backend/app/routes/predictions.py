from fastapi import APIRouter,HTTPException,Query
from typing import Dict,Any,List
import logging 

from app.models import PredictionRequest,FailurePrediction,DurationPrediction
from app.services.predictor import predictor_service
from app.services.log_processor import log_processor
from app.database import get_database

logger=logging.getLogger(__name__)
router=APIRouter()

@router.post("/failure",response_model=FailurePrediction)
async def predict_failure(request:PredictionRequest):
   
   try:
        features=await _gather_builds_features(
            request.project_slug,
            request.branch,
            request.recent_build_count
        )

        features_update({
            "commit_message":request.commit_message,
            "author":request.author,
            "workflow_name":request.workflow_name
        })

        prediction=await predictor_service.predict_failure(features)

        db=get_database()
        await db.predictions.insert_one(prediction.model_dump())

        return prediction
   except Exception as e:
        logger.error(f"Failed to predict failure: {e}")
        raise HTTPError(status_code=500,detail="Failed to predict failure")

@router.post("/duration",response_model=DurationPrediction)
async def predict_duration(request:PredictionRequest):
    try:
        features=await _gather_builds_features(
            request.project_slug,
            request.branch,
            request.recent_build_count
        )

        features_update({
            "workflow_name":request.workflow_name
        })

        prediction=await predictor_service.predict_duration(features)

        db=get_database()
        await db.predictions.insert_one(prediction.model_dump())

        return prediction

    except Exception as e:
        logger.error(f"Failed to predict duration: {e}")
        raise HTTPError(status_code=500,detail="Failed to predict duration")

@router.get("/history")
async def get_prediction_history(project_slug:str=Query(...,description="Project slug"),
limit:int=Query(20,ge=1,le=100,description="Number of predictions to return")
):
    try:
        db=get_database()
        predictions=await db.predictions.find(
            {"project_slug":project_slug}
        ).sort("timestamp",-1).limit(limit).to_list(length=limit)

        for pred in predictions:
            pred.pop("_id",None)

        return {
            "project_slug":project_slug,
            "predictions":predictions,
            "count":len(predictions)
        }
    except Exception as e:
        logger.error(f"Failed to get prediction history: {e}")
        raise HTTPError(status_code=500,detail="Failed to get prediction history")

async def _gather_builds_features(project_slug:str,
branch:str,recent_build_count:int)->List[Dict[str,Any]]:
    db=get_database()
    
    query={
        "project_slug":project_slug 
    }
    if branch:
        query["branch"]=branch
    
    recent_builds=await db.builds.find(
        query
    ).sort("created_at",-1).limit(recent_build_count).to_list(length=recent_build_count)
    
    if not recent_builds:
        return {
            "project_slug":project_slug,
            "branch":branch,
            "recent_build_count":recent_build_count,
            "success_rate":0.5,
            "average_duration":300,
            "failure_count":0
        }
    total_builds=len(recent_builds)
    success_count=sum(1 for build in recent_builds if build.get("status") == "success")
    failure_count=total_builds-success_count
    success_rate = success_count / total_builds if total_builds > 0 else 0.5
    
    # Calculate average duration (only for completed builds)
    durations = [b.get("duration", 0) for b in recent_builds if b.get("duration")]
    average_duration = sum(durations) / len(durations) if durations else 300

    log_features={}
    for build in recent_builds:
        if build.get("status") == "failed":
            log_entry=await db.logs.find_one(
                {
                    "project_slug":project_slug,
                    "build_num":build.get("build_num")
                }
            )
            if log_entry:
                log_features=log_processor.extract_features(log_entry.get("log_content",""))
                break
    
    features={
        "project_slug":project_slug,
        "branch":branch,
        "recent_build_count":recent_build_count,
        "success_rate":success_rate,
        "average_duration":average_duration,
        "failure_count":failure_count,
        **log_features
    }
    return features
