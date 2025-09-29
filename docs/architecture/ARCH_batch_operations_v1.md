# Batch Operations Architecture

## Service Layer Criticality
| Benefit | Description |
|--------|-------------|
| Consistent Generation | Correct format/params |
| Error Handling | Centralized recovery |
| Logging | Monitoring/debug |
| Queue Mgmt | Auto start/stop |
| Thread Safety | No races |
| Extensibility | Add without UI changes |

## Issue Indicators
| Sign | Description |
|------|-------------|
| Direct Queue | start/stop in UI |
| String Construction | UI cmd building |
| Dupe Handling | Scattered logic |
| Business in UI | Beyond interaction |
| Tight Coupling | Direct low-level refs |

## Best Practices
| Practice | Details |
|----------|----------|
| Use Services | For execution |
| Centralize Formats | In services |
| Logging | In methods |
| Type/Validate | Inputs |
| MVP | UI presentation only |
| Standardize Errors | Consistent patterns |
| Document Contracts | Inputs/outputs/effects |