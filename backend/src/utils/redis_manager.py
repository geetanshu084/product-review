"""
Redis Manager - Centralized Redis client initialization
Provides a singleton Redis client instance for the entire application

IMPORTANT: Redis is REQUIRED for this application to run.
If Redis is not available at startup, the application will fail immediately.
"""

import os
import redis
import sys


class RedisManager:
    """Singleton Redis client manager - Redis is REQUIRED"""

    _instance: redis.Redis = None
    _initialized: bool = False

    @classmethod
    def get_client(cls, force_reconnect: bool = False) -> redis.Redis:
        """
        Get Redis client instance (creates if not exists)

        All configuration is read from environment variables:
        - REDIS_HOST: Redis server host (default: localhost)
        - REDIS_PORT: Redis server port (default: 6379)
        - REDIS_DB: Redis database number (default: 0)
        - REDIS_PASSWORD: Redis password (optional)

        Args:
            force_reconnect: Force create a new connection

        Returns:
            Redis client instance (guaranteed to be valid)

        Raises:
            SystemExit: If Redis connection fails
        """
        if force_reconnect or not cls._initialized:
            cls._instance = cls._create_client()
            cls._initialized = True

        return cls._instance

    @classmethod
    def _create_client(cls) -> redis.Redis:
        """
        Create and test Redis client connection

        Returns:
            Redis client instance

        Raises:
            SystemExit: If Redis connection fails
        """
        try:
            client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                db=int(os.getenv('REDIS_DB', '0')),
                password=os.getenv('REDIS_PASSWORD'),
                decode_responses=True
            )

            # Test connection - this will raise an exception if Redis is not available
            client.ping()
            print(f"✓ Redis connected: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}")
            return client

        except redis.ConnectionError as e:
            print(f"\n❌ FATAL: Redis connection failed!")
            print(f"   Error: {str(e)}")
            print(f"   Make sure Redis is running at {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}")
            print(f"\n   To start Redis:")
            print(f"   - macOS/Linux: redis-server")
            print(f"   - Docker: docker run -d -p 6379:6379 redis")
            sys.exit(1)

        except Exception as e:
            print(f"\n❌ FATAL: Redis initialization error!")
            print(f"   Error: {str(e)}")
            sys.exit(1)

    @classmethod
    def close(cls):
        """Close Redis connection"""
        if cls._instance:
            try:
                cls._instance.close()
                print("✓ Redis connection closed")
            except:
                pass
            finally:
                cls._instance = None
                cls._initialized = False


def get_redis_client() -> redis.Redis:
    """
    Convenience function to get Redis client

    Returns:
        Redis client instance (guaranteed to be valid)

    Raises:
        SystemExit: If Redis connection fails
    """
    return RedisManager.get_client()
