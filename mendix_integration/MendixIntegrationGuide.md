# Mendix Integration Guide for Trading Bot

This guide explains how to connect your Mendix application to the Python Trading Bot API.

## Step 1: Set up the API
Ensure the Python API is running:
```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

## Step 2: Import the OpenAPI Specification
1. In Mendix Studio Pro, right-click on your module and select **Add other > App service / REST service > Consumed REST service**.
2. Name it `TradingBotAPI`.
3. In the "General" tab, click "Import from file" and select `mendix_integration/openapi.json`.
4. Mendix will automatically create the operations for `GET /status`, `POST /start`, `GET /positions`, etc.

## Step 3: Create a Dashboard Page
1. Create a Data View that calls a Microflow.
2. The Microflow should:
    - Call the REST service `GET /status`.
    - Map the response to a `BotStatus` entity.
    - Return the `BotStatus` object.
3. Add a Template Grid or List View for `Positions`:
    - Data source: Microflow calling `GET /positions`.
    - Map to `Position` entities.

## Step 4: Add Controls
1. **Start/Stop Buttons**: Call Microflows that trigger `POST /start` and `POST /stop`.
2. **Strategy Toggle**: In a list of strategies, add a switch widget. On change, call a Microflow that triggers `POST /strategies/{name}/toggle?enabled={value}`.

## Step 5: Real-time Updates
Use the **Pusher** or **SignalR** connector if real-time updates are needed, or simply set the Refresh interval on your Mendix pages to 5-10 seconds to match the bot's loop.
