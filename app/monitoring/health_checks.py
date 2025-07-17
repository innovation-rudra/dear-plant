"""
Plant Care Application - Health Check Endpoints
"""
import asyncio
import time
from typing import Dict, Any, List

from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
import structlog

"""
Plant Care Application - Health Check Endpoints
"""
import asyncio
import time
from typing import Dict, Any, List

from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
import structlog

from app.shared.config.settings import get_settings
from app.shared.infrastructure.database.connection import get_db_manager
from app.shared.infrastructure.cache.redis_client import get_redis_manager
from app.shared.config.supabase import get_supabase_manager

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()


class HealthChecker:
    """Health check utility class for Plant Care Application."""
    
    def __init__(self):
        self.start_time = time.time()
        self.failure_threshold = settings.HEALTH_CHECK_FAILURE_THRESHOLD
        self.timeout = settings.HEALTH_CHECK_TIMEOUT
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            db_manager = get_db_manager()
            result = await db_manager.health_check()
            
            return {
                "status": "healthy" if result.get("status") == "healthy" else "unhealthy",
                "details": result,
                "component": "database",
            }
            
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "component": "database",
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            redis_manager = get_redis_manager()
            result = await redis_manager.health_check()
            
            return {
                "status": "healthy" if result.get("status") == "healthy" else "unhealthy",
                "details": result,
                "component": "redis",
            }
            
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "component": "redis",
            }
    
    async def check_supabase(self) -> Dict[str, Any]:
        """Check Supabase health."""
        try:
            supabase_manager = get_supabase_manager()
            result = await supabase_manager.health_check()
            
            return {
                "status": "healthy" if result.get("status") == "healthy" else "unhealthy",
                "details": result,
                "component": "supabase",
            }
            
        except Exception as e:
            logger.error("Supabase health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "component": "supabase",
            }
    
    async def check_external_apis(self) -> Dict[str, Any]:
        """Check external API connectivity (basic ping)."""
        try:
            import httpx
            
            # Test external APIs with timeout
            apis_to_check = [
                {
                    "name": "OpenWeatherMap",
                    "url": "https://api.openweathermap.org/data/2.5/weather",
                    "params": {"q": "London", "appid": "test"}
                },
                {
                    "name": "PlantNet",
                    "url": "https://my-api.plantnet.org/v2/identify",
                    "method": "HEAD"
                }
            ]
            
            api_results = []
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                for api in apis_to_check:
                    try:
                        start_time = time.time()
                        
                        if api.get("method") == "HEAD":
                            response = await client.head(api["url"])
                        else:
                            response = await client.get(api["url"], params=api.get("params", {}))
                        
                        response_time = time.time() - start_time
                        
                        api_results.append({
                            "name": api["name"],
                            "status": "healthy" if response.status_code < 500 else "unhealthy",
                            "status_code": response.status_code,
                            "response_time": response_time,
                        })
                        
                    except Exception as e:
                        api_results.append({
                            "name": api["name"],
                            "status": "unhealthy",
                            "error": str(e),
                        })
            
            # Determine overall external API health
            healthy_apis = sum(1 for api in api_results if api["status"] == "healthy")
            overall_status = "healthy" if healthy_apis > 0 else "unhealthy"
            
            return {
                "status": overall_status,
                "details": {
                    "apis": api_results,
                    "healthy_count": healthy_apis,
                    "total_count": len(api_results),
                },
                "component": "external_apis",
            }
            
        except Exception as e:
            logger.error("External API health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "component": "external_apis",
            }
    
    async def check_application_metrics(self) -> Dict[str, Any]:
        """Check application-specific metrics."""
        try:
            uptime = time.time() - self.start_time
            
            # Check memory usage (basic)
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            # Check disk space
            disk_usage = psutil.disk_usage('/')
            disk_free_percent = (disk_usage.free / disk_usage.total) * 100
            
            # Determine health based on metrics
            status = "healthy"
            warnings = []
            
            if memory_info.rss > 1024 * 1024 * 1024:  # 1GB
                warnings.append("High memory usage")
            
            if cpu_percent > 80:
                warnings.append("High CPU usage")
            
            if disk_free_percent < 10:
                warnings.append("Low disk space")
                status = "unhealthy"
            
            return {
                "status": status,
                "details": {
                    "uptime_seconds": uptime,
                    "memory_usage_mb": memory_info.rss / 1024 / 1024,
                    "cpu_percent": cpu_percent,
                    "disk_free_percent": disk_free_percent,
                    "warnings": warnings,
                },
                "component": "application_metrics",
            }
            
        except Exception as e:
            logger.error("Application metrics check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "component": "application_metrics",
            }
    
    async def run_all_checks(self, include_external: bool = False) -> Dict[str, Any]:
        """Run all health checks."""
        checks = [
            self.check_database(),
            self.check_redis(),
            self.check_supabase(),
            self.check_application_metrics(),
        ]
        
        if include_external:
            checks.append(self.check_external_apis())
        
        # Run checks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*checks, return_exceptions=True),
                timeout=self.timeout
            )
            
            # Process results
            health_results = []
            overall_status = "healthy"
            
            for result in results:
                if isinstance(result, Exception):
                    health_results.append({
                        "status": "unhealthy",
                        "error": str(result),
                        "component": "unknown",
                    })
                    overall_status = "unhealthy"
                else:
                    health_results.append(result)
                    if result["status"] != "healthy":
                        overall_status = "unhealthy"
            
            return {
                "status": overall_status,
                "timestamp": time.time(),
                "version": settings.APP_VERSION,
                "environment": settings.APP_ENV,
                "checks": health_results,
            }
            
        except asyncio.TimeoutError:
            logger.error("Health checks timed out")
            return {
                "status": "unhealthy",
                "error": "Health checks timed out",
                "timestamp": time.time(),
                "version": settings.APP_VERSION,
                "environment": settings.APP_ENV,
            }


# Create global health checker instance
health_checker = HealthChecker()


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    Liveness probe endpoint.
    
    This endpoint checks if the application is running and responsive.
    Used by Kubernetes/Docker for liveness probes.
    """
    return {
        "status": "alive",
        "timestamp": time.time(),
        "version": settings.APP_VERSION,
        "uptime": time.time() - health_checker.start_time,
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """
    Readiness probe endpoint.
    
    This endpoint checks if the application is ready to serve traffic.
    Used by Kubernetes/Docker for readiness probes.
    """
    try:
        # Run basic checks for readiness
        db_check = await health_checker.check_database()
        redis_check = await health_checker.check_redis()
        supabase_check = await health_checker.check_supabase()
        
        # Check if all critical components are healthy
        if all(check["status"] == "healthy" for check in [db_check, redis_check, supabase_check]):
            return {
                "status": "ready",
                "timestamp": time.time(),
                "version": settings.APP_VERSION,
                "checks": {
                    "database": db_check["status"],
                    "redis": redis_check["status"],
                    "supabase": supabase_check["status"],
                },
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "not_ready",
                    "timestamp": time.time(),
                    "checks": {
                        "database": db_check["status"],
                        "redis": redis_check["status"],
                        "supabase": supabase_check["status"],
                    },
                }
            )
            
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": time.time(),
            }
        )


@router.get("/startup", status_code=status.HTTP_200_OK)
async def startup_check():
    """
    Startup probe endpoint.
    
    This endpoint checks if the application has completed startup.
    Used by Kubernetes for startup probes.
    """
    try:
        # Check if application has been running for minimum time
        uptime = time.time() - health_checker.start_time
        minimum_startup_time = 10  # seconds
        
        if uptime < minimum_startup_time:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "starting",
                    "uptime": uptime,
                    "minimum_startup_time": minimum_startup_time,
                    "timestamp": time.time(),
                }
            )
        
        # Run startup checks
        checks = await health_checker.run_all_checks(include_external=False)
        
        if checks["status"] == "healthy":
            return {
                "status": "started",
                "timestamp": time.time(),
                "uptime": uptime,
                "version": settings.APP_VERSION,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "startup_failed",
                    "checks": checks,
                    "timestamp": time.time(),
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Startup check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "startup_failed",
                "error": str(e),
                "timestamp": time.time(),
            }
        )


@router.get("/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check():
    """
    Detailed health check endpoint.
    
    This endpoint provides comprehensive health information about all components.
    Should be used sparingly as it can be resource-intensive.
    """
    try:
        # Run all checks including external APIs
        health_data = await health_checker.run_all_checks(include_external=True)
        
        # Add additional metadata
        health_data.update({
            "build_info": {
                "version": settings.APP_VERSION,
                "environment": settings.APP_ENV,
                "debug": settings.DEBUG,
            },
            "runtime_info": {
                "uptime_seconds": time.time() - health_checker.start_time,
                "python_version": f"{settings.APP_VERSION}",  # Add actual Python version if needed
                "host_info": "containerized",  # Add actual host info if needed
            },
        })
        
        # Return appropriate status code
        if health_data["status"] == "healthy":
            return health_data
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=health_data
            )
            
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time(),
                "version": settings.APP_VERSION,
            }
        )


@router.get("/components/{component}", status_code=status.HTTP_200_OK)
async def component_health_check(component: str):
    """
    Check health of a specific component.
    
    Args:
        component: Component name (database, redis, supabase, external_apis, metrics)
    """
    try:
        component_checks = {
            "database": health_checker.check_database,
            "redis": health_checker.check_redis,
            "supabase": health_checker.check_supabase,
            "external_apis": health_checker.check_external_apis,
            "metrics": health_checker.check_application_metrics,
        }
        
        if component not in component_checks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": f"Component '{component}' not found",
                    "available_components": list(component_checks.keys()),
                }
            )
        
        # Run specific component check
        result = await component_checks[component]()
        
        if result["status"] == "healthy":
            return result
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=result
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Component health check failed", component=component, error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "component": component,
                "error": str(e),
                "timestamp": time.time(),
            }
        )


# Add route for Prometheus metrics integration
@router.get("/metrics", include_in_schema=False)
async def health_metrics():
    """
    Health metrics endpoint for Prometheus scraping.
    
    This endpoint provides health metrics in a format suitable for Prometheus.
    """
    try:
        health_data = await health_checker.run_all_checks(include_external=False)
        
        # Convert health data to Prometheus metrics format
        metrics = []
        
        # Overall health metric
        health_status = 1 if health_data["status"] == "healthy" else 0
        metrics.append(f"plant_care_health_status {health_status}")
        
        # Component health metrics
        for check in health_data.get("checks", []):
            component = check.get("component", "unknown")
            status_value = 1 if check["status"] == "healthy" else 0
            metrics.append(f'plant_care_component_health{{component="{component}"}} {status_value}')
        
        # Application metrics
        uptime = time.time() - health_checker.start_time
        metrics.append(f"plant_care_uptime_seconds {uptime}")
        
        return "\n".join(metrics)
        
    except Exception as e:
        logger.error("Health metrics generation failed", error=str(e))
        return "plant_care_health_status 0\n"


# Export router
__all__ = ["router", "HealthChecker", "health_checker"]