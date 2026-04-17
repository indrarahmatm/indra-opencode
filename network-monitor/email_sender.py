import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def create_email_body(check_results: Dict[str, Any]) -> str:
    """
    Create HTML email body from network check results
    
    Args:
        check_results: Dictionary from network_checker.run_all_checks()
        
    Returns:
        HTML formatted email body
    """
    status = check_results["overall_status"]
    timestamp = check_results["timestamp"]
    results = check_results["results"]
    
    # Status color mapping
    status_colors = {
        "Stable": "#28a745",      # Green
        "Unstable": "#ffc107",    # Yellow
        "Critical": "#dc3545",    # Red
        "Unknown": "#6c757d"      # Gray
    }
    
    status_color = status_colors.get(status, "#6c757d")
    
    # Start HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: {status_color}; color: white; padding: 15px; border-radius: 5px; }}
            .content {{ margin-top: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 15px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .stable {{ background-color: #d4edda; }}
            .unstable {{ background-color: #fff3cd; }}
            .critical {{ background-color: #f8d7da; }}
            .summary {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-top: 20px; }}
            .footer {{ margin-top: 30px; font-size: 0.9em; color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Network Stability Report</h2>
            <p><strong>Status:</strong> {status}</p>
            <p><strong>Time:</strong> {timestamp}</p>
        </div>
        
        <div class="content">
            <h3>Ping Results</h3>
            <table>
                <thead>
                    <tr>
                        <th>Target</th>
                        <th>Min Latency (ms)</th>
                        <th>Avg Latency (ms)</th>
                        <th>Max Latency (ms)</th>
                        <th>Packet Loss (%)</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add rows for each target
    for result in results:
        target = result["target"]
        min_ms = result["min_ms"]
        avg_ms = result["avg_ms"]
        max_ms = result["max_ms"]
        packet_loss = result["packet_loss_pct"]
        reachable = result["reachable"]
        
        # Determine row status
        if not reachable:
            row_class = "critical"
            row_status = "UNREACHABLE"
        elif packet_loss >= 5.0 or avg_ms >= 200.0:
            row_class = "critical"
            row_status = "CRITICAL"
        elif packet_loss >= 1.0 or avg_ms >= 100.0:
            row_class = "unstable"
            row_status = "UNSTABLE"
        else:
            row_class = "stable"
            row_status = "STABLE"
            
        html += f"""
                    <tr class="{row_class}">
                        <td>{target}</td>
                        <td>{min_ms:.1f}</td>
                        <td>{avg_ms:.1f}</td>
                        <td>{max_ms:.1f}</td>
                        <td>{packet_loss:.1f}</td>
                        <td>{row_status}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
    """
    
    # Add summary
    html += f"""
            <div class="summary">
                <h3>Summary</h3>
                <p><strong>Overall Network Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status}</span></p>
                <p><strong>Targets Checked:</strong> {len(results)}</p>
                <p><strong>Check Completed:</strong> {timestamp}</p>
            </div>
    """
    
    # Add recommendations based on status
    if status == "Stable":
        rec = "Network performance is within normal parameters. No action required."
    elif status == "Unstable":
        rec = "Network shows minor issues. Consider monitoring closely. Check for temporary congestion or interference."
    else:  # Critical
        rec = "Network has significant issues requiring attention. Check physical connections, router status, and contact ISP if problems persist."
        
    html += f"""
            <div class="summary">
                <h3>Recommendation</h3>
                <p>{rec}</p>
            </div>
    """
    
    # Close HTML
    html += """
        <div class="footer">
            <p>This is an automated message from Network Stability Monitor.</p>
            <p>© 2026 Network Monitoring System</p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(check_results: Dict[str, Any], 
               sender_email: str, 
               sender_password: str, 
               receiver_email: str,
               smtp_host: str = "smtp.gmail.com", 
               smtp_port: int = 587) -> bool:
    """
    Send email with network check results
    
    Args:
        check_results: Dictionary from network_checker.run_all_checks()
        sender_email: Email address to send from
        sender_password: Password or app password for sender
        receiver_email: Email address to send to
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[Network Monitor] Status: {check_results['overall_status']} - {check_results['timestamp']}"
        msg['From'] = sender_email
        msg['To'] = receiver_email
        
        # Create HTML body
        html_body = create_email_body(check_results)
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Create secure connection and send email
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            
        logger.info(f"Email sent successfully to {receiver_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

if __name__ == "__main__":
    # Test the module (requires config)
    import config
    
    # Create dummy results for testing
    dummy_results = {
        "timestamp": "2026-04-06 08:00:00",
        "overall_status": "Stable",
        "results": [
            {
                "target": "8.8.8.8",
                "min_ms": 10.5,
                "avg_ms": 12.3,
                "max_ms": 15.7,
                "packet_loss_pct": 0.0,
                "reachable": True
            },
            {
                "target": "1.1.1.1",
                "min_ms": 11.2,
                "avg_ms": 13.1,
                "max_ms": 16.8,
                "packet_loss_pct": 0.0,
                "reachable": True
            }
        ]
    }
    
    # Test email body creation
    body = create_email_body(dummy_results)
    print("Email body created successfully")
    print(f"Body length: {len(body)} characters")
    
    # Note: Actual email sending requires valid credentials
    print("To test email sending, run with actual credentials from config")
