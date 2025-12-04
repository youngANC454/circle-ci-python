from fastapi import APIRouter,HTTPException,Query,Path
from typing import List,Dict,Any, Optional
import logging
from app.models import Build,BuildLog
from app.database import get_database
from app.services.circleci_client import circleci_client

logger=logging.getLogger(__name__)
router=APIRouter()

@router.get('/',response_model=List[Build])
async def get_builds(
    project_slug:str=Query(...,description="Project slug"),
    branch:Optional[str]=Query(None,description="Branch name"),
    limit:int=Query(30,ge=1,le=100,description="Number of builds to return")
):
    try:
        db=get_database()
        if builds:
            await db.builds.insert_many(builds,ordered=False)
            logger.info(f"Stored {len(builds)} builds fir {project_slug}")

        if branch:
            builds=[b for b in builds if b.get("branch") == branch]

        return builds
    except Exception as e:
        logger.error(f"Failed to get builds: {e}")
        raise HTTPError(status_code=500,detail="Failed to get builds")

from fastapi import Path

@router.get("/{build_num}", response_model=Build)
async def get_build(
    build_num: int = Path(..., description="Build number"),
    project_slug: str = Query(..., description="Project slug")
):


    try:
        db=get_database()
        build=await db.builds.find_one({"project_slug":project_slug,"build_num":build_num})
        if build:
           build.pop("_id",None)
           return build
        job_details=await circleci_client.get_job_details(project_slug,build_num)
        build_data={
            "build_num":build_num,
            "project_slug":project_slug,
            "branch":job_details.get("branch"),
            "status":job_details.get("status"),
            "duration":job_details.get("duration"),
            "created_at":job_details.get("created_at"),
            "updated_at":job_details.get("updated_at")
        }
        await db.builds.insert_one(build_data)
        return build_data
    except Exception as e:
        logger.error(f"Failed to get build {build_num}: {e}")
        raise HTTPError(status_code=500,detail="Failed to get build")

@router.get("/{build_num}/logs", response_model=BuildLog)
async def get_build_logs(
    build_num: int = Path(..., description="Build number"),
    project_slug: str = Query(..., description="Project slug")
):

    try:
        db=get_database()
        log_entry=await db.logs.find_one({"project_slug":project_slug,"build_num":build_num})
        if log_entry:
            log_entry.pop("_id",None)
            return log_entry
        log_content=await circleci_client.get_job_log(project_slug,build_num)
        log_data={
            "project_slug":project_slug,
            "build_num":build_num,
            "log_content":log_content
        }
        await db.logs.insert_one(log_data)
        return log_data
    except Exception as e:
        logger.error(f"Failed to get build log {build_num}: {e}")
        raise HTTPError(status_code=500,detail="Failed to get build log")


@router.post('/sync')
async def sync_builds():
    try:
        builds=await circleci_client.get_recent_builds(project_slug,limit=limit)
        db=get_database()
        for build in builds:
            await db.builds.update_one(
                {
                    "project_slug":project_slug,
                    "build_num":build.get("build_num")
                },
                {
                    "$set":build
                },
                upsert=True
            )
        logger.info(f"Synced {len(builds)} builds for {project_slug}")
        return {"message":"Synced builds successfully",
        "project_slug":project_slug,
        "build_count":len(builds)}
    except Exception as e:
        logger.error(f"Failed to sync builds: {e}")
        raise HTTPError(status_code=500,detail="Failed to sync builds")

