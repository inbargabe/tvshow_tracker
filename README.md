# TV Show Tracker Flask App

A simple Flask application that helps users track their progress in TV shows using AWS DynamoDB for storage and CloudWatch for logging and metrics.

## Features

- **Track TV Show Progress**: Users can store and update their current season and episode for any TV show
- **User Management**: View all shows a user is currently watching
- **Complete Overview**: Admin endpoint to view all entries in the system
- **Logging & Metrics**: Comprehensive logging with CloudWatch integration
- **AWS Integration**: Uses DynamoDB for data persistence and CloudWatch for monitoring

## Project Structure

```
tv-show-tracker/
├── app.py                          # Flask app initialization
├── infra/
│   ├── __init__.py
│   └── api.py                      # API routes and DynamoDB operations
├── utils/
│   ├── __init__.py
│   └── decorators.py               # Logging and metrics decorators
├── scripts/
│   └── setup_dynamodb.py           # DynamoDB table setup script
├── requirements.txt                # Python dependencies
├── cloudwatch-agent-config.json   # CloudWatch agent configuration
└── README.md                       # This file
```

## API Endpoints

### 1. Get Episode Information
**GET** `/api/show_episode?username={username}&tv_show={tv_show}`

Returns the current season and episode for a specific user and TV show.

**Example:**
```bash
curl "http://localhost:5000/api/show_episode?username=john_doe&tv_show=Breaking%20Bad"
```

### 2. Get User's Shows
**GET** `/api/show_user?username={username}`

Returns all TV shows that a user is currently tracking.

**Example:**
```bash
curl "http://localhost:5000/api/show_user?username=john_doe"
```

### 3. Update Episode
**POST** `/api/update_episode`

Adds or updates episode information for a user's TV show.

**Request Body:**
```json
{
    "username": "john_doe",
    "tv_show": "Breaking Bad",
    "season": 3,
    "episode": 8
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/update_episode \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","tv_show":"Breaking Bad","season":3,"episode":8}'
```

### 4. Show All Entries
**GET** `/api/show_all`

Returns all entries in the database (admin function).

**Example:**
```bash
curl "http://localhost:5000/api/show_all"
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- AWS CLI configured with appropriate permissions
- AWS account with DynamoDB and CloudWatch access

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up DynamoDB Table

```bash
python scripts/setup_dynamodb.py
```

This will create a table named `tv_show_tracker` with the following schema:
- **Partition Key**: `username` (String)
- **Sort Key**: `tv_show` (String)
- **Attributes**: `season` (Number), `episode` (Number), `last_updated` (String)

### 4. Environment Variables

Set the following environment variables:

```bash
export AWS_REGION=us-east-1
export DYNAMODB_TABLE=tv_show_tracker
```

### 5. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## AWS Permissions Required

Your AWS credentials need the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/tv_show_tracker"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData"
            ],
            "Resource": "*"
        }
    ]
}
```

## CloudWatch Integration

### Logs
The application sends structured logs to CloudWatch with the following dimensions:
- Endpoint
- Method
- Status Code
- Error Type (for errors)
- Duration

### Metrics
Custom metrics are sent to the `TVShowTracker/API` namespace:

- **RequestCount**: Total number of API requests
- **ResponseTime**: API response time in milliseconds
- **SuccessCount**: Number of successful requests
- **ErrorCount**: Number of failed requests

### CloudWatch Agent Setup

1. Install CloudWatch agent on your EC2 instance
2. Use the provided `cloudwatch-agent-config.json` configuration
3. Start the agent:

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:cloudwatch-agent-config.json \
    -s
```

## Production Deployment

### Using Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:

```bash
docker build -t tv-show-tracker .
docker run -p 5000:5000 \
  -e AWS_REGION=us-east-1 \
  -e DYNAMODB_TABLE=tv_show_tracker \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  tv-show-tracker
```

## Monitoring and Alerting

### CloudWatch Dashboards

Create dashboards to monitor:
- API request rates
- Error rates
- Response times
- DynamoDB throttling
- System metrics (CPU, memory, disk)

### Recommended Alarms

1. **High Error Rate**
   - Metric: `ErrorCount`
   - Threshold: > 10 errors in 5 minutes

2. **High Response Time**
   - Metric: `ResponseTime`
   - Threshold: > 2000ms average over 5 minutes

3. **DynamoDB Throttling**
   - Metric: `DynamoDB ThrottledRequests`
   - Threshold: > 0

## Testing

### Manual Testing Examples

```bash
# Test update episode
curl -X POST http://localhost:5000/api/update_episode \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","tv_show":"The Office","season":2,"episode":5}'

# Test get episode
curl "http://localhost:5000/api/show_episode?username=test_user&tv_show=The%20Office"

# Test get user shows
curl "http://localhost:5000/api/show_user?username=test_user"

# Test show all
curl "http://localhost:5000/api/show_all"
```

### Response Examples

**Successful Episode Update:**
```json
{
    "message": "Episode updated successfully",
    "username": "test_user",
    "tv_show": "The Office",
    "season": 2,
    "episode": 5
}
```

**Get Episode Response:**
```json
{
    "username": "test_user",
    "tv_show": "The Office",
    "season": 2,
    "episode": 5,
    "last_updated": "2025-01-15T10:30:00.123456"
}
```

**Get User Shows Response:**
```json
{
    "username": "test_user",
    "shows": [
        {
            "tv_show": "The Office",
            "season": 2,
            "episode": 5,
            "last_updated": "2025-01-15T10:30:00.123456"
        },
        {
            "tv_show": "Breaking Bad",
            "season": 1,
            "episode": 3,
            "last_updated": "2025-01-14T15:20:00.789012"
        }
    ],
    "total_shows": 2
}
```

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Missing or invalid parameters
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Database or server errors

All errors are logged with appropriate context for debugging.

## Security Considerations

1. **Input Validation**: All inputs are validated for type and range
2. **Error Handling**: Sensitive information is not exposed in error messages
3. **AWS IAM**: Use least-privilege IAM roles
4. **Environment Variables**: Sensitive configuration should use environment variables
5. **HTTPS**: Use HTTPS in production with proper SSL certificates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Troubleshooting

### Common Issues

1. **DynamoDB Access Denied**
   - Check AWS credentials and IAM permissions
   - Verify the table name matches the environment variable

2. **CloudWatch Metrics Not Appearing**
   - Check CloudWatch permissions
   - Verify AWS region configuration
   - Check CloudWatch agent logs

3. **Application Won't Start**
   - Check all dependencies are installed
   - Verify Python version compatibility
   - Check environment variables are set

### Logs Location

- Application logs: CloudWatch Logs `/aws/ec2/tv-show-tracker`
- System logs: `/var/log/tv-show-tracker/app.log`
- CloudWatch agent logs: `/opt/aws/amazon-cloudwatch-agent/logs/`