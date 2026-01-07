"""
Mission42 Timesheet - FastAPI Application

Main FastAPI application providing REST API endpoints for:
- Health checks and status
- Manual data processing triggers
- Timesheet data access
- Monthly export (HTML, CSV, Excel)
- OAuth authentication flows
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Depends, Response, Cookie
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.pocketbase_client import PocketBaseClient
from app.config import Config
from app.services.scheduler import SchedulerService
from app.services.exporters import MonthlyExporter
from app.utils.logging_config import configure_logging_from_env

# Configure logging from environment
configure_logging_from_env()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Mission42 Timesheet API",
    description="Automated timesheet system with multi-source data aggregation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
pb_client: Optional[PocketBaseClient] = None
config: Optional[Config] = None
scheduler: Optional[SchedulerService] = None
exporter: Optional[MonthlyExporter] = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    global pb_client, config, scheduler, exporter

    logger.info("Starting Mission42 Timesheet API...")

    # Initialize PocketBase client
    pb_client = PocketBaseClient()

    # Check PocketBase connection
    if not pb_client.health_check():
        logger.error("PocketBase is not accessible!")
        raise RuntimeError("PocketBase connection failed")

    logger.info("✓ Connected to PocketBase")

    # Initialize configuration
    config = Config()
    try:
        config.setup_pocketbase(pb_client)
        logger.info("✓ Configuration loaded")
    except Exception as e:
        logger.warning(f"Failed to load settings: {e}. Using defaults.")

    # Initialize scheduler
    scheduler = SchedulerService(pb_client, config)
    scheduler.start()
    logger.info("✓ Background scheduler started")

    # Initialize exporter
    exporter = MonthlyExporter(pb_client, config)
    logger.info("✓ Monthly exporter initialized")

    logger.info("🚀 Mission42 Timesheet API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down Mission42 Timesheet API...")

    if scheduler:
        scheduler.stop()
        logger.info("✓ Scheduler stopped")

    logger.info("👋 Goodbye!")


# ============================================================================
# Health & Status Endpoints
# ============================================================================


@app.get("/", tags=["Health"])
async def root():
    """API status and information."""
    return {
        "name": "Mission42 Timesheet API",
        "version": "1.0.0",
        "status": "operational",
        "message": "Welcome to Mission42 Timesheet API! 🚀",
        "quick_links": {
            "interactive_viewer": "/viewer",
            "dashboard": "/dashboard",
            "api_documentation": "/docs",
            "health_check": "/health",
        },
        "data_access": {
            "settings": "/data/settings",
            "work_packages": "/data/work_packages",
            "project_specs": "/data/project_specs",
            "raw_events": "/data/raw_events",
            "time_blocks": "/data/time_blocks",
        },
        "features": [
            "📊 Interactive data viewer with copy-to-clipboard",
            "📈 Real-time dashboard with system stats",
            "📅 Automated timesheet generation",
            "🔄 Multi-source data aggregation (WakaTime, GitHub, Calendar, Gmail)",
            "📤 Export to HTML, CSV, Excel",
        ],
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Verifies:
    - PocketBase connection
    - Scheduler status
    """
    if not pb_client:
        raise HTTPException(status_code=503, detail="PocketBase client not initialized")

    pocketbase_healthy = pb_client.health_check()
    scheduler_running = scheduler._running if scheduler else False

    status = "healthy" if pocketbase_healthy and scheduler_running else "degraded"

    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "pocketbase": "healthy" if pocketbase_healthy else "unhealthy",
            "scheduler": "running" if scheduler_running else "stopped",
        },
    }


@app.get("/status/scheduler", tags=["Status"])
async def scheduler_status():
    """Get background scheduler status and job information."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    return scheduler.get_job_status()


# ============================================================================
# Manual Processing Endpoints
# ============================================================================


@app.post("/process/manual", tags=["Processing"])
async def manual_process():
    """
    Manually trigger data fetching and processing for current week.

    This endpoint:
    1. Fetches data from all enabled sources (WakaTime, Calendar, Gmail, GitHub, Claude Code)
    2. Processes current week into time blocks
    3. Applies auto-fill if needed

    Returns:
        Processing results with statistics
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    logger.info("Manual processing triggered via API")

    try:
        result = await scheduler.manual_fetch_and_process()
        return result
    except Exception as e:
        logger.error(f"Manual processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/process/week/{date}", tags=["Processing"])
async def process_specific_week(date: str):
    """
    Process a specific week.

    Args:
        date: Date within the week to process (YYYY-MM-DD format)

    Returns:
        Processing results
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    try:
        # Parse date
        reference_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    logger.info(f"Processing week containing {date}")

    try:
        result = await scheduler.manual_process_week(reference_date)
        return result
    except Exception as e:
        logger.error(f"Week processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ============================================================================
# Data Access Endpoints
# ============================================================================


@app.get("/timesheet/current", tags=["Timesheet"])
async def get_current_timesheet(auth_token: Optional[str] = Cookie(None)):
    """Get timesheet for current month. Requires authentication."""
    from app.utils.auth import get_current_user

    # Check authentication
    try:
        user = get_current_user(auth_token)
    except HTTPException:
        # Redirect to login
        return RedirectResponse(url="/login", status_code=303)

    now = datetime.now()
    return await get_timesheet_month(now.year, now.month, auth_token=auth_token)


@app.get("/timesheet/month/{year}/{month}", tags=["Timesheet"])
async def get_timesheet_month(
    year: int,
    month: int,
    format: str = Query("html", regex="^(html|json)$"),
    auth_token: Optional[str] = Cookie(None)
):
    """
    Get timesheet data for a specific month. Requires authentication.

    Args:
        year: Year (e.g., 2026)
        month: Month (1-12)
        format: Output format (html or json). Default: html
        auth_token: Authentication token from cookie

    Returns:
        Time blocks for the specified month as HTML table or JSON
    """
    from app.utils.auth import get_current_user

    # Check authentication
    try:
        user = get_current_user(auth_token)
    except HTTPException:
        # Redirect to login
        return RedirectResponse(url="/login", status_code=303)

    if not pb_client:
        raise HTTPException(status_code=503, detail="PocketBase client not initialized")

    # Validate month
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    try:
        # Get start and end of month
        from datetime import timedelta
        start_date = datetime(year, month, 1)

        # Get end of month
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        # Fetch time blocks
        filter_str = (
            f'block_start >= "{start_date.isoformat()}" && '
            f'block_start <= "{end_date.replace(hour=23, minute=59, second=59).isoformat()}"'
        )

        time_blocks = pb_client.get_full_list(
            pb_client.COLLECTION_TIME_BLOCKS,
            filter=filter_str,
            sort="+block_start"
        )

        # Convert to dict list
        blocks_list = []
        for block in time_blocks:
            if hasattr(block, "__dict__"):
                block_dict = {
                    k: v for k, v in block.__dict__.items()
                    if not k.startswith("_")
                }
            else:
                block_dict = dict(block)
            blocks_list.append(block_dict)

        # Calculate total hours
        total_hours = sum(
            float(block.get("duration_hours", 0))
            for block in blocks_list
        )

        # Return JSON if requested
        if format == "json":
            return {
                "year": year,
                "month": month,
                "time_blocks": blocks_list,
                "total_hours": total_hours,
                "count": len(blocks_list),
            }

        # Otherwise return simple HTML timesheet
        from app.utils.timesheet_template import render_monthly_timesheet
        html_content = render_monthly_timesheet(year, month, blocks_list, total_hours)
        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Failed to fetch timesheet: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch timesheet: {str(e)}")


@app.get("/summary/week/{week_start}", tags=["Summary"])
async def get_week_summary(week_start: str):
    """
    Get summary for a specific week.

    Args:
        week_start: Week start date (YYYY-MM-DD format)

    Returns:
        Week summary with total hours and metadata
    """
    if not pb_client:
        raise HTTPException(status_code=503, detail="PocketBase client not initialized")

    try:
        # Parse date
        week_date = datetime.fromisoformat(week_start)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    try:
        # Fetch week summary
        filter_str = f'week_start = "{week_date.isoformat()}"'
        summaries = pb_client.get_full_list(
            pb_client.COLLECTION_WEEK_SUMMARIES,
            filter=filter_str
        )

        if not summaries:
            raise HTTPException(
                status_code=404,
                detail=f"No summary found for week starting {week_start}"
            )

        summary = summaries[0]

        # Convert to dict
        if hasattr(summary, "__dict__"):
            summary_dict = {
                k: v for k, v in summary.__dict__.items()
                if not k.startswith("_")
            }
        else:
            summary_dict = dict(summary)

        return summary_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch week summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")


# ============================================================================
# Export Endpoints
# ============================================================================


@app.get("/export/month/{year}/{month}", tags=["Export"])
async def export_month(
    year: int,
    month: int,
    format: str = Query("html", regex="^(html|csv|excel)$"),
):
    """
    Export monthly timesheet in specified format.

    Args:
        year: Year (e.g., 2026)
        month: Month (1-12)
        format: Export format (html, csv, or excel)

    Returns:
        Timesheet in requested format
    """
    if not exporter:
        raise HTTPException(status_code=503, detail="Exporter not initialized")

    # Validate month
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    try:
        if format == "html":
            html_content = exporter.export_html(year, month)
            return HTMLResponse(content=html_content)

        elif format == "csv":
            csv_content = exporter.export_csv(year, month)
            from io import StringIO
            import csv as csv_module
            from fastapi.responses import StreamingResponse

            # Create CSV response
            output = StringIO()
            output.write(csv_content)
            output.seek(0)

            filename = f"timesheet_{year}_{month:02d}.csv"
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        elif format == "excel":
            excel_file = exporter.export_excel(year, month)
            filename = f"timesheet_{year}_{month:02d}.xlsx"

            return FileResponse(
                excel_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=filename,
            )

    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ============================================================================
# User-Friendly Data Viewing Endpoints
# ============================================================================


@app.get("/viewer", response_class=HTMLResponse, tags=["Data Viewer"])
async def data_viewer():
    """
    Interactive data viewer with copy-to-clipboard functionality.

    Provides a beautiful web interface to view and copy all collection data.
    """
    from pathlib import Path

    viewer_path = Path(__file__).parent.parent / "data_viewer.html"

    if not viewer_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Data viewer not found. Make sure data_viewer.html exists in the project root."
        )

    with open(viewer_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    return HTMLResponse(content=html_content)


@app.get("/data/{collection}", tags=["Data Access"])
async def get_collection_data(
    collection: str,
    format: str = Query("html", regex="^(html|json)$")
):
    """
    Get all records from a collection in a user-friendly format.

    Args:
        collection: Collection name (settings, work_packages, project_specs,
                   raw_events, time_blocks, week_summaries,
                   calendar_accounts, email_accounts)
        format: Output format (html or json). Default: html

    Returns:
        Collection data as HTML table or JSON
    """
    if not pb_client:
        raise HTTPException(status_code=503, detail="PocketBase client not initialized")

    # Valid collections
    valid_collections = [
        "settings",
        "work_packages",
        "project_specs",
        "raw_events",
        "time_blocks",
        "week_summaries",
        "calendar_accounts",
        "email_accounts",
    ]

    if collection not in valid_collections:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid collection. Valid options: {', '.join(valid_collections)}"
        )

    try:
        # Fetch all records (no sort for better compatibility)
        records = pb_client.get_full_list(collection)

        # Convert to dicts
        records_list = []
        for record in records:
            if hasattr(record, "__dict__"):
                record_dict = {
                    k: v for k, v in record.__dict__.items()
                    if not k.startswith("_")
                }
            else:
                record_dict = dict(record)
            records_list.append(record_dict)

        # Return JSON if requested
        if format == "json":
            return {
                "collection": collection,
                "count": len(records_list),
                "records": records_list,
                "timestamp": datetime.now().isoformat(),
            }

        # Otherwise return HTML
        from app.utils.html_templates import render_collection_html
        html_content = render_collection_html(collection, records_list)
        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Failed to fetch {collection}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch data: {str(e)}"
        )


@app.get("/dashboard", tags=["Dashboard"])
async def dashboard():
    """
    Get dashboard overview with system statistics and recent activity.

    Returns:
        System overview including record counts, recent data, and configuration
    """
    if not pb_client:
        raise HTTPException(status_code=503, detail="PocketBase client not initialized")

    try:
        # Get counts for all collections
        counts = {}
        collections = [
            "settings",
            "work_packages",
            "project_specs",
            "raw_events",
            "time_blocks",
            "week_summaries",
            "calendar_accounts",
            "email_accounts",
        ]

        for collection in collections:
            try:
                counts[collection] = pb_client.count(collection)
            except:
                counts[collection] = 0

        # Get recent raw events (last 10)
        recent_events = []
        try:
            events = pb_client.get_list(
                "raw_events",
                page=1,
                per_page=10,
                sort="-created"
            )
            for event in events:
                if hasattr(event, "__dict__"):
                    event_dict = {
                        k: v for k, v in event.__dict__.items()
                        if not k.startswith("_")
                    }
                else:
                    event_dict = dict(event)
                recent_events.append(event_dict)
        except:
            pass

        # Get recent time blocks (last 10)
        recent_blocks = []
        try:
            blocks = pb_client.get_list(
                "time_blocks",
                page=1,
                per_page=10,
                sort="-created"
            )
            for block in blocks:
                if hasattr(block, "__dict__"):
                    block_dict = {
                        k: v for k, v in block.__dict__.items()
                        if not k.startswith("_")
                    }
                else:
                    block_dict = dict(block)
                recent_blocks.append(block_dict)
        except:
            pass

        # Get configuration summary
        config_summary = {}
        if config and config.settings:
            try:
                settings = config.settings
                config_summary = {
                    "work_week": f"{settings.core.work_week_start_day.value} to {settings.core.work_week_end_day.value}",
                    "target_hours": settings.core.target_hours_per_week,
                    "auto_fill_enabled": settings.core.auto_fill_enabled,
                    "wakatime_enabled": settings.wakatime.wakatime_enabled,
                    "github_enabled": settings.github.github_enabled,
                    "calendar_enabled": settings.calendar.calendar_enabled,
                    "gmail_enabled": settings.gmail.gmail_enabled,
                }
            except:
                pass

        # Get scheduler status
        scheduler_info = {}
        if scheduler:
            try:
                scheduler_info = scheduler.get_job_status()
            except:
                pass

        return {
            "timestamp": datetime.now().isoformat(),
            "system_status": "operational",
            "collection_counts": counts,
            "recent_events": recent_events,
            "recent_time_blocks": recent_blocks,
            "configuration": config_summary,
            "scheduler": scheduler_info,
            "quick_links": {
                "viewer": "/viewer",
                "api_docs": "/docs",
                "settings": "/data/settings",
                "work_packages": "/data/work_packages",
                "current_timesheet": "/timesheet/current",
            }
        }

    except Exception as e:
        logger.error(f"Dashboard failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Dashboard failed: {str(e)}"
        )


# ============================================================================
# Authentication Endpoints
# ============================================================================


class LoginRequest(BaseModel):
    """Login request model."""
    email: str
    password: str


@app.get("/login", response_class=HTMLResponse, tags=["Authentication"])
async def login_page():
    """Show login page."""
    from pathlib import Path

    login_path = Path(__file__).parent.parent / "login.html"

    if not login_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Login page not found"
        )

    with open(login_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    return HTMLResponse(content=html_content)


@app.post("/auth/login", tags=["Authentication"])
async def login(request: LoginRequest, response: Response):
    """
    Authenticate user and set auth cookie.

    Args:
        request: Login credentials
        response: FastAPI response to set cookie

    Returns:
        Success message and user data
    """
    from app.utils.auth import auth_service

    try:
        token, user_data = auth_service.authenticate(request.email, request.password)

        # Set auth cookie (14 days expiry to match PocketBase)
        response.set_cookie(
            key="auth_token",
            value=token,
            max_age=14 * 24 * 60 * 60,  # 14 days
            httponly=True,
            samesite="lax",
        )

        return {
            "success": True,
            "message": "Login successful",
            "user": user_data
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Login failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/auth/logout", tags=["Authentication"])
async def logout(response: Response):
    """Logout user by clearing auth cookie."""
    response.delete_cookie(key="auth_token")
    return {"success": True, "message": "Logged out successfully"}


@app.get("/auth/me", tags=["Authentication"])
async def get_current_user_info(user: dict = Depends(lambda: None)):
    """Get current authenticated user info."""
    from app.utils.auth import get_current_user
    from fastapi import Cookie

    auth_token = Cookie(None)

    try:
        user_data = get_current_user(auth_token)
        return {"authenticated": True, "user": user_data}
    except:
        return {"authenticated": False, "user": None}


# ============================================================================
# OAuth Endpoints
# ============================================================================


@app.get("/oauth/google/authorize", tags=["OAuth"])
async def google_oauth_authorize(service: str = Query("calendar", regex="^(calendar|gmail)$")):
    """
    Initiate Google OAuth flow for Calendar or Gmail.

    Args:
        service: Service to authorize (calendar or gmail)

    Returns:
        Redirect to Google consent screen
    """
    from fastapi.responses import RedirectResponse
    from app.utils.oauth import build_google_auth_url

    try:
        auth_url = build_google_auth_url(service)
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"OAuth authorization failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OAuth failed: {str(e)}")


@app.get("/oauth/google/callback", tags=["OAuth"])
async def google_oauth_callback(code: str, state: str):
    """
    Handle Google OAuth callback.

    Args:
        code: Authorization code from Google
        state: State parameter (contains service type)

    Returns:
        Success message and token storage confirmation
    """
    # TODO: Implement OAuth token exchange and storage
    # This requires implementing the full OAuth flow with token exchange
    return {
        "status": "success",
        "message": "OAuth callback received",
        "service": state,
        "note": "Full OAuth implementation pending"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
