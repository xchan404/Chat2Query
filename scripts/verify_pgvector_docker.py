import asyncio
import os
import sys
import subprocess

async def main():
    print("Testing Docker Environment for pgvector...")
    
    # Check if docker is running
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("Error: Docker daemon is not running. Please start Docker Desktop and try again.")
        sys.exit(1)
        
    print("Docker is running. Spin up docker-compose and run F4 hybrid verification...")
    print("To run the actual verification:")
    print("1. Ensure native PostgreSQL on 5432 is stopped.")
    print("2. Run: docker-compose up -d postgres")
    print("3. Run: alembic upgrade head")
    print("4. Run: pytest tests/integration/test_end_to_end_flow.py::test_integration_hybrid_chat -v")
    
if __name__ == "__main__":
    asyncio.run(main())
