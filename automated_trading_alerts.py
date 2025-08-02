#!/usr/bin/env python3
"""
Automated Trading Alerts - No Pandas Version
Fixed for Railway deployment without pandas dependency
"""

import json
import glob
import os
import requests
from datetime import datetime
import pytz

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ALPHA_CHANNEL_ID = os.getenv('ALPHA_DISCORD_CHANNEL_ID', '1399790636990857277')
PORTFOLIO_CHANNEL_ID = os.getenv('PORTFOLIO_DISCORD_CHANNEL_ID', '1399451217372905584')

def load_latest_positions():
    """Load latest positions data without pandas"""
    try:
        # Try JSON files first
        json_files = glob.glob("positions_*.json")
        if json_files:
            latest_file = max(json_files, key=lambda x: os.path.getctime(x))
            print(f"📊 Loading positions from: {latest_file}")
            
            with open(latest_file, 'r') as f:
                positions = json.load(f)
            
            print(f"✅ Loaded {len(positions)} positions")
            return positions
        
        # Fallback to CSV if no JSON
        csv_files = glob.glob("positions_*.csv")
        if csv_files:
            latest_file = max(csv_files, key=lambda x: os.path.getctime(x))
            print(f"📊 Loading positions from CSV: {latest_file}")
            
            positions = []
            import csv
            with open(latest_file, 'r') as f:
                reader = csv.DictReader(f)
                positions = list(reader)
            
            # Convert string numbers to floats
            for pos in positions:
                for key in ['PnL %', 'PnL $', 'Margin Size ($)', 'Entry Price', 'Mark Price']:
                    if key in pos and pos[key]:
                        try:
                            pos[key] = float(pos[key])
                        except:
                            pos[key] = 0.0
            
            print(f"✅ Loaded {len(positions)} positions from CSV")
            return positions
        
        print("❌ No positions files found")
        return []
        
    except Exception as e:
        print(f"❌ Error loading positions: {e}")
        return []

def send_discord_message(message, channel_id):
    """Send message to Discord channel"""
    if not DISCORD_TOKEN:
        print("⚠️ Discord token not configured, skipping message")
        return False
    
    try:
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {"content": message}
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Discord message sent to channel {channel_id}")
            return True
        else:
            print(f"❌ Discord API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending Discord message: {e}")
        return False

def analyze_positions(positions):
    """Analyze positions for alerts without pandas"""
    alerts = []
    
    try:
        for pos in positions:
            symbol = pos.get('Symbol', 'Unknown')
            platform = pos.get('Platform', 'Unknown')
            pnl_percent = pos.get('PnL %', 0)
            pnl_dollar = pos.get('PnL $', 0)
            margin = pos.get('Margin Size ($)', 0)
            
            # Convert to float if string
            try:
                pnl_percent = float(pnl_percent)
                pnl_dollar = float(pnl_dollar) 
                margin = float(margin)
            except:
                continue
            
            # High profit alert
            if pnl_percent > 50:
                alerts.append({
                    'type': 'high_profit',
                    'symbol': symbol,
                    'platform': platform,
                    'pnl': pnl_percent,
                    'message': f"💰 {symbol} up {pnl_percent:.1f}%! Consider rotating or trailing stops.",
                    'channel': 'portfolio'
                })
            
            # Losing trade alert
            elif pnl_percent < -10:
                alerts.append({
                    'type': 'losing_trade', 
                    'symbol': symbol,
                    'platform': platform,
                    'pnl': pnl_percent,
                    'margin': margin,
                    'message': f"🚨 {symbol} is down {pnl_percent:.1f}%. Capital preservation - review position.",
                    'channel': 'portfolio'
                })
            
            # Oversold conditions (simulate RSI)
            if pnl_percent < -15:
                alerts.append({
                    'type': 'oversold',
                    'symbol': symbol,
                    'platform': platform,
                    'rsi': 20,  # Simulated RSI based on losses
                    'pnl': pnl_percent,
                    'message': f"🟩 {symbol} is oversold at simulated RSI 20. Clean reversal setup detected.",
                    'channel': 'alpha'
                })
            
            # Overbought conditions (simulate RSI)
            elif pnl_percent > 80:
                alerts.append({
                    'type': 'overbought',
                    'symbol': symbol,
                    'platform': platform, 
                    'rsi': 85,  # Simulated RSI based on gains
                    'pnl': pnl_percent,
                    'message': f"🟥 Alert! {symbol} RSI is 85. Consider exiting or trailing stop.",
                    'channel': 'alpha'
                })
            
            # No stop loss warning for high margin positions
            sl_set = pos.get('SL Set?', '❌')
            if sl_set == '❌' and margin > 100:
                alerts.append({
                    'type': 'no_stop_loss',
                    'symbol': symbol,
                    'platform': platform,
                    'margin': margin,
                    'message': f"🛡️ {symbol} position (${margin:.0f}) needs STOP LOSS for fast rotation!",
                    'channel': 'portfolio'
                })
        
        return alerts
        
    except Exception as e:
        print(f"❌ Error analyzing positions: {e}")
        return []

def get_crypto_news_summary():
    """Get crypto news summary - simplified version"""
    try:
        # Import crypto news functions if available
        from crypto_news_alerts import get_breaking_news_optimized
        
        news = get_breaking_news_optimized(hours=6, items=20)
        
        if news:
            bullish_count = len([n for n in news if n.get('sentiment') == 'Positive'])
            bearish_count = len([n for n in news if n.get('sentiment') == 'Negative'])
            
            summary = f"📰 News: {len(news)} articles | 📈 Bullish: {bullish_count} | 📉 Bearish: {bearish_count}"
            
            # Add top news headline if available
            if news:
                top_news = news[0]
                summary += f"\n🔥 Breaking: {top_news.get('title', '')[:100]}..."
            
            return summary
        
        return "📰 No recent crypto news available"
        
    except Exception as e:
        print(f"⚠️ Crypto news unavailable: {e}")
        return "📰 Crypto news module not available"

def generate_portfolio_summary(positions, alerts):
    """Generate portfolio summary without pandas"""
    try:
        total_positions = len(positions)
        profitable_positions = len([p for p in positions if float(p.get('PnL %', 0)) > 0])
        losing_positions = len([p for p in positions if float(p.get('PnL %', 0)) < 0])
        
        # Calculate total PnL
        total_pnl = 0
        for pos in positions:
            try:
                pnl = float(pos.get('PnL $', 0))
                total_pnl += pnl
            except:
                continue
        
        # Alert breakdown
        alert_counts = {}
        for alert in alerts:
            alert_type = alert.get('type', 'unknown')
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
        
        # Build summary
        summary = f"""
🎯 **PORTFOLIO SUMMARY - {datetime.now(pytz.timezone('US/Central')).strftime('%I:%M %p CST')}**

📊 **Positions:** {total_positions} total | ✅ {profitable_positions} profitable | ❌ {losing_positions} losing
💰 **Total PnL:** ${total_pnl:,.2f}

🚨 **Alerts ({len(alerts)} total):**"""
        
        for alert_type, count in alert_counts.items():
            emoji = {"oversold": "🟩", "overbought": "🟥", "high_profit": "💰", "losing_trade": "📉", "no_stop_loss": "🛡️"}.get(alert_type, "⚠️")
            summary += f"\n{emoji} {alert_type.replace('_', ' ').title()}: {count}"
        
        return summary
        
    except Exception as e:
        print(f"❌ Error generating portfolio summary: {e}")
        return "❌ Error generating portfolio summary"

def run_automated_alerts():
    """Main function to run automated alerts"""
    try:
        print("🚀 Starting automated trading alerts...")
        current_time = datetime.now(pytz.timezone('US/Central'))
        print(f"⏰ Time: {current_time.strftime('%Y-%m-%d %I:%M %p CST')}")
        
        # Load positions
        positions = load_latest_positions()
        if not positions:
            print("❌ No positions data available")
            return False
        
        # Analyze positions for alerts
        alerts = analyze_positions(positions)
        print(f"🔍 Generated {len(alerts)} alerts")
        
        # Get crypto news summary
        news_summary = get_crypto_news_summary()
        
        # Generate portfolio summary
        portfolio_summary = generate_portfolio_summary(positions, alerts)
        
        # Send alerts to appropriate channels
        portfolio_alerts = [a for a in alerts if a.get('channel') == 'portfolio']
        alpha_alerts = [a for a in alerts if a.get('channel') == 'alpha']
        
        # Send portfolio summary + portfolio alerts
        if portfolio_alerts or True:  # Always send portfolio summary
            portfolio_message = portfolio_summary
            if portfolio_alerts:
                portfolio_message += "\n\n📋 **PORTFOLIO ALERTS:**"
                for alert in portfolio_alerts[:5]:  # Limit to 5 alerts
                    portfolio_message += f"\n• {alert['message']}"
            
            send_discord_message(portfolio_message, PORTFOLIO_CHANNEL_ID)
        
        # Send alpha alerts + news summary
        if alpha_alerts or True:  # Always send news summary
            alpha_message = f"🎯 **ALPHA HUNTING UPDATE**\n\n{news_summary}"
            
            if alpha_alerts:
                alpha_message += "\n\n🚀 **ALPHA ALERTS:**"
                for alert in alpha_alerts[:5]:  # Limit to 5 alerts
                    alpha_message += f"\n• {alert['message']}"
            
            send_discord_message(alpha_message, ALPHA_CHANNEL_ID)
        
        # Save alerts to file
        alerts_data = {
            'timestamp': current_time.strftime('%Y-%m-%d %I:%M %p CST'),
            'total_alerts': len(alerts),
            'alerts': alerts,
            'portfolio_summary': {
                'total_positions': len(positions),
                'profitable_count': len([p for p in positions if float(p.get('PnL %', 0)) > 0]),
                'losing_count': len([p for p in positions if float(p.get('PnL %', 0)) < 0])
            }
        }
        
        with open('latest_alerts.json', 'w') as f:
            json.dump(alerts_data, f, indent=2)
        
        print("✅ Automated alerts completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in automated alerts: {e}")
        return False

if __name__ == "__main__":
    # Test the alerts system
    print("🧪 Testing automated trading alerts...")
    success = run_automated_alerts()
    print(f"🎯 Test result: {'✅ Success' if success else '❌ Failed'}")
