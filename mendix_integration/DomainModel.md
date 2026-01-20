# Mendix Domain Model Design

To integrate the Trading Bot with Mendix, you should create the following entities in your Mendix Domain Model.

## Entities

### BotStatus
- **IsRunning**: Boolean
- **LastRunTime**: DateTime
- **ActivePositionsCount**: Integer
- **DisabledStrategies**: String (Comma separated or use a associated Strategy entity)

### Position
- **StrategyName**: String
- **Symbol**: String
- **Direction**: String (CALL/PUT)
- **Quantity**: Integer
- **EntryPrice**: Decimal
- **SLPrice**: Decimal
- **TPPrice**: Decimal
- **OpenedAt**: DateTime
- **PnL**: Decimal

### Strategy
- **Name**: String
- **IsEnabled**: Boolean
- **HasActivePosition**: Boolean

### LogEntry
- **Message**: String (Unlimited length)

## Mappings

### Import Mappings
Use the provided `openapi.json` to generate Import Mappings for:
- `/status` -> BotStatus
- `/positions` -> List of Position
- `/strategies` -> List of Strategy
- `/logs` -> List of Strings (or LogEntry)

### Export Mappings
- To toggle strategies, use an Export Mapping for the `enabled` boolean parameter in the POST request.
