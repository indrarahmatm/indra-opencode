# Network Stability Monitor

An automated Python application that checks network stability (ping + packet loss) and sends email reports via Gmail SMTP every day at 08:00 AM.

## Features

- **Network Monitoring**: Pings multiple targets (8.8.8.8, 1.1.1.1, google.com) to measure latency and packet loss
- **Status Classification**: 
  - **Stable**: 0% packet loss & <100ms latency
  - **Unstable**: 1-5% packet loss OR 100-200ms latency  
  - **Critical**: >5% packet loss OR >200ms latency OR unreachable
- **Email Reports**: HTML formatted reports sent via Gmail SMTP
- **Scheduler**: Automated daily execution at 08:00 AM
- **Logging**: Detailed logs to console and file

## Prerequisites

- Python 3.6+
- Gmail account with App Password (for sending emails)
- Internet connectivity (obviously!)

## Installation

1. Clone or copy this repository to your local machine
2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

## Configuration

Edit `config.py` with your email settings:

```python
EMAIL_SENDER = "your_email@gmail.com"           # Your Gmail address
EMAIL_PASSWORD = "your_app_password"            # Gmail App Password (NOT regular password)
EMAIL_RECEIVER = "indra_rahmat@psp.co.id"       # Recipient email
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

PING_TARGETS = ["8.8.8.8", "1.1.1.1", "google.com"]  # Targets to ping
PING_COUNT = 10                                   # Number of ping packets per target
SCHEDULE_TIME = "08:00"                           # Time to run daily (24h format)
LOG_FILE = "network_monitor.log"                  # Log file path
```

### Getting Gmail App Password

1. Enable 2-Factor Authentication on your Google Account
2. Go to: Google Account → Security → App Passwords
3. Select app: "Mail", device: "Other" (name it e.g., "Network Monitor")
4. Copy the 16-character password and use it as `EMAIL_PASSWORD`

## Usage

### Run as Daemon (Recommended for Production)

```bash
python3 main.py
```
This will start the scheduler and wait until 08:00 AM each day to run the network check and send email.

### Run Once Immediately (For Testing)

```bash
python3 main.py --run-now
```
This will run the network check once and send an email immediately.

### Test Email Functionality

```bash
python3 main.py --test-email
```
This sends a test email with dummy data to verify your email configuration works.

## Sample Email Report

The email includes:
- Overall network status (Stable/Unstable/Critical)
- Table showing ping results for each target (latency min/avg/max, packet loss)
- Summary and recommendations based on the status
- Professional HTML formatting with color-coding

## Logs

Activity is logged to:
- Console (stdout)
- File: `network_monitor.log` (in the same directory)

Logs include:
- Network check results
- Email sending status
- Errors and warnings
- Scheduler activity

## Customization

### Changing Check Frequency
To check more than once daily, modify `main.py`:
```python
# Instead of: schedule.every().day.at(config.SCHEDULE_TIME).do(job)
# For every 4 hours: schedule.every(4).hours.do(job)
# For every hour: schedule.every().hour.do(job)
```

### Adding/Removing Ping Targets
Edit `config.py`:
```python
PING_TARGETS = ["8.8.8.8", "1.1.1.1", "google.com", "your-custom-target.com"]
```

### Adjusting Thresholds
Edit `network_checker.py` in the `determine_overall_status()` function to change what constitutes Stable/Unstable/Critical.

## How It Works

1. At scheduled time (08:00), the application:
   - Pings each target 10 times
   - Parses results for latency (min/avg/max) and packet loss percentage
   - Determines overall network status
   - Formats results into an HTML email
   - Sends email via Gmail SMTP with TLS encryption
   - Logs all activity

2. The scheduler runs continuously, checking every minute if it's time to execute the job.

## Troubleshooting

### Common Issues

**"Authentication failed" when sending email**
- Make sure you're using an App Password, not your regular Gmail password
- Verify 2-Factor Authentication is enabled on your Google Account
- Check that the App Password was created for "Mail" service

"No module named 'schedule'"
- Run: `pip3 install -r requirements.txt`

"Permission denied" when writing log file
- Make sure you have write permissions to the directory
- Or change LOG_FILE in config.py to a path you can write to

Ping shows 100% loss but you know network is fine
- Some networks block ICMP (ping) packets
- Try changing PING_TARGETS to hosts that allow pinging
- Or reduce PING_COUNT if experiencing rate limiting

### Getting Help

Check the log file (`network_monitor.log`) for detailed error messages.
Make sure your system time is correct for the scheduler to work properly.
