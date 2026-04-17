import subprocess
import re
import time
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def check_ping(target: str, count: int = 10) -> Dict[str, Any]:
    """
    Ping a target and parse the results
    
    Args:
        target: Hostname or IP to ping
        count: Number of ping packets to send
        
    Returns:
        Dictionary with ping results
    """
    try:
        # Run ping command
        cmd = ["ping", "-c", str(count), target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        output = result.stdout
        
        # Parse packet loss
        packet_loss_match = re.search(r'(\d+)% packet loss', output)
        packet_loss_pct = float(packet_loss_match.group(1)) if packet_loss_match else 100.0
        
        # Parse latency stats (min/avg/max/mdev)
        latency_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms', output)
        
        if latency_match:
            min_ms = float(latency_match.group(1))
            avg_ms = float(latency_match.group(2))
            max_ms = float(latency_match.group(3))
            # mdev = float(latency_match.group(4))  # Not used for now
        else:
            min_ms = avg_ms = max_ms = 0.0
            
        reachable = packet_loss_pct < 100.0  # Consider reachable if we got any replies
        
        return {
            "target": target,
            "min_ms": min_ms,
            "avg_ms": avg_ms,
            "max_ms": max_ms,
            "packet_loss_pct": packet_loss_pct,
            "reachable": reachable,
            "raw_output": output[:200] + "..." if len(output) > 200 else output  # For debugging
        }
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Ping to {target} timed out")
        return {
            "target": target,
            "min_ms": 0.0,
            "avg_ms": 0.0,
            "max_ms": 0.0,
            "packet_loss_pct": 100.0,
            "reachable": False,
            "error": "timeout"
        }
    except Exception as e:
        logger.error(f"Error pinging {target}: {e}")
        return {
            "target": target,
            "min_ms": 0.0,
            "avg_ms": 0.0,
            "max_ms": 0.0,
            "packet_loss_pct": 100.0,
            "reachable": False,
            "error": str(e)
        }

def run_all_checks(targets: List[str] = None, count: int = 10) -> Dict[str, Any]:
    """
    Run ping checks on all targets
    
    Args:
        targets: List of targets to ping (defaults to common DNS/hosts)
        count: Number of ping packets per target
        
    Returns:
        Dictionary with all results and overall status
    """
    if targets is None:
        targets = ["8.8.8.8", "1.1.1.1", "google.com"]
        
    logger.info(f"Starting network check for {len(targets)} targets: {targets}")
    
    results = []
    for target in targets:
        logger.debug(f"Pinging {target}...")
        result = check_ping(target, count)
        results.append(result)
        logger.debug(f"Result for {target}: {result['avg_ms']:.1f}ms avg, {result['packet_loss_pct']}% loss")
    
    # Determine overall status
    overall_status = determine_overall_status(results)
    
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": results,
        "overall_status": overall_status,
        "targets_checked": len(targets)
    }

def determine_overall_status(results: List[Dict[str, Any]]) -> str:
    """
    Determine overall network status based on individual results
    
    Args:
        results: List of ping result dictionaries
        
    Returns:
        Overall status: "Stable", "Unstable", or "Critical"
    """
    if not results:
        return "Unknown"
        
    # Check for any critical issues
    critical_conditions = []
    unstable_conditions = []
    
    for result in results:
        if not result["reachable"]:
            critical_conditions.append(f"{result['target']} unreachable")
        elif result["packet_loss_pct"] >= 5.0:  # Critical packet loss
            critical_conditions.append(f"{result['target']} packet loss {result['packet_loss_pct']}%")
        elif result["avg_ms"] >= 200.0:  # Critical latency
            critical_conditions.append(f"{result['target']} latency {result['avg_ms']:.1f}ms")
        elif result["packet_loss_pct"] >= 1.0:  # Unstable packet loss
            unstable_conditions.append(f"{result['target']} packet loss {result['packet_loss_pct']}%")
        elif result["avg_ms"] >= 100.0:  # Unstable latency
            unstable_conditions.append(f"{result['target']} latency {result['avg_ms']:.1f}ms")
    
    if critical_conditions:
        return "Critical"
    elif unstable_conditions:
        return "Unstable"
    else:
        return "Stable"

if __name__ == "__main__":
    # Test the module
    logging.basicConfig(level=logging.INFO)
    results = run_all_checks()
    print(f"Overall Status: {results['overall_status']}")
    for r in results['results']:
        print(f"{r['target']}: {r['avg_ms']:.1f}ms avg, {r['packet_loss_pct']}% loss")
