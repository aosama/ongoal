"""
Test Timing Utilities
Provides decorators and functions for tracking test execution time
"""

import time
import functools
from datetime import datetime
from pathlib import Path
import json


class TestTimingTracker:
    """Tracks test execution times and provides analysis"""
    
    def __init__(self):
        self.timing_file = Path(__file__).parent / "test_timings.json"
        self.load_historical_data()
    
    def load_historical_data(self):
        """Load historical timing data"""
        try:
            if self.timing_file.exists():
                with open(self.timing_file) as f:
                    self.historical_data = json.load(f)
            else:
                self.historical_data = {}
        except Exception:
            self.historical_data = {}
    
    def save_timing_data(self):
        """Save timing data to file"""
        try:
            with open(self.timing_file, 'w') as f:
                json.dump(self.historical_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save timing data: {e}")
    
    def record_test_time(self, test_name, duration, status="completed"):
        """Record a test execution time"""
        timestamp = datetime.now().isoformat()
        
        if test_name not in self.historical_data:
            self.historical_data[test_name] = []
        
        # Keep only last 10 runs for each test
        self.historical_data[test_name].append({
            "timestamp": timestamp,
            "duration": duration,
            "status": status
        })
        
        if len(self.historical_data[test_name]) > 10:
            self.historical_data[test_name] = self.historical_data[test_name][-10:]
        
        self.save_timing_data()
    
    def get_timing_analysis(self, test_name):
        """Get timing analysis for a test"""
        if test_name not in self.historical_data:
            return None
        
        runs = self.historical_data[test_name]
        durations = [run["duration"] for run in runs]
        
        if not durations:
            return None
        
        return {
            "avg": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
            "latest": durations[-1],
            "runs": len(durations),
            "trend": self._calculate_trend(durations)
        }
    
    def _calculate_trend(self, durations):
        """Calculate if test is getting slower/faster"""
        if len(durations) < 5:  # Need at least 5 data points for trend analysis
            return "stable"
        
        recent_avg = sum(durations[-3:]) / 3
        earlier_avg = sum(durations[:-3]) / len(durations[:-3])
        
        change = (recent_avg - earlier_avg) / earlier_avg
        
        if change > 0.2:
            return "slower"
        elif change < -0.2:
            return "faster"
        else:
            return "stable"


# Global timing tracker instance
timing_tracker = TestTimingTracker()


def time_test(category="general"):
    """Decorator to time test execution with category"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            test_name = f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            print(f"⏱️  Starting {category} test: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                status = "passed"
            except Exception as e:
                status = "failed"
                raise
            finally:
                duration = time.time() - start_time
                
                # Record timing
                timing_tracker.record_test_time(test_name, duration, status)
                
                # Get analysis
                analysis = timing_tracker.get_timing_analysis(test_name)
                
                # Print timing info
                print(f"⏱️  Completed {category} test: {func.__name__}")
                print(f"   Duration: {duration:.2f}s")
                
                if analysis:
                    print(f"   Average: {analysis['avg']:.2f}s, Trend: {analysis['trend']}")
                    if duration > analysis['avg'] * 1.5:
                        print(f"   ⚠️  SLOW: This run was 50% slower than average!")
                    elif duration < analysis['avg'] * 0.7:
                        print(f"   🚀 FAST: This run was 30% faster than average!")
            
            return result
        return wrapper
    return decorator


def time_browser_test(func):
    """Specialized timing decorator for browser tests"""
    return time_test("browser")(func)


def time_integration_test(func):
    """Specialized timing decorator for integration tests"""
    return time_test("integration")(func)


def time_unit_test(func):
    """Specialized timing decorator for unit tests"""
    return time_test("unit")(func)


def print_timing_summary():
    """Print a summary of all test timings"""
    print("\n" + "=" * 60)
    print("📊 TEST TIMING SUMMARY")
    print("=" * 60)
    
    for test_name, runs in timing_tracker.historical_data.items():
        if runs:
            latest = runs[-1]
            durations = [run["duration"] for run in runs]
            avg_duration = sum(durations) / len(durations)
            
            # Determine category from test name
            if "browser" in test_name:
                category = "🌐 Browser"
            elif "integration" in test_name:
                category = "🔗 Integration"
            elif "unit" in test_name:
                category = "⚡ Unit"
            else:
                category = "📝 General"
            
            trend_emoji = {
                "slower": "📈",
                "faster": "📉", 
                "stable": "➡️"
            }
            
            analysis = timing_tracker.get_timing_analysis(test_name)
            trend = trend_emoji.get(analysis["trend"], "➡️")
            
            print(f"{category} {test_name.split('.')[-1]}")
            print(f"   Latest: {latest['duration']:.2f}s | Avg: {avg_duration:.2f}s | {trend} {analysis['trend']}")
    
    print("=" * 60)


class TimingContext:
    """Context manager for timing code blocks"""
    
    def __init__(self, name, print_result=True):
        self.name = name
        self.print_result = print_result
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        if self.print_result:
            print(f"⏱️  Starting: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        if self.print_result:
            status = "completed" if exc_type is None else "failed"
            print(f"⏱️  {status.title()}: {self.name} in {self.duration:.2f}s")
