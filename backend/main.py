import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from orchestrator import WatchmanOrchestrator, extract_webhook_data


# Pydantic models for request/response validation
class WebhookPayload(BaseModel):
    """GitHub webhook payload model"""
    ref: Optional[str] = None
    after: Optional[str] = None
    repository: Optional[Dict[str, Any]] = None
    head_commit: Optional[Dict[str, Any]] = None
    pusher: Optional[Dict[str, Any]] = None
    commits: Optional[list] = None

class ManualScanRequest(BaseModel):
    """Manual scan request model"""
    repo_name: str
    branch: str = "main"

class ScanResponse(BaseModel):
    """Scan response model"""
    success: bool
    scan_run_id: Optional[int] = None
    message: str
    workflow_id: Optional[str] = None


# Global orchestrator instance
orchestrator: Optional[WatchmanOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global orchestrator

    print("🚀 Starting Watchman API server...")
    try:
        # Initialize orchestrator on startup
        orchestrator = WatchmanOrchestrator()
        print("✓ Orchestrator initialized successfully")
        yield
    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        raise
    finally:
        print("🔄 Shutting down Watchman API server...")


# Create FastAPI app
app = FastAPI(
    title="Watchman Security Scanner API",
    description="AI-powered security scanning platform with GitHub integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_orchestrator() -> WatchmanOrchestrator:
    """Dependency to get orchestrator instance"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return orchestrator


async def process_webhook_background(
    webhook_data: Dict,
    repo_name: str,
    branch: str,
    commit_sha: str
):
    """Background task to process GitHub webhook"""
    try:
        print(f"🔄 Processing webhook for {repo_name}:{branch} in background...")

        result = orchestrator.process_github_webhook(
            webhook_payload=webhook_data,
            repo_full_name=repo_name,
            branch=branch,
            commit_sha=commit_sha
        )

        if result["success"]:
            print(f"✅ Webhook processing completed for {repo_name}")
        else:
            print(f"❌ Webhook processing failed for {repo_name}: {result.get('error')}")

    except Exception as e:
        print(f"❌ Background webhook processing error: {e}")


async def process_manual_scan_background(repo_name: str, branch: str):
    """Background task to process manual scan"""
    try:
        print(f"🔄 Processing manual scan for {repo_name}:{branch} in background...")

        result = orchestrator.process_manual_scan(repo_name, branch)

        if result["success"]:
            print(f"✅ Manual scan completed for {repo_name}")
        else:
            print(f"❌ Manual scan failed for {repo_name}: {result.get('error')}")

    except Exception as e:
        print(f"❌ Background manual scan error: {e}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Watchman Security Scanner",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "webhook": "/webhook/github",
            "manual_scan": "/scan/manual",
            "scan_status": "/scan/{scan_id}",
            "recent_scans": "/scans",
            "health": "/health",
            "stats": "/stats"
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check(orchestrator_instance: WatchmanOrchestrator = Depends(get_orchestrator)):
    """Health check endpoint"""
    try:
        # Test database connection
        stats = orchestrator_instance.get_system_stats()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "total_scans": stats.get("total_scans", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    orchestrator_instance: WatchmanOrchestrator = Depends(get_orchestrator)
):
    """
    GitHub webhook endpoint - receives push events and triggers security scans
    """
    try:
        # Get raw payload
        payload = await request.json()

        # Extract webhook data
        webhook_data = extract_webhook_data(payload)

        print(f"📥 Received GitHub webhook: {webhook_data.get('event_type')}")

        # Validate it's a push event to a branch we care about
        if webhook_data.get("event_type") != "push":
            return JSONResponse(
                status_code=200,
                content={
                    "message": f"Ignored {webhook_data.get('event_type')} event",
                    "timestamp": datetime.now().isoformat()
                }
            )

        repo_name = webhook_data.get("repo_full_name")
        branch = webhook_data.get("branch")
        commit_sha = webhook_data.get("commit_sha")

        if not repo_name or not branch:
            raise HTTPException(
                status_code=400,
                detail="Missing repository name or branch in webhook payload"
            )

        # Skip if branch is being deleted
        if commit_sha and commit_sha.startswith("0000000"):
            return JSONResponse(
                status_code=200,
                content={
                    "message": f"Ignored branch deletion event for {branch}",
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Add background task to process the webhook
        background_tasks.add_task(
            process_webhook_background,
            webhook_data,
            repo_name,
            branch,
            commit_sha
        )

        # Respond immediately to GitHub
        return JSONResponse(
            status_code=202,
            content={
                "message": f"Webhook received, processing scan for {repo_name}:{branch}",
                "repo": repo_name,
                "branch": branch,
                "commit": commit_sha[:8] if commit_sha else "unknown",
                "status": "processing",
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@app.post("/scan/manual", response_model=ScanResponse)
async def manual_scan(
    scan_request: ManualScanRequest,
    background_tasks: BackgroundTasks,
    orchestrator_instance: WatchmanOrchestrator = Depends(get_orchestrator)
):
    """
    Manually trigger a security scan for a repository
    """
    try:
        print(f"🔧 Manual scan requested for {scan_request.repo_name}:{scan_request.branch}")

        # Add background task to process the scan
        background_tasks.add_task(
            process_manual_scan_background,
            scan_request.repo_name,
            scan_request.branch
        )

        return ScanResponse(
            success=True,
            message=f"Manual scan started for {scan_request.repo_name}:{scan_request.branch}",
            workflow_id=f"manual_{int(datetime.now().timestamp())}"
        )

    except Exception as e:
        print(f"❌ Manual scan error: {e}")
        return ScanResponse(
            success=False,
            message=f"Failed to start manual scan: {str(e)}"
        )


@app.get("/scan/{scan_id}")
async def get_scan_status(
    scan_id: int,
    orchestrator_instance: WatchmanOrchestrator = Depends(get_orchestrator)
):
    """Get status and details of a specific scan run"""
    try:
        result = orchestrator_instance.get_scan_status(scan_id)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scan status: {str(e)}")


@app.get("/scans")
async def get_recent_scans(
    repo_name: Optional[str] = None,
    limit: int = 10,
    orchestrator_instance: WatchmanOrchestrator = Depends(get_orchestrator)
):
    """Get recent scan runs, optionally filtered by repository"""
    try:
        scans = orchestrator_instance.get_recent_scans(repo_name, limit)

        return {
            "scans": scans,
            "count": len(scans),
            "filtered_by_repo": repo_name,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scans: {str(e)}")


@app.get("/stats")
async def get_system_stats(orchestrator_instance: WatchmanOrchestrator = Depends(get_orchestrator)):
    """Get overall system statistics"""
    try:
        stats = orchestrator_instance.get_system_stats()

        return {
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/repos/{owner}/{repo}/scans")
async def get_repo_scans(
    owner: str,
    repo: str,
    limit: int = 5,
    orchestrator_instance: WatchmanOrchestrator = Depends(get_orchestrator)
):
    """Get recent scans for a specific repository"""
    repo_name = f"{owner}/{repo}"
    return await get_recent_scans(repo_name, limit, orchestrator_instance)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "message": "The requested resource was not found",
            "path": str(request.url),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "path": str(request.url),
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
