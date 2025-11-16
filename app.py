<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gann Analysis Trading Signal</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #1a2a3a, #0d1b2a);
            color: #e0e1dd;
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            max-width: 900px;
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .header {
            background: rgba(0, 0, 0, 0.3);
            padding: 20px 30px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .signal-title {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }
        
        .signal-title h1 {
            font-size: 1.8rem;
            font-weight: 600;
            color: #ffb74d;
        }
        
        .signal-badge {
            background: #ff9800;
            color: #1a2a3a;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .signal-subtitle {
            color: #90caf9;
            font-size: 1.1rem;
            margin-bottom: 5px;
        }
        
        .content {
            padding: 30px;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section-title {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .section-title h2 {
            font-size: 1.4rem;
            color: #4fc3f7;
        }
        
        .section-title i {
            color: #4fc3f7;
        }
        
        .description-box {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #4fc3f7;
        }
        
        .description-box p {
            line-height: 1.6;
            margin-bottom: 10px;
        }
        
        .highlight {
            color: #ffb74d;
            font-weight: 600;
        }
        
        .cycles-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .cycle-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 20px;
            transition: transform 0.3s ease, background 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .cycle-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.08);
        }
        
        .cycle-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .cycle-name {
            font-size: 1.1rem;
            font-weight: 600;
            color: #4fc3f7;
        }
        
        .cycle-date {
            background: rgba(255, 255, 255, 0.1);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.85rem;
        }
        
        .cycle-details {
            margin-bottom: 15px;
        }
        
        .cycle-detail {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .detail-label {
            color: #b0bec5;
        }
        
        .detail-value {
            font-weight: 600;
        }
        
        .cycle-forecast {
            background: rgba(255, 255, 255, 0.05);
            padding: 12px;
            border-radius: 8px;
            font-size: 0.9rem;
            line-height: 1.5;
            border-left: 3px solid #4caf50;
        }
        
        .prediction-high {
            color: #4caf50;
        }
        
        .prediction-low {
            color: #f44336;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 0.9rem;
            color: #b0bec5;
        }
        
        .ai-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(33, 150, 243, 0.2);
            padding: 6px 12px;
            border-radius: 20px;
            margin-top: 10px;
            font-size: 0.85rem;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
            }
            
            .content {
                padding: 20px;
            }
            
            .cycles-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="signal-title">
                <h1>MILD BULLISH - Above Pivot</h1>
                <span class="signal-badge">LIVE</span>
            </div>
            <div class="signal-subtitle">Gann Analysis Trading Signal</div>
        </div>
        
        <div class="content">
            <div class="section">
                <div class="section-title">
                    <i class="fas fa-chart-line"></i>
                    <h2>Gann Analysis</h2>
                </div>
                
                <div class="description-box">
                    <p><span class="highlight">Description:</span> Technical analysis method using geometry and time cycles to predict market movements based on mathematical relationships between price and time.</p>
                    <p><span class="highlight">Interpretation:</span> Based on W.D. Gann theories of price and time relationships, focusing on support/resistance levels and cyclical patterns.</p>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">
                    <i class="fas fa-robot"></i>
                    <h2>AI-Predicted Upcoming Gann Cycles</h2>
                </div>
                
                <div class="cycles-container">
                    <div class="cycle-card">
                        <div class="cycle-header">
                            <div class="cycle-name">Primary Cycle</div>
                            <div class="cycle-date">Oct 20-25, 2023</div>
                        </div>
                        <div class="cycle-details">
                            <div class="cycle-detail">
                                <span class="detail-label">Strength:</span>
                                <span class="detail-value">High</span>
                            </div>
                            <div class="cycle-detail">
                                <span class="detail-label">Duration:</span>
                                <span class="detail-value">6 days</span>
                            </div>
                            <div class="cycle-detail">
                                <span class="detail-label">Impact:</span>
                                <span class="detail-value">Major</span>
                            </div>
                        </div>
                        <div class="cycle-forecast">
                            <span class="prediction-high">Bullish momentum</span> expected with potential breakout above resistance at 1.0950
                        </div>
                    </div>
                    
                    <div class="cycle-card">
                        <div class="cycle-header">
                            <div class="cycle-name">Secondary Cycle</div>
                            <div class="cycle-date">Nov 5-8, 2023</div>
                        </div>
                        <div class="cycle-details">
                            <div class="cycle-detail">
                                <span class="detail-label">Strength:</span>
                                <span class="detail-value">Medium</span>
                            </div>
                            <div class="cycle-detail">
                                <span class="detail-label">Duration:</span>
                                <span class="detail-value">4 days</span>
                            </div>
                            <div class="cycle-detail">
                                <span class="detail-label">Impact:</span>
                                <span class="detail-value">Moderate</span>
                            </div>
                        </div>
                        <div class="cycle-forecast">
                            Possible <span class="prediction-low">correction</span> to test support at 1.0820 before resuming upward trend
                        </div>
                    </div>
                    
                    <div class="cycle-card">
                        <div class="cycle-header">
                            <div class="cycle-name">Tertiary Cycle</div>
                            <div class="cycle-date">Nov 18-22, 2023</div>
                        </div>
                        <div class="cycle-details">
                            <div class="cycle-detail">
                                <span class="detail-label">Strength:</span>
                                <span class="detail-value">Low</span>
                            </div>
                            <div class="cycle-detail">
                                <span class="detail-label">Duration:</span>
                                <span class="detail-value">5 days</span>
                            </div>
                            <div class="cycle-detail">
                                <span class="detail-label">Impact:</span>
                                <span class="detail-value">Minor</span>
                            </div>
                        </div>
                        <div class="cycle-forecast">
                            Sideways consolidation expected with <span class="prediction-high">bullish bias</span> maintaining above pivot
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Gann Analysis Trading Signal • Updated in Real-time</p>
            <div class="ai-badge">
                <i class="fas fa-brain"></i>
                <span>AI-Powered Gann Cycle Predictions</span>
            </div>
        </div>
    </div>

    <script>
        // Simple animation for cycle cards on load
        document.addEventListener('DOMContentLoaded', function() {
            const cycleCards = document.querySelectorAll('.cycle-card');
            
            cycleCards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 300 + (index * 200));
            });
            
            // Update current date in the primary cycle
            const currentDate = new Date();
            const futureDate1 = new Date(currentDate);
            futureDate1.setDate(currentDate.getDate() + 5);
            const futureDate2 = new Date(futureDate1);
            futureDate2.setDate(futureDate1.getDate() + 5);
            
            document.querySelector('.cycle-date').textContent = 
                `${futureDate1.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
        });
    </script>
</body>
</html>
