from fastapi import APIRouter,HTTPException,Query
from typing import List
from datetime import datetime,timedelta
import logging
from app.models import BuildMetrics
from app.database import get_database

logger=logging.getLogger(__name__)
router=APIRouter()

@router.get("/build-stats",response_model=BuildMetrics)
async def get_build_stats(project_slug:str=Query(...,description="Project slug"),
days:int=Query(30,ge=1,le=365,description="Number of days"),
):
    try:
        db=get_database()
        end_date=datetime.utcnow()
        start_date=end_date-timedelta(days=days)
        builds=await db.builds.find(
            {
                "project_slug":project_slug,
                "created_at":{"$gte":start_date.isoformat(),"$lte":end_date.isoformat()}
            }
        ).to_list(length=None)

        if not builds:
            raise HTTPError(status_code=404,detail="No builds found for the specified project and time range")
        
        total_builds=len(builds)
        success_count=sum(1 for build in builds if build.get("status") == "success")
        failure_count=total_builds-success_count
        success_rate=(success_count/total_builds)*100 if total_builds>0 else 0.0
        
        durations=[b.get('duration',0) for b in builds if b.get('duration')]
        average_duration=sum(durations)/len(durations) if durations else 0
        
        return BuildMetrics(
            project_slug=project_slug,
            total_builds=total_builds,
            success_rate=success_rate,
            failure_count=failure_count,
            success_count=success_count,
            average_duration=average_duration,
            date_range={
                "start":start_date(),
                "end":end_date()
            }
        )
    except Exception as e:
        logger.error(f"Failed to get build stats: {e}")
        raise HTTPError(status_code=500,detail="Failed to get build stats")

@router.get('/failed-trends')
async def get_failed_trends(project_slug:str=Query(...,description="Project slug"),
days:int=Query(30,ge=1,le=365,description="Number of days"),
):
    try:
        db=get_database()
        end_date=datetime.utcnow()
        start_date=end_date-timedelta(days=days)
        builds=await db.builds.find(
            {
                "project_slug":project_slug,
                "created_at":{"$gte":start_date.isoformat(),"$lte":end_date.isoformat()}
            }
        ).sort("created_at",1).to_list(length=None)

        daily_stats={}
        for build in builds:
            created_at=build.get("created_at","")
            if isinstance(created_at,str):
                date=created_at.split("T")[0]
            else:
                date=created_at.strftime("%Y-%m-%d")
            if date not in daily_stats:
                daily_stats[date]={
                    
                    "failures":0,
                    "total":0
                }
            daily_stats[date]["total"]+=1
            if build.get("status") == "failed":
                daily_stats[date]["failures"]+=1
        
        trends=[]
        for date,stats in sorted(daily_stats.items()):
            failure_rate=(stats["failures"]/stats["total"])*100 if stats["total"]>0 else 0.0
            trends.append({
                "date":date,
                'failures':stats['failures'],
                "failure_rate":round(failure_rate,2),
                "total_builds":stats["total"]
            })
        return {
            "project_slug":project_slug,
            "period_days":days,
            "trends":trends
        }
    except Exception as e:
        logger.error(f"Failed to get failed trends: {e}")
        raise HTTPError(status_code=500,detail="Failed to get failed trends")

@router.get('/duration-analysis')
async def get_duration_analysis(project_slug:str=Query(...,description="Project slug"),
days:int=Query(30,ge=1,le=365,description="Number of days"),
):
    try:
        db=get_database()
        end_date=datetime.utcnow()
        start_date=end_date-timedelta(days=days)
        builds=await db.builds.find(
            {
                "project_slug":project_slug,
                "created_at":{"$gte":start_date.isoformat(),"$lte":end_date.isoformat()},
                "duration":{"$exists":True,"$ne":None}

            }
        ).to_list(length=None)

        if not builds:
            return {
                "project_slug":project_slug,
                "message":"No data available for the specified project and time range"
            }
        
        durations=[b.get('duration',0) for b in builds ]
        durations.sort()
        
        average_duration=sum(durations)/len(durations)
        max_duration=max(durations)
        min_duration=min(durations)

        p50 = durations[len(durations) // 2]
        p90 = durations[int(len(durations) * 0.9)]
        p95 = durations[int(len(durations) * 0.95)]
        
        return {
            "project_slug":project_slug,
            "period_days":days,
            "build_count":len(builds),
            "average_duration":round(average_duration,2),
            "max_duration":max_duration,
            "min_duration":min_duration,
            "percentiles":{"p50":p50,
            "p90":p90,
            "p95":p95}
        }
    except Exception as e:
        logger.error(f"Failed to get duration analysis: {e}")
        raise HTTPError(status_code=500,detail="Failed to get duration analysis")

@router.get('/common-failures')
async def get_common_failures(project_slug:str=Query(...,description="Project slug"),
days:int=Query(10,ge=1,le=365,description="Number of failure return"),
):

    try:
        db=get_database()

        failed_builds=await db.builds.find(
            {
                "project_slug":project_slug,
                "status":"failed"
            }
        ).to_list(length=None)

        if not failed_builds:
            return {
                "project_slug":project_slug,
                "message":"No failed builds found for the specified project and time range"
            }
        
        failure_type={}

        for build in failed_builds[:limit]:
            log_entry=await db.logs.find_one(
                {
                    "project_slug":project_slug,
                    "build_num":build.get("build_num")
                }
            )
            if log_entry:
                from app.services.log_processor import Log_processor
                features=log_processor.extract_features(log_entry.get("log",""))

                for error_types,count in features.get("error_types",[]).items():
                    if count>0:
                        failure_type[error_types]=failure_type.get(error_types,0)+count
        
        sorted_failures=sorted(
            failure_types.items(),
            key=lambda x:x[1],
            reverse=True
        )[:limit]

        return {
            "project_slug":project_slug,
            "common_failure":[
                {"type":ftype,"count":count}
                for ftype,count in sorted_failures
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get common failures: {e}")
        raise HTTPError(status_code=500,detail="Failed to get common failures")

