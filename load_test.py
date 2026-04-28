#!/usr/bin/env python3
"""
EntokMart Load Test - Simulate 1000 concurrent users
Using concurrent.futures instead of aiohttp
"""

import urllib.request
import urllib.error
import threading
import time
import sys
from collections import defaultdict
import json

BASE_URL = "http://127.0.0.1:5003"

results = {
    'success': 0,
    'errors': 0,
    'response_times': [],
    'status_codes': defaultdict(int),
    'errors_detail': [],
}
results_lock = threading.Lock()

def make_request(url):
    """Make a single HTTP request"""
    start_time = time.time()
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'LoadTest/1.0')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.status
            response.read()
            elapsed = time.time() - start_time
            
            with results_lock:
                results['status_codes'][status] += 1
                results['response_times'].append(elapsed)
                
                if status < 400:
                    results['success'] += 1
                else:
                    results['errors'] += 1
                    results['errors_detail'].append(f"{status} - {url}")
                    
    except urllib.error.HTTPError as e:
        with results_lock:
            results['errors'] += 1
            results['status_codes'][e.code] += 1
            results['errors_detail'].append(f"HTTP {e.code} - {url}")
    except Exception as e:
        with results_lock:
            results['errors'] += 1
            results['errors_detail'].append(f"ERROR - {url}: {str(e)[:50]}")

def run_load_test(num_users=1000):
    """Run load test simulating N concurrent users"""
    
    print(f"\n🚀 Starting load test: {num_users} concurrent requests")
    print("=" * 60)
    
    # Define endpoints to test
    endpoints = [
        f"{BASE_URL}/",
        f"{BASE_URL}/api/v1/products",
        f"{BASE_URL}/api/v1/categories",
        f"{BASE_URL}/api/v1/sellers",
        f"{BASE_URL}/api/v1/zones",
    ]
    
    # Create threads
    threads = []
    requests_per_endpoint = num_users // len(endpoints)
    
    print(f"📊 Total requests: {num_users}")
    print(f"📍 Endpoints: {len(endpoints)}")
    print(f"   Requests per endpoint: {requests_per_endpoint}")
    
    start_time = time.time()
    
    # Create all threads
    for url in endpoints:
        for _ in range(requests_per_endpoint):
            t = threading.Thread(target=make_request, args=(url,))
            threads.append(t)
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for all to complete
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    
    # Print results
    print_results(num_users, total_time)

def print_results(num_requests, total_time):
    """Print test results"""
    
    print("\n" + "=" * 60)
    print("📈 LOAD TEST RESULTS")
    print("=" * 60)
    
    total_req = results['success'] + results['errors']
    
    print(f"\n📊 Summary:")
    print(f"   Total Requests:  {total_req}")
    print(f"   Successful:     {results['success']} ({results['success']/total_req*100:.1f}%)")
    print(f"   Failed:         {results['errors']} ({results['errors']/total_req*100:.1f}%)")
    print(f"   Total Time:     {total_time:.2f}s")
    print(f"   RPS:            {total_req/total_time:.1f} requests/sec")
    
    # Response time stats
    if results['response_times']:
        times = sorted(results['response_times'])
        avg_time = sum(times) / len(times)
        p50 = times[len(times)//2]
        p95 = times[int(len(times)*0.95)]
        p99 = times[int(len(times)*0.99)]
        
        print(f"\n⏱️ Response Time:")
        print(f"   Average: {avg_time*1000:.0f}ms")
        print(f"   P50:     {p50*1000:.0f}ms")
        print(f"   P95:     {p95*1000:.0f}ms")
        print(f"   P99:     {p99*1000:.0f}ms")
        print(f"   Min:     {min(times)*1000:.0f}ms")
        print(f"   Max:     {max(times)*1000:.0f}ms")
    
    # Status codes
    print(f"\n📊 HTTP Status Codes:")
    for status, count in sorted(results['status_codes'].items()):
        print(f"   {status}: {count}")
    
    # Errors
    if results['errors_detail']:
        print(f"\n⚠️ Errors ({len(results['errors_detail'])} total):")
        error_counts = defaultdict(int)
        for err in results['errors_detail'][:10]:
            error_counts[err] += 1
        for err, count in error_counts.items():
            print(f"   {count}x {err}")
    
    # Evaluation
    print(f"\n🎯 Evaluation:")
    success_rate = results['success'] / total_req * 100
    if success_rate >= 99:
        print(f"   ✅ EXCELLENT - {success_rate:.1f}% success rate")
    elif success_rate >= 95:
        print(f"   ✅ GOOD - {success_rate:.1f}% success rate")
    elif success_rate >= 90:
        print(f"   ⚠️ FAIR - {success_rate:.1f}% success rate")
    else:
        print(f"   ❌ POOR - {success_rate:.1f}% success rate")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    run_load_test(num)