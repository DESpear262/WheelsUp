# WheelsUp Monitoring & Logging Infrastructure
# CloudWatch log groups, dashboards, and basic monitoring setup

# ============================================================================
# CloudWatch Log Groups
# ============================================================================

# Web application logs
resource "aws_cloudwatch_log_group" "wheelsup_web" {
  name              = "/wheelsup/web"
  retention_in_days = 30
  kms_key_id        = null # Use default encryption

  tags = {
    Name        = "wheelsup-web-logs"
    Application = "web"
    Environment = var.environment
  }
}

# ETL pipeline logs
resource "aws_cloudwatch_log_group" "wheelsup_etl" {
  name              = "/wheelsup/etl"
  retention_in_days = 90 # Keep ETL logs longer for debugging
  kms_key_id        = null

  tags = {
    Name        = "wheelsup-etl-logs"
    Application = "etl"
    Environment = var.environment
  }
}

# Application error logs (structured)
resource "aws_cloudwatch_log_group" "wheelsup_errors" {
  name              = "/wheelsup/errors"
  retention_in_days = 90
  kms_key_id        = null

  tags = {
    Name        = "wheelsup-error-logs"
    Application = "errors"
    Environment = var.environment
  }
}

# ============================================================================
# CloudWatch Alarms
# ============================================================================

# High error rate alarm
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "wheelsup-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ErrorCount"
  namespace           = "WheelsUp/Application"
  period              = "300" # 5 minutes
  statistic           = "Sum"
  threshold           = "10"  # More than 10 errors in 5 minutes
  alarm_description   = "This metric monitors application error rate"
  alarm_actions       = [] # Add SNS topic ARN for notifications

  tags = {
    Name        = "wheelsup-error-alarm"
    Environment = var.environment
  }
}

# ETL pipeline failure alarm
resource "aws_cloudwatch_metric_alarm" "etl_pipeline_failure" {
  alarm_name          = "wheelsup-etl-pipeline-failure"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ETLFailure"
  namespace           = "WheelsUp/ETL"
  period              = "3600" # 1 hour
  statistic           = "Sum"
  threshold           = "0"    # Any ETL failure
  alarm_description   = "This metric monitors ETL pipeline failures"
  alarm_actions       = [] # Add SNS topic ARN for notifications

  tags = {
    Name        = "wheelsup-etl-failure-alarm"
    Environment = var.environment
  }
}

# API response time alarm
resource "aws_cloudwatch_metric_alarm" "api_response_time" {
  alarm_name          = "wheelsup-api-slow-response"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "ResponseTime"
  namespace           = "WheelsUp/API"
  period              = "300" # 5 minutes
  statistic           = "Average"
  threshold           = "5000" # 5 seconds average response time
  alarm_description   = "This metric monitors API response time"
  alarm_actions       = [] # Add SNS topic ARN for notifications

  tags = {
    Name        = "wheelsup-api-response-alarm"
    Environment = var.environment
  }
}

# ============================================================================
# CloudWatch Dashboard
# ============================================================================

resource "aws_cloudwatch_dashboard" "wheelsup_main" {
  dashboard_name = "wheelsup-main-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # Application Overview
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["WheelsUp/Application", "RequestCount", { "stat": "Sum", "period": 300 }],
            [".", "ErrorCount", { "stat": "Sum" }],
            [".", "ResponseTime", { "stat": "Average" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Application Overview"
          period  = 300
        }
      },

      # ETL Pipeline Metrics
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["WheelsUp/ETL", "CrawlSuccess", { "stat": "Sum", "period": 3600 }],
            [".", "CrawlFailure", { "stat": "Sum" }],
            [".", "ETLProcessedRecords", { "stat": "Sum" }],
            [".", "ETLFailure", { "stat": "Sum" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ETL Pipeline Metrics"
          period  = 3600
        }
      },

      # API Performance
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["WheelsUp/API", "RequestCount", { "stat": "Sum", "period": 300 }],
            [".", "4XXError", { "stat": "Sum" }],
            [".", "5XXError", { "stat": "Sum" }],
            [".", "ResponseTime", { "stat": "Average" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "API Performance"
          period  = 300
        }
      },

      # Database Metrics
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", var.db_instance_id, { "stat": "Average" }],
            [".", "CPUUtilization", ".", ".", { "stat": "Average" }],
            [".", "FreeStorageSpace", ".", ".", { "stat": "Minimum" }],
            [".", "ReadLatency", ".", ".", { "stat": "Average" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Database Metrics"
          period  = 300
        }
      },

      # Log Insights - Recent Errors
      {
        type   = "log"
        x      = 0
        y      = 12
        width  = 24
        height = 6

        properties = {
          query = "fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 100"
          region = var.aws_region
          title  = "Recent Application Errors"
        }
      }
    ]
  })
}

# ============================================================================
# IAM Policy for CloudWatch Logging
# ============================================================================

resource "aws_iam_policy" "cloudwatch_logging" {
  name        = "wheelsup-cloudwatch-logging"
  description = "Policy for CloudWatch logging access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams",
          "logs:DescribeLogGroups"
        ]
        Resource = [
          aws_cloudwatch_log_group.wheelsup_web.arn,
          aws_cloudwatch_log_group.wheelsup_etl.arn,
          aws_cloudwatch_log_group.wheelsup_errors.arn,
          "${aws_cloudwatch_log_group.wheelsup_web.arn}/*",
          "${aws_cloudwatch_log_group.wheelsup_etl.arn}/*",
          "${aws_cloudwatch_log_group.wheelsup_errors.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = [
              "WheelsUp/Application",
              "WheelsUp/ETL",
              "WheelsUp/API"
            ]
          }
        }
      }
    ]
  })

  tags = {
    Name        = "wheelsup-cloudwatch-policy"
    Environment = var.environment
  }
}

# ============================================================================
# Outputs
# ============================================================================

output "cloudwatch_log_groups" {
  description = "CloudWatch log group names"
  value = {
    web_logs   = aws_cloudwatch_log_group.wheelsup_web.name
    etl_logs   = aws_cloudwatch_log_group.wheelsup_etl.name
    error_logs = aws_cloudwatch_log_group.wheelsup_errors.name
  }
}

output "cloudwatch_dashboard_url" {
  description = "URL to access the CloudWatch dashboard"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.wheelsup_main.dashboard_name}"
}

output "cloudwatch_logging_policy_arn" {
  description = "ARN of the CloudWatch logging IAM policy"
  value       = aws_iam_policy.cloudwatch_logging.arn
}
