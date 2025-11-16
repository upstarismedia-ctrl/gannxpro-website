<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Signal</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background-color: #f5f5f5;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 30px;
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #2c3e50;
            font-weight: 600;
        }
        
        .signal-card {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
            background-color: #f9f9f9;
        }
        
        .signal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .symbol {
            font-size: 1.4rem;
            font-weight: bold;
        }
        
        .action {
            padding: 5px 12px;
            border-radius: 4px;
            font-weight: bold;
            color: white;
        }
        
        .buy {
            background-color: #27ae60;
        }
        
        .sell {
            background-color: #e74c3c;
        }
        
        .hold {
            background-color: #f39c12;
        }
        
        .signal-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .detail-item {
            margin-bottom: 10px;
        }
        
        .label {
            font-weight: 600;
            color: #7f8c8d;
            margin-bottom: 5px;
        }
        
        .value {
            font-size: 1.1rem;
        }
        
        .timestamp {
            text-align: right;
            color: #95a5a6;
            font-size: 0.9rem;
            margin-top: 10px;
        }
        
        .no-signals {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
            font-style: italic;
        }
        
        @media (max-width: 600px) {
            .signal-details {
                grid-template-columns: 1fr;
            }
            
            .signal-header {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .action {
                margin-top: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Trading Signals</h1>
        
        <div class="signal-card">
            <div class="signal-header">
                <div class="symbol">EUR/USD</div>
                <div class="action buy">BUY</div>
            </div>
            <div class="signal-details">
                <div class="detail-item">
                    <div class="label">Entry Price</div>
                    <div class="value">1.0850</div>
                </div>
                <div class="detail-item">
                    <div class="label">Stop Loss</div>
                    <div class="value">1.0800</div>
                </div>
                <div class="detail-item">
                    <div class="label">Take Profit 1</div>
                    <div class="value">1.0900</div>
                </div>
                <div class="detail-item">
                    <div class="label">Take Profit 2</div>
                    <div class="value">1.0950</div>
                </div>
            </div>
            <div class="timestamp">Generated: 2023-10-15 14:30 UTC</div>
        </div>
        
        <div class="signal-card">
            <div class="signal-header">
                <div class="symbol">GBP/JPY</div>
                <div class="action sell">SELL</div>
            </div>
            <div class="signal-details">
                <div class="detail-item">
                    <div class="label">Entry Price</div>
                    <div class="value">183.50</div>
                </div>
                <div class="detail-item">
                    <div class="label">Stop Loss</div>
                    <div class="value">184.20</div>
                </div>
                <div class="detail-item">
                    <div class="label">Take Profit 1</div>
                    <div class="value">182.50</div>
                </div>
                <div class="detail-item">
                    <div class="label">Take Profit 2</div>
                    <div class="value">181.80</div>
                </div>
            </div>
            <div class="timestamp">Generated: 2023-10-15 13:45 UTC</div>
        </div>
        
        <div class="signal-card">
            <div class="signal-header">
                <div class="symbol">USD/CAD</div>
                <div class="action hold">HOLD</div>
            </div>
            <div class="signal-details">
                <div class="detail-item">
                    <div class="label">Current Price</div>
                    <div class="value">1.3650</div>
                </div>
                <div class="detail-item">
                    <div class="label">Next Update</div>
                    <div class="value">2 hours</div>
                </div>
                <div class="detail-item">
                    <div class="label">Reason</div>
                    <div class="value">Waiting for breakout</div>
                </div>
            </div>
            <div class="timestamp">Generated: 2023-10-15 12:15 UTC</div>
        </div>
    </div>
</body>
</html>
