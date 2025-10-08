"""
ClickHouse monitoring module for live EPS tracking (direct connection)
"""
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

try:
    from clickhouse_driver import Client
    CLICKHOUSE_DRIVER_AVAILABLE = True
except ImportError:
    CLICKHOUSE_DRIVER_AVAILABLE = False
    logger.warning(
        "clickhouse-driver not available. Install with: pip install clickhouse-driver>=0.2.7"
    )


class ClickHouseMonitor:
    """Monitor ClickHouse for Kafka metrics via direct connection"""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9000,
        database: str = "monitoring",
        user: str = "default",
        password: str = "",
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.client: Optional[Client] = None

    def connect(self) -> bool:
        """Establish connection to ClickHouse server"""
        if not CLICKHOUSE_DRIVER_AVAILABLE:
            logger.error(
                "clickhouse-driver package is not installed. Please install it with: pip install clickhouse-driver>=0.2.7"
            )
            return False

        try:
            self.client = Client(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            # Test connection
            self.client.execute("SELECT 1")
            logger.info(f"Connected to ClickHouse at {self.host}:{self.port}, database: {self.database}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse at {self.host}:{self.port}: {e}")
            self.client = None
            return False

    def disconnect(self):
        """Close ClickHouse connection"""
        if self.client:
            self.client.disconnect()
            self.client = None
            logger.info("Disconnected from ClickHouse server")

    def execute_query(self, query: str) -> Tuple[bool, str]:
        """Execute a ClickHouse query"""
        if not self.client:
            return False, "Not connected to ClickHouse"

        try:
            result = self.client.execute(query)
            if not result:
                return True, ""

            # Flatten tuples if needed
            output_lines = []
            for row in result:
                if isinstance(row, tuple):
                    output_lines.append("\t".join(str(v) for v in row))
                else:
                    output_lines.append(str(row))
            return True, "\n".join(output_lines)

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return False, str(e)

    def get_eps_for_topic(self, topic: str) -> Tuple[bool, Optional[float], str]:
        """Get the current OneMinuteRate (EPS) for a specific Kafka topic"""
        query = f"""
        SELECT OneMinuteRate
        FROM kafka_Broker_Topic_Metrics_data
        WHERE topic = '{topic}'
        ORDER BY timestamp DESC
        LIMIT 1
        """
        success, result = self.execute_query(query)
        if not success:
            return False, None, result

        try:
            if result.strip():
                eps_value = float(result.strip())
                return True, eps_value, "Success"
            else:
                return False, None, "No data found for topic"
        except ValueError as e:
            return False, None, f"Failed to parse EPS value: {e}"

    def get_topic_metrics(self, topic: str) -> Tuple[bool, Optional[Dict], str]:
        """Get comprehensive metrics for a topic"""
        query = f"""
        SELECT
            OneMinuteRate,
            FiveMinuteRate,
            FifteenMinuteRate,
            MeanRate,
            Count,
            timestamp
        FROM kafka_Broker_Topic_Metrics_data
        WHERE topic = '{topic}'
        ORDER BY timestamp DESC
        LIMIT 1
        """
        success, result = self.execute_query(query)
        if not success:
            return False, None, result

        try:
            fields = result.strip().split("\t")
            if len(fields) >= 6:
                metrics = {
                    "one_minute_rate": float(fields[0]),
                    "five_minute_rate": float(fields[1]),
                    "fifteen_minute_rate": float(fields[2]),
                    "mean_rate": float(fields[3]),
                    "count": float(fields[4]),
                    "timestamp": fields[5],
                }
                return True, metrics, "Success"
            else:
                return False, None, "Incomplete data received"
        except (ValueError, IndexError) as e:
            return False, None, f"Failed to parse metrics: {e}"

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# -------------------
# Example usage
# -------------------
if __name__ == "__main__":
    clickhouse_monitor = ClickHouseMonitor(
        host="10.32.3.50",  # same node as Streamlit app
        port=9000,
        database="monitoring",
        user="vuDataSim_tool",
        password="StrongPassword123"
    )

    if clickhouse_monitor.connect():
        success, eps, msg = clickhouse_monitor.get_eps_for_topic("azuresql-single-database-jdbc-metrics")
        if success:
            logger.info(f"Current EPS for topic: {eps}")
        else:
            logger.warning(f"Failed to get EPS: {msg}")
        clickhouse_monitor.disconnect()
