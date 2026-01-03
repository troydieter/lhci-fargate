"""
Configuration constants for LHCI Fargate deployment
"""

# Container Configuration
LHCI_CONTAINER_IMAGE = "patrickhulce/lhci-server:0.14.0"
LHCI_CONTAINER_PORT = 9001
LHCI_CONTAINER_USER = "1001:1001"

# ECS Configuration
FARGATE_CPU = 512
FARGATE_MEMORY_MB = 1024
MIN_CAPACITY = 1
MAX_CAPACITY = 4
CPU_TARGET_UTILIZATION = 75
MEMORY_TARGET_UTILIZATION = 80

# Health Check Configuration
HEALTH_CHECK_PATH = "/healthz"
HEALTH_CHECK_CODES = "200,302"
HEALTH_CHECK_INTERVAL_SECONDS = 30
HEALTH_CHECK_TIMEOUT_SECONDS = 5

# EFS Configuration
EFS_MOUNT_PATH = "/data"
EFS_ACCESS_POINT_PATH = "/lhci-data"
EFS_USER_ID = 1001
EFS_GROUP_ID = 1001

# Logging Configuration
LOG_RETENTION_DAYS = 30

# Auto Scaling Configuration
SCALE_IN_COOLDOWN_MINUTES = 5
SCALE_OUT_COOLDOWN_MINUTES = 2

# Database Configuration
DB_ENGINE = "postgres"
DB_PORT = 5432
DB_NAME = "lhci"
DB_USERNAME = "lhci_admin"
AURORA_MIN_CAPACITY = 0.5  # Minimum ACUs (Aurora Capacity Units)
AURORA_MAX_CAPACITY = 1.0  # Maximum ACUs for small workload

# Environment Variables (connection URL will be constructed dynamically)
CONTAINER_ENVIRONMENT_BASE = {
    "LHCI_STORAGE__SQL_DIALECT": "postgres"
    # LHCI_STORAGE__SQL_CONNECTION_URL will be added dynamically with secrets
}
