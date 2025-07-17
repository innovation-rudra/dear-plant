#!/usr/bin/env python3
"""
Plant Care Application - Setup Test Script

This script tests the basic setup and connectivity of our Plant Care Application.
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath('.'))

async def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration...")
    
    try:
        from app.shared.config.settings import get_settings
        settings = get_settings()
        
        print(f"✅ Configuration loaded successfully")
        print(f"   - App Name: {settings.APP_NAME}")
        print(f"   - Version: {settings.APP_VERSION}")
        print(f"   - Environment: {settings.APP_ENV}")
        print(f"   - Debug: {settings.DEBUG}")
        print(f"   - Supabase URL: {settings.SUPABASE_URL}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_supabase_connection():
    """Test Supabase connection."""
    print("\n🏢 Testing Supabase connection...")
    
    try:
        from app.shared.config.supabase import get_supabase_manager
        
        supabase_manager = get_supabase_manager()
        health_result = await supabase_manager.health_check()
        
        if health_result.get("status") == "healthy":
            print("✅ Supabase connection successful")
            print(f"   - Status: {health_result.get('status')}")
            print(f"   - Database: {health_result.get('database')}")
            print(f"   - Auth: {health_result.get('auth')}")
            print(f"   - Storage: {health_result.get('storage')}")
            return True
        else:
            print(f"❌ Supabase connection failed: {health_result}")
            return False
            
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
        return False


async def test_database_connection():
    """Test database connection."""
    print("\n🗄️ Testing database connection...")
    
    try:
        from app.shared.infrastructure.database.connection import get_db_manager
        
        db_manager = get_db_manager()
        await db_manager.initialize()
        
        health_result = await db_manager.health_check()
        
        if health_result.get("status") == "healthy":
            print("✅ Database connection successful")
            print(f"   - Response time: {health_result.get('response_time', 0):.3f}s")
            print(f"   - Pool status: {health_result.get('pool_status', {})}")
            return True
        else:
            print(f"❌ Database connection failed: {health_result}")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


async def test_redis_connection():
    """Test Redis connection."""
    print("\n🔴 Testing Redis connection...")
    
    try:
        from app.shared.infrastructure.cache.redis_client import get_redis_manager
        
        redis_manager = get_redis_manager()
        await redis_manager.initialize()
        
        health_result = await redis_manager.health_check()
        
        if health_result.get("status") == "healthy":
            print("✅ Redis connection successful")
            print(f"   - Response time: {health_result.get('response_time', 0):.3f}s")
            print(f"   - Redis version: {health_result.get('redis_version')}")
            print(f"   - Connected clients: {health_result.get('connected_clients')}")
            return True
        else:
            print(f"❌ Redis connection failed: {health_result}")
            return False
            
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        print("   💡 Make sure Redis is running (docker-compose up -d redis)")
        return False


async def test_basic_database_operations():
    """Test basic database operations."""
    print("\n🔍 Testing basic database operations...")
    
    try:
        from app.shared.infrastructure.database.connection import DatabaseUtils
        
        # Test table existence
        tables_exist = await DatabaseUtils.check_table_exists("profiles")
        if tables_exist:
            print("✅ Database tables exist")
        else:
            print("❌ Database tables not found - run the SQL schema first")
            return False
        
        # Test basic query
        result = await DatabaseUtils.execute_raw_query("SELECT COUNT(*) FROM plant_library")
        plant_count = result[0][0] if result else 0
        print(f"✅ Basic query successful - {plant_count} plants in library")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False


async def test_logging():
    """Test logging system."""
    print("\n📝 Testing logging system...")
    
    try:
        from app.shared.utils.logging import setup_logging, get_logger
        
        # Setup logging
        setup_logging()
        
        # Test logger
        logger = get_logger(__name__)
        logger.info("Test log message", test_data={"key": "value"})
        
        print("✅ Logging system working")
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False


async def test_health_checks():
    """Test health check endpoints."""
    print("\n🏥 Testing health checks...")
    
    try:
        from app.monitoring.health_checks import HealthChecker
        
        health_checker = HealthChecker()
        
        # Test individual components
        db_health = await health_checker.check_database()
        print(f"   - Database: {db_health.get('status')}")
        
        redis_health = await health_checker.check_redis()
        print(f"   - Redis: {redis_health.get('status')}")
        
        supabase_health = await health_checker.check_supabase()
        print(f"   - Supabase: {supabase_health.get('status')}")
        
        # Test overall health
        overall_health = await health_checker.run_all_checks(include_external=False)
        
        if overall_health.get("status") == "healthy":
            print("✅ All health checks passed")
            return True
        else:
            print(f"❌ Some health checks failed: {overall_health}")
            return False
            
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Plant Care Application - Setup Test\n")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Supabase Connection", test_supabase_connection),
        ("Database Connection", test_database_connection),
        ("Redis Connection", test_redis_connection),
        ("Database Operations", test_basic_database_operations),
        ("Logging System", test_logging),
        ("Health Checks", test_health_checks),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("-" * 25)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Start the application: uvicorn app.main:app --reload")
        print("   2. Visit http://localhost:8000/docs for API documentation")
        print("   3. Check health: http://localhost:8000/health/detailed")
    else:
        print("⚠️  Some tests failed. Please check the configuration and services.")
        print("\n🔧 Common fixes:")
        print("   1. Make sure Docker services are running: docker-compose up -d")
        print("   2. Check your .env file has correct Supabase credentials")
        print("   3. Run the SQL schema in your Supabase dashboard")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)