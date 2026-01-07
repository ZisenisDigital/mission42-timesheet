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

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.pocketbase_client import PocketBaseClient
from app.config import Config
from app.services.scheduler import SchedulerService
from app.services.exporters import MonthlyExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
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
        "documentation": "/docs",
        "health": "/health",
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
async def get_current_timesheet():
    """Get timesheet for current month."""
    now = datetime.now()
    return await get_timesheet_month(now.year, now.month)


@app.get("/timesheet/month/{year}/{month}", tags=["Timesheet"])
async def get_timesheet_month(year: int, month: int):
    """
    Get timesheet data for a specific month.

    Args:
        year: Year (e.g., 2026)
        month: Month (1-12)

    Returns:
        Time blocks for the specified month
    """
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

        return {
            "year": year,
            "month": month,
            "time_blocks": blocks_list,
            "total_hours": total_hours,
            "count": len(blocks_list),
        }

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
