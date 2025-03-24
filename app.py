import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                             QPushButton, QLabel, QProgressBar, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal
import speedtest


class SpeedTestThread(QThread):
    """
    Thread to run the speed test in the background to prevent GUI freezing
    """
    update_signal = pyqtSignal(str, float)
    progress_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)

    def run(self):
        try:
            self.progress_signal.emit(10)
            st = speedtest.Speedtest()
            
            # Get best server
            self.update_signal.emit("Finding best server...", 0)
            st.get_best_server()
            self.progress_signal.emit(30)
            
            # Test download speed
            self.update_signal.emit("Testing download speed...", 0)
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            self.update_signal.emit(f"Download: {download_speed:.2f} Mbps", download_speed)
            self.progress_signal.emit(60)
            
            # Test upload speed
            self.update_signal.emit("Testing upload speed...", 0)
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            self.update_signal.emit(f"Upload: {upload_speed:.2f} Mbps", upload_speed)
            self.progress_signal.emit(90)
            
            # Get ping
            ping = st.results.ping
            self.update_signal.emit(f"Ping: {ping:.2f} ms", 0)
            self.progress_signal.emit(100)
            
        except Exception as e:
            self.error_signal.emit(f"Error: {str(e)}")


class SpeedTestGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Internet Speed Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Main widget and layout
        self.main_widget = QWidget()
        self.layout = QVBoxLayout()
        
        # Create UI elements
        self.title_label = QLabel("Internet Speed Test")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        self.status_label = QLabel("Click 'Start Test' to begin")
        self.status_label.setStyleSheet("font-size: 14px;")
        
        self.download_label = QLabel("Download: -- Mbps")
        self.upload_label = QLabel("Upload: -- Mbps")
        self.ping_label = QLabel("Ping: -- ms")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        
        self.start_button = QPushButton("Start Test")
        self.start_button.clicked.connect(self.start_test)
        
        # Add elements to layout
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.download_label)
        self.layout.addWidget(self.upload_label)
        self.layout.addWidget(self.ping_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.start_button)
        
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)
        
        # Thread for speed test
        self.test_thread = None

    def start_test(self):
        """Start the speed test"""
        if self.test_thread and self.test_thread.isRunning():
            return
            
        # Reset UI
        self.download_label.setText("Download: -- Mbps")
        self.upload_label.setText("Upload: -- Mbps")
        self.ping_label.setText("Ping: -- ms")
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting test...")
        
        # Create and start thread
        self.test_thread = SpeedTestThread()
        self.test_thread.update_signal.connect(self.update_status)
        self.test_thread.progress_signal.connect(self.progress_bar.setValue)
        self.test_thread.error_signal.connect(self.show_error)
        self.test_thread.finished.connect(self.test_complete)
        self.test_thread.start()
        
        self.start_button.setEnabled(False)

    def update_status(self, message, speed):
        """Update the status labels"""
        if "Download" in message:
            self.download_label.setText(message)
        elif "Upload" in message:
            self.upload_label.setText(message)
        elif "Ping" in message:
            self.ping_label.setText(message)
        self.status_label.setText(message)

    def show_error(self, message):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
        self.test_complete()

    def test_complete(self):
        """Clean up after test completes"""
        self.status_label.setText("Test complete!")
        self.start_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Check if speedtest-cli is available
    try:
        import speedtest
    except ImportError:
        QMessageBox.critical(None, "Error", 
                            "speedtest-cli package not found. Please install it with:\n\npip install speedtest-cli")
        sys.exit(1)
    
    window = SpeedTestGUI()
    window.show()
    sys.exit(app.exec_())