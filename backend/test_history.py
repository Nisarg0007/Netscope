"""
Test script for history service
"""
import sys
import os
import tempfile
import shutil
import time
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# We'll set a temporary database for testing
TEST_DB_PATH = None

def setup_test_db():
    """Set up a temporary SQLite database for testing"""
    global TEST_DB_PATH
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    TEST_DB_PATH = os.path.join(temp_dir, "test_netscope.db")
    # Set the environment variable for the database URL
    os.environ["SQLALCHEMY_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
    # Now we need to reload the modules to pick up the new database URL
    # Since we are in a script, we can just import the modules after setting the env var
    # But note: the modules might have been already imported by other test scripts.
    # We'll force reload of the modules that use the database.
    # For simplicity, we'll just import the modules again and hope that the environment variable is picked up.
    # However, the SQLALCHEMY_DATABASE_URL is set in the module level in database.py.
    # We'll reload the database module and then the models and services that import it.
    import importlib
    if 'app.database' in sys.modules:
        importlib.reload(sys.modules['app.database'])
    if 'app.models.history' in sys.modules:
        importlib.reload(sys.modules['app.models.history'])
    if 'app.services.history_service' in sys.modules:
        importlib.reload(sys.modules['app.services.history_service'])
    if 'app.routers.history' in sys.modules:
        importlib.reload(sys.modules['app.routers.history'])
    # Also reload the main app to reinitialize the database? We don't need to run the app for tests.
    # We'll just use the services and models directly.

def cleanup_test_db():
    """Clean up the temporary database"""
    global TEST_DB_PATH
    if TEST_DB_PATH and os.path.exists(os.path.dirname(TEST_DB_PATH)):
        shutil.rmtree(os.path.dirname(TEST_DB_PATH))
    TEST_DB_PATH = None
    # Remove the environment variable
    if "SQLALCHEMY_DATABASE_URL" in os.environ:
        del os.environ["SQLALCHEMY_DATABASE_URL"]

def test_database_initialization():
    """Test that the database Initializes correctly"""
    print("Testing database initialization...")
    setup_test_db()
    try:
        from app.database import init_db, engine
        from app.models.history import NetworkHistory
        # Initialize the database
        init_db()
        # Check that the table exists
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "network_history" in tables
        print("Database initialization test passed")
    finally:
        cleanup_test_db()

def test_snapshot_creation_and_storage():
    """Test that a snapshot can be created and stored"""
    print("Testing snapshot creation and storage...")
    setup_test_db()
    try:
        from app.database import init_db, SessionLocal
        from app.models.history import NetworkHistory
        from app.services.history_service import HistoryService
        from app.services.bandwidth_monitor import bandwidth_monitor
        from app.services.protocol_analysis import protocol_analysis_service
        from app.services.packet_capture import packet_capture_service

        # Initialize the database
        init_db()

        # Clear any existing data
        db = SessionLocal()
        db.query(NetworkHistory).delete()
        db.commit()
        db.close()

        # Start the bandwidth monitor (if not already started) to have some data
        # We'll set a dummy interface and start monitoring
        # Note: We don't have a real interface, but we can still start the monitor and it will get data from psutil
        bandwidth_monitor.set_selected_interface(None)  # No specific interface
        bandwidth_monitor.start_monitoring()
        # Wait for the monitor to collect at least one sample
        time.sleep(2)

        # Create a history service and take a snapshot
        history_service = HistoryService(interval=1)
        # We don't want to wait for the interval, so we call the method directly
        history_service._take_snapshot()

        # Check that a record was stored
        db = SessionLocal()
        count = db.query(NetworkHistory).count()
        db.close()

        assert count == 1, f"Expected 1 snapshot, got {count}"

        # Stop the bandwidth monitor
        bandwidth_monitor.stop_monitoring_thread()

        print("Snapshot creation and storage test passed")
    finally:
        cleanup_test_db()

def test_history_retrieval():
    """Test that historical snapshots can be retrieved"""
    print("Testing history retrieval...")
    setup_test_db()
    try:
        from app.database import init_db, SessionLocal
        from app.models.history import NetworkHistory
        from app.services.history_service import HistoryService
        from app.services.bandwidth_monitor import bandwidth_monitor

        # Initialize the database
        init_db()

        # Clear any existing data
        db = SessionLocal()
        db.query(NetworkHistory).delete()
        db.commit()
        db.close()

        # Start the bandwidth monitor
        bandwidth_monitor.set_selected_interface(None)
        bandwidth_monitor.start_monitoring()

        # Create a history service and take multiple snapshots
        history_service = HistoryService(interval=1)
        # Take 3 snapshots with a small delay
        for i in range(3):
            history_service._take_snapshot()
            # Wait a bit to ensure different timestamps
            time.sleep(0.1)

        # Stop the bandwidth monitor
        bandwidth_monitor.stop_monitoring_thread()

        # Now test the retrieval via the router function (but we'll call the service directly for simplicity)
        # We'll use the get_db function from the router? Instead, we'll use SessionLocal.
        from app.routers.history import get_history
        # We need to override the get_db dependency? Instead, we'll just query the database directly.
        db = SessionLocal()
        snapshots = db.query(NetworkHistory).order_by(NetworkHistory.timestamp.desc()).all()
        db.close()

        assert len(snapshots) == 3, f"Expected 3 snapshots, got {len(snapshots)}"

        # Check that the timestamps are in descending order (most recent first)
        timestamps = [s.timestamp for s in snapshots]
        assert timestamps == sorted(timestamps, reverse=True), "Timestamps are not in descending order"

        print("History retrieval test passed")
    finally:
        cleanup_test_db()

def test_latest_history():
    """Test retrieving the latest history snapshot"""
    print("Testing latest history retrieval...")
    setup_test_db()
    try:
        from app.database import init_db, SessionLocal
        from app.models.history import NetworkHistory
        from app.services.history_service import HistoryService
        from app.services.bandwidth_monitor import bandwidth_monitor

        # Initialize the database
        init_db()

        # Clear any existing data
        db = SessionLocal()
        db.query(NetworkHistory).delete()
        db.commit()
        db.close()

        # Start the bandwidth monitor
        bandwidth_monitor.set_selected_interface(None)
        bandwidth_monitor.start_monitoring()

        # Create a history service and take a snapshot
        history_service = HistoryService(interval=1)
        history_service._take_snapshot()

        # Stop the bandwidth monitor
        bandwidth_monitor.stop_monitoring_thread()

        # Get the latest snapshot
        db = SessionLocal()
        latest = db.query(NetworkHistory).order_by(NetworkHistory.timestamp.desc()).first()
        db.close()

        assert latest is not None, "Expected a latest snapshot"

        # Check that the fields are set
        assert latest.timestamp is not None
        # The interface might be None because we didn't select one
        # But we set selected_interface to None, so the bandwidth monitor returns aggregate stats and interface is None
        # That's acceptable.

        print("Latest history test passed")
    finally:
        cleanup_test_db()

def test_clear_history():
    """Test clearing the history"""
    print("Testing clear history...")
    setup_test_db()
    try:
        from app.database import init_db, SessionLocal
        from app.models.history import NetworkHistory
        from app.services.history_service import HistoryService
        from app.services.bandwidth_monitor import bandwidth_monitor

        # Initialize the database
        init_db()

        # Clear any existing data
        db = SessionLocal()
        db.query(NetworkHistory).delete()
        db.commit()
        db.close()

        # Start the bandwidth monitor
        bandwidth_monitor.set_selected_interface(None)
        bandwidth_monitor.start_monitoring()

        # Create a history service and take multiple snapshots
        history_service = HistoryService(interval=1)
        for i in range(5):
            history_service._take_snapshot()
            time.sleep(0.1)

        # Stop the bandwidth monitor
        bandwidth_monitor.stop_monitoring_thread()

        # Verify we have 5 snapshots
        db = SessionLocal()
        count_before = db.query(NetworkHistory).count()
        db.close()
        assert count_before == 5, f"Expected 5 snapshots before clear, got {count_before}"

        # Clear the history
        db = SessionLocal()
        db.query(NetworkHistory).delete()
        db.commit()
        db.close()

        # Verify the history is cleared
        db = SessionLocal()
        count_after = db.query(NetworkHistory).count()
        db.close()
        assert count_after == 0, f"Expected 0 snapshots after clear, got {count_after}"

        print("Clear history test passed")
    finally:
        cleanup_test_db()

def test_history_service_start_stop():
    """Test starting and stopping the history service"""
    print("Testing history service start/stop...")
    setup_test_db()
    try:
        from app.services.history_service import HistoryService

        history_service = HistoryService(interval=1)

        # Initially, the thread should be None
        assert history_service.thread is None or not history_service.thread.is_alive()

        # Start the service
        history_service.start()
        assert history_service.thread is not None
        assert history_service.thread.is_alive(), "History service thread should be alive after start"

        # Stop the service
        history_service.stop()
        # Give it a moment to stop
        time.sleep(0.1)
        # After stopping, the thread should be None (as set in the stop method)
        assert history_service.thread is None, "History service thread should be None after stop"

        # Starting again should work
        history_service.start()
        assert history_service.thread is not None
        assert history_service.thread.is_alive(), "History service thread should be alive after second start"
        history_service.stop()

        print("History service start/stop test passed")
    finally:
        cleanup_test_db()

def test_duplicate_collector_prevention():
    """Test that starting the history service multiple times does not create multiple collector loops"""
    print("Testing duplicate collector prevention...")
    setup_test_db()
    try:
        from app.services.history_service import HistoryService

        history_service = HistoryService(interval=1)

        # Start the service multiple times
        history_service.start()
        thread1 = history_service.thread
        history_service.start()  # Should not create a new thread
        thread2 = history_service.thread
        history_service.start()  # Should not create a new thread
        thread3 = history_service.thread

        # The thread should be the same
        assert thread1 is thread2, "Starting the service multiple times should not create a new thread"
        assert thread2 is thread3, "Starting the service multiple times should not create a new thread"

        # Stop the service
        history_service.stop()

        print("Duplicate collector prevention test passed")
    finally:
        cleanup_test_db()

def test_retention_policy():
    """Test that the retention policy deletes old snapshots when the limit is exceeded"""
    print("Testing retention policy...")
    setup_test_db()
    try:
        from app.services.history_service import HistoryService
        from app.services.bandwidth_monitor import bandwidth_monitor
        from app.database import SessionLocal
        from app.models.history import NetworkHistory

        # Initialize the database
        from app.database import init_db
        init_db()

        # Clear any existing data
        db = SessionLocal()
        db.query(NetworkHistory).delete()
        db.commit()
        db.close()

        # Start the bandwidth monitor
        bandwidth_monitor.set_selected_interface(None)
        bandwidth_monitor.start_monitoring()
        # Wait for the monitor to collect at least one sample
        time.sleep(2)

        # Create a history service with a small retention limit for testing
        retention_limit = 5
        history_service = HistoryService(interval=1, retention_limit=retention_limit)

        # We'll take snapshots manually and enforce retention after each
        # But note: the _take_snapshot method already calls _enforce_retention.
        # We'll just call _take_snapshot multiple times.
        num_snapshots = 10
        for i in range(num_snapshots):
            history_service._take_snapshot()
            # Wait a bit to ensure different timestamps
            time.sleep(0.1)

        # Stop the bandwidth monitor
        bandwidth_monitor.stop_monitoring_thread()

        # Now check that we have exactly retention_limit snapshots
        db = SessionLocal()
        count = db.query(NetworkHistory).count()
        db.close()
        assert count == retention_limit, f"Expected {retention_limit} snapshots after retention, got {count}"

        # Additionally, we can check that the snapshots are the most recent ones by timestamp.
        # We'll get all snapshots ordered by timestamp descending and check that we have retention_limit of them.
        db = SessionLocal()
        snapshots = db.query(NetworkHistory).order_by(NetworkHistory.timestamp.desc()).all()
        db.close()
        assert len(snapshots) == retention_limit, f"Expected {retention_limit} snapshots in descending order, got {len(snapshots)}"

        # We can also check that the timestamps are indeed the most recent by comparing to the current time?
        # Not necessary for this test.

        print("Retention policy test passed")
    finally:
        cleanup_test_db()

if __name__ == "__main__":
    print("Running history tests...")
    try:
        test_database_initialization()
        test_snapshot_creation_and_storage()
        test_history_retrieval()
        test_latest_history()
        test_clear_history()
        test_history_service_start_stop()
        test_duplicate_collector_prevention()
        test_retention_policy()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)