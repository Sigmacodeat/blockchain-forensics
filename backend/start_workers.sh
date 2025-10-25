#!/bin/bash
# Start all Kafka Consumer Workers

echo "Starting Kafka Consumer Workers..."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start Trace Consumer
echo "Starting Trace Consumer..."
python -m app.workers.trace_consumer --group trace-consumer &
TRACE_PID=$!

# Start Enrichment Consumer
echo "Starting Enrichment Consumer..."
python -m app.workers.enrichment_consumer --group enrichment-consumer &
ENRICH_PID=$!

# Start Alert Consumer
echo "Starting Alert Consumer..."
python -m app.workers.alert_consumer --group alert-consumer &
ALERT_PID=$!

# Start DLQ Consumer (monitoring only)
echo "Starting DLQ Consumer..."
python -m app.workers.dlq_consumer --group dlq-monitor &
DLQ_PID=$!

echo "All workers started!"
echo "Trace Consumer PID: $TRACE_PID"
echo "Enrichment Consumer PID: $ENRICH_PID"
echo "Alert Consumer PID: $ALERT_PID"
echo "DLQ Consumer PID: $DLQ_PID"

# Trap SIGINT and SIGTERM to gracefully stop all workers
trap "echo 'Stopping all workers...'; kill $TRACE_PID $ENRICH_PID $ALERT_PID $DLQ_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Wait for all background processes
wait
