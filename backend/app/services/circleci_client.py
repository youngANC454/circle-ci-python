import httpx 
from httpx import HTTPError
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class CircleCIClient:
    """Client for interacting with CircleCI API"""
    
    def __init__(self):
        self.base_url = settings.CIRCLECI_BASE_URL
        self.headers = {
            "Circle-Token": settings.CIRCLECI_API_TOKEN,
            "Accept": "application/json"
        }
        self.timeout = 30.0
    
    async def get_project_pipelines(
        self, 
        project_slug: str, 
        branch: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get pipelines for a project"""
        url = f"{self.base_url}/project/{project_slug}/pipeline"
        params = {"limit": limit}
        
        if branch:
            params["branch"] = branch
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("items", [])
        
        except httpx.HTTPError as e:
            logger.error(f"Error fetching pipelines: {e}")
            raise
    
    async def get_pipeline_workflows(self, pipeline_id: str) -> List[Dict[str, Any]]:
        """Get workflows for a pipeline"""
        url = f"{self.base_url}/pipeline/{pipeline_id}/workflow"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data.get("items", [])
        
        except httpx.HTTPError as e:
            logger.error(f"Error fetching workflows: {e}")
            raise
    
    async def get_workflow_jobs(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get jobs for a workflow"""
        url = f"{self.base_url}/workflow/{workflow_id}/job"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data.get("items", [])
        
        except httpx.HTTPError as e:
            logger.error(f"Error fetching jobs: {e}")
            raise
    
    async def get_job_details(self, project_slug: str, job_number: int) -> Dict[str, Any]:
        """Get detailed job information"""
        url = f"{self.base_url}/project/{project_slug}/job/{job_number}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"Error fetching job details: {e}")
            raise
    
    async def get_build_logs(self, project_slug: str, build_num: int) -> str:
        """Get build logs for a specific build"""
        # Note: CircleCI API v2 doesn't directly expose logs
        # This is a placeholder - you may need to use artifacts or steps
        url = f"{self.base_url}/project/{project_slug}/{build_num}/artifacts"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                artifacts = response.json()
                
                # Download log artifacts
                log_content = []
                for artifact in artifacts:
                    if 'log' in artifact.get('path', '').lower():
                        log_url = artifact.get('url')
                        log_response = await client.get(log_url)
                        log_content.append(log_response.text)
                
                return "\n".join(log_content)
        
        except httpx.HTTPError as e:
            logger.error(f"Error fetching build logs: {e}")
            return ""
    
    async def get_recent_builds(
        self, 
        project_slug: str, 
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get recent builds for a project"""
        pipelines = await self.get_project_pipelines(project_slug, limit=limit)
        builds = []
        
        for pipeline in pipelines:
            pipeline_id = pipeline.get("id")
            workflows = await self.get_pipeline_workflows(pipeline_id)
            
            for workflow in workflows:
                workflow_id = workflow.get("id")
                jobs = await self.get_workflow_jobs(workflow_id)
                
                for job in jobs:
                    build_info = {
                        "build_num": job.get("job_number"),
                        "project_slug": project_slug,
                        "branch": pipeline.get("vcs", {}).get("branch"),
                        "status": job.get("status"),
                        "duration": self._calculate_duration(
                            job.get("started_at"),
                            job.get("stopped_at")
                        ),
                        "created_at": job.get("started_at"),
                        "stopped_at": job.get("stopped_at"),
                        "commit_sha": pipeline.get("vcs", {}).get("revision"),
                        "workflow_name": workflow.get("name"),
                        "job_name": job.get("name")
                    }
                    builds.append(build_info)
        
        return builds
    
    def _calculate_duration(self, started_at: str, stopped_at: str) -> Optional[int]:
        """Calculate build duration in seconds"""
        if not started_at or not stopped_at:
            return None
        
        try:
            start = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            stop = datetime.fromisoformat(stopped_at.replace('Z', '+00:00'))
            return int((stop - start).total_seconds())
        except (ValueError, AttributeError):
            return None


# Singleton instance
circleci_client = CircleCIClient()
