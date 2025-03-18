param(
    [string]$task
)

Write-Output "Starting $task..."

if ($task -eq "dev-ui") {
    cd ui
    npm run build-dev
} elseif ($task -eq "dev-backend") {
    fastapi dev app.py --port 8081
} else {
    Write-Error "Task $task is not recognized."
}

Write-Output "Stopped $task."
