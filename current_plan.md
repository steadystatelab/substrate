# Implementation Plan - Bruck Monitor V1 (Config & Calibration)

Refactor the monitoring utility to support external configuration and session-based calibration reporting.

## User Review Required

> [!IMPORTANT]
> The script will now attempt to load settings from `G:\My Drive\_ANTIGRAV_BUILD_CORE\01_Blueprints\config.json`. If this file is modified, the script must be restarted to ingest new thresholds.

> [!NOTE]
> A detailed calibration report (Mean and 95th Percentile) will be generated and saved to `G:\My Drive\_ANTIGRAV_BUILD_CORE\03_Telemetry\calibration_report.json` exactly 5 minutes after startup.

## Proposed Changes

### Configuration Management

#### [MODIFY] [bruck_monitor_v1.py](file:///G:/My%20Drive/_ANTIGRAV_BUILD_CORE/02_The_Foundry/bruck_monitor_v1.py)
- **External Config**: Implement JSON-based configuration loading/initialization.
- **Path Resolution**: Use `ROOT_DIR` from config to resolve telemetry and blueprint paths.

### Calibration Reporter

#### [MODIFY] [bruck_monitor_v1.py](file:///G:/My%20Drive/_ANTIGRAV_BUILD_CORE/02_The_Foundry/bruck_monitor_v1.py)
- **Session Buffers**: Maintain temporary lists to store entropy and fragmentation data during the 5-minute calibration phase.
- **Statistical Analysis**: Calculate Mean and 95th Percentile upon completion of the calibration threshold.
- **JSON Export**: Save analysis results to `calibration_report.json`.

### Kernel Shutdown

#### [MODIFY] [bruck_monitor_v1.py](file:///G:/My%20Drive/_ANTIGRAV_BUILD_CORE/02_The_Foundry/bruck_monitor_v1.py)
- **Explicit Closure**: Ensure the named pipe handle is explicitly closed in the `finally` block to prevent resource leaks.

## Verification Plan

### Automated Tests
- Run syntax check.
- Delete `config.json` and verify the script regenerates it with defaults.
- Verify that `calibration_report.json` is created after 3000 cycles.

### Manual Verification
- Modify `ENTROPY_THRESHOLD` in `config.json` and verify the script uses the new value after restart.
