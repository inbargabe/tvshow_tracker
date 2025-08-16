import functools
import time
import logging
import boto3
from flask import request, g
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize CloudWatch client
cloudwatch = boto3.client('cloudwatch')

BATCH_INTERVAL = 60

def log_api_call(func):
    """Decorator to log API calls with basic dimensions"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint = request.endpoint or 'unknown'
        method = request.method
        user_agent = request.headers.get('User-Agent', 'unknown')

        # Store in g for use in metrics decorator
        g.start_time = start_time
        g.endpoint = endpoint
        g.method = method

        # Log the incoming request
        logger.info(
            "API_CALL_START",
            extra={
                'endpoint': endpoint,
                'method': method,
                'user_agent': user_agent,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        try:
            # Execute the function
            result = func(*args, **kwargs)

            # Calculate duration
            duration = time.time() - start_time

            # Determine status code from result
            if isinstance(result, tuple):
                status_code = result[1]
            else:
                status_code = 200

            # Log successful completion
            logger.info(
                "API_CALL_SUCCESS",
                extra={
                    'endpoint': endpoint,
                    'method': method,
                    'status_code': status_code,
                    'duration_ms': round(duration * 1000, 2),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            return result

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            logger.error(
                "API_CALL_ERROR",
                extra={
                    'endpoint': endpoint,
                    'method': method,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'duration_ms': round(duration * 1000, 2),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            raise

    return wrapper


def track_metrics(func):
    """Decorator to send metrics to CloudWatch"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)

            # Get values from g (set by log_api_call decorator)
            start_time = getattr(g, 'start_time', time.time())
            endpoint = getattr(g, 'endpoint', 'unknown')
            method = getattr(g, 'method', 'unknown')

            duration = time.time() - start_time

            # Determine status code
            if isinstance(result, tuple):
                status_code = result[1]
            else:
                status_code = 200

            # Send metrics to CloudWatch
            send_metrics_to_cloudwatch(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                duration=duration,
                success=True
            )

            return result

        except Exception as e:
            # Get values from g
            start_time = getattr(g, 'start_time', time.time())
            endpoint = getattr(g, 'endpoint', 'unknown')
            method = getattr(g, 'method', 'unknown')

            duration = time.time() - start_time

            # Send error metrics
            send_metrics_to_cloudwatch(
                endpoint=endpoint,
                method=method,
                status_code=500,
                duration=duration,
                success=False,
                error_type=type(e).__name__
            )

            raise

    return wrapper


def send_metrics_to_cloudwatch(endpoint, method, status_code, duration, success, error_type=None):
    """Send custom metrics to CloudWatch"""
    try:
        namespace = 'TVShowTracker/API'
        timestamp = datetime.utcnow()

        # Base dimensions
        dimensions = [
            {'Name': 'Endpoint', 'Value': endpoint},
            {'Name': 'Method', 'Value': method},
            {'Name': 'StatusCode', 'Value': str(status_code)}
        ]

        # Add error type if applicable
        if error_type:
            dimensions.append({'Name': 'ErrorType', 'Value': error_type})

        metric_data = [
            {
                'MetricName': 'RequestCount',
                'Dimensions': dimensions,
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': timestamp
            },
            {
                'MetricName': 'ResponseTime',
                'Dimensions': dimensions,
                'Value': duration * 1000,  # Convert to milliseconds
                'Unit': 'Milliseconds',
                'Timestamp': timestamp
            }
        ]

        # Add success/error specific metrics
        if success:
            metric_data.append({
                'MetricName': 'SuccessCount',
                'Dimensions': dimensions,
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': timestamp
            })
        else:
            metric_data.append({
                'MetricName': 'ErrorCount',
                'Dimensions': dimensions,
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': timestamp
            })

        # Send metrics to CloudWatch
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=metric_data
        )

        logger.debug(f"Sent metrics to CloudWatch for {endpoint}")

    except Exception as e:
        # Don't let metrics failure break the application
        logger.error(f"Failed to send metrics to CloudWatch: {str(e)}")


def log_database_operation(operation_type):
    """Decorator specifically for database operations"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            logger.info(
                "DB_OPERATION_START",
                extra={
                    'operation_type': operation_type,
                    'function': func.__name__,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    "DB_OPERATION_SUCCESS",
                    extra={
                        'operation_type': operation_type,
                        'function': func.__name__,
                        'duration_ms': round(duration * 1000, 2),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    "DB_OPERATION_ERROR",
                    extra={
                        'operation_type': operation_type,
                        'function': func.__name__,
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'duration_ms': round(duration * 1000, 2),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )

                raise

        return wrapper

    return decorator