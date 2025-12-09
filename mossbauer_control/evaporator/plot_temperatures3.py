import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import os
import time
from collections import deque

# Configuration
TEMP_FILE_NAME = "temperatures.txt"
NUM_SENSORS = 10
MAX_POINTS = 3600  # Keep last hour of data (assuming 1 point per second)
UPDATE_INTERVAL = 1000  # Update every 1000ms
MOVING_AVERAGE_WINDOW = 10

# Sensor labels
LABELS = [
    "T (V: 1-2)", "Manipulator (V: 1-2)", "Top Sphere (V: 3-4)", "Window L (V: 3-4)",
    "Window M (V: 5-6)", "Bottom Sphere (V: 5-6)", "Back Sphere (V: 5-6)",
    "Window S (V: 3-4)", "Reducer (V: 7)", "Window LL (V: 7)"
]

# Colors for consistent plotting
COLORS = [
    (31, 119, 180), (255, 127, 14), (44, 160, 44), (214, 39, 40), (148, 103, 189),
    (140, 86, 75), (227, 119, 194), (127, 127, 127), (188, 189, 34), (23, 190, 207)
]

class TemperatureData:
    """Handles temperature data parsing and storage"""
    
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_file_path = os.path.join(self.script_dir, TEMP_FILE_NAME)
        
        # Data storage
        self.timestamps = deque(maxlen=MAX_POINTS)
        self.temperatures = [deque(maxlen=MAX_POINTS) for _ in range(NUM_SENSORS)]
        self.rates = [deque(maxlen=MAX_POINTS) for _ in range(NUM_SENSORS)]
        self.rate_history = [deque(maxlen=MOVING_AVERAGE_WINDOW) for _ in range(NUM_SENSORS)]
        
        self.last_file_size = 0
        self.last_timestamp = 0
        
    def parse_line(self, line):
        """Parse a single line of temperature data"""
        line = line.strip()
        if not line:
            return None
            
        parts = [p.strip() for p in line.split(',') if p.strip()]
        
        # Only accept lines with exactly 11 columns (timestamp + 10 temps)
        if len(parts) != 11:
            return None
            
        try:
            timestamp = float(parts[0])
            if timestamp <= 1000000000:  # Invalid timestamp
                return None
                
            temperatures = []
            for i in range(1, 11):
                temp = float(parts[i])
                if not (-100 <= temp <= 1000):  # Reasonable temperature range
                    temp = 0.0
                temperatures.append(temp)
                
            return timestamp, temperatures
            
        except (ValueError, IndexError):
            return None
            
    def update_data(self):
        """Update data from file"""
        try:
            # Check if file exists and has new data
            if not os.path.exists(self.temp_file_path):
                return False
                
            file_size = os.path.getsize(self.temp_file_path)
            if file_size <= self.last_file_size:
                return False
                
            # Read only new lines
            with open(self.temp_file_path, 'r') as f:
                if self.last_file_size > 0:
                    f.seek(self.last_file_size)
                lines = f.readlines()
                
            self.last_file_size = file_size
            
            # Process new lines
            new_data = False
            for line in lines:
                result = self.parse_line(line)
                if result:
                    timestamp, temps = result
                    
                    # Skip duplicate timestamps
                    if timestamp <= self.last_timestamp:
                        continue
                        
                    self.last_timestamp = timestamp
                    self.timestamps.append(timestamp)
                    
                    # Update temperature data
                    for i in range(NUM_SENSORS):
                        self.temperatures[i].append(temps[i])
                    
                    # Calculate rates of change
                    if len(self.timestamps) >= 2:
                        dt = self.timestamps[-1] - self.timestamps[-2]
                        if dt > 0:
                            for i in range(NUM_SENSORS):
                                if len(self.temperatures[i]) >= 2:
                                    dtemp = self.temperatures[i][-1] - self.temperatures[i][-2]
                                    rate = (dtemp / dt) * 60  # °C/min
                                    
                                    # Add to rate history for moving average
                                    self.rate_history[i].append(rate)
                                    avg_rate = np.mean(self.rate_history[i])
                                    self.rates[i].append(avg_rate)
                                else:
                                    self.rates[i].append(0.0)
                        else:
                            for i in range(NUM_SENSORS):
                                self.rates[i].append(0.0)
                    else:
                        for i in range(NUM_SENSORS):
                            self.rates[i].append(0.0)
                            
                    new_data = True
                    
            return new_data
            
        except Exception as e:
            print(f"Error updating data: {e}")
            return False
            
    def get_plot_data(self):
        """Get data for plotting"""
        if not self.timestamps:
            return None, None, None
            
        # Convert to numpy arrays for plotting
        times = np.array(self.timestamps)
        # Convert to relative time (seconds from start)
        times = times - times[0] if len(times) > 0 else times
        
        temp_data = []
        rate_data = []
        
        for i in range(NUM_SENSORS):
            temp_data.append(np.array(self.temperatures[i]))
            rate_data.append(np.array(self.rates[i]))
            
        return times, temp_data, rate_data

class TemperaturePlotter(QtWidgets.QWidget):
    """Main plotting widget"""
    
    def __init__(self):
        super().__init__()
        self.data_handler = TemperatureData()
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle('Temperature Monitor')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Create control panel
        control_layout = QtWidgets.QHBoxLayout()
        
        # Reset zoom buttons
        self.reset_temp_button = QtWidgets.QPushButton('Reset Temperature Zoom')
        self.reset_rate_button = QtWidgets.QPushButton('Reset Rate Zoom')
        self.reset_all_button = QtWidgets.QPushButton('Reset All Zoom')
        
        self.reset_temp_button.clicked.connect(self.reset_temp_zoom)
        self.reset_rate_button.clicked.connect(self.reset_rate_zoom)
        self.reset_all_button.clicked.connect(self.reset_all_zoom)
        
        # Instructions label
        instructions = QtWidgets.QLabel("Mouse: Left-drag=Pan | Right-drag=Zoom to selection | Wheel=Zoom | Right-click=Menu")
        instructions.setStyleSheet("color: gray; font-size: 10px;")
        
        control_layout.addWidget(self.reset_temp_button)
        control_layout.addWidget(self.reset_rate_button)
        control_layout.addWidget(self.reset_all_button)
        control_layout.addStretch()  # Push buttons to left
        control_layout.addWidget(instructions)
        
        layout.addLayout(control_layout)
        
        # Create plot widgets
        self.temp_plot = pg.PlotWidget(title="Temperature vs Time")
        self.rate_plot = pg.PlotWidget(title="Temperature Rate of Change vs Time")
        
        layout.addWidget(self.temp_plot)
        layout.addWidget(self.rate_plot)
        
        # Configure temperature plot
        self.temp_plot.setLabel('left', 'Temperature', '°C')
        self.temp_plot.setLabel('bottom', 'Time', 's')
        temp_legend = self.temp_plot.addLegend(offset=(10, 10))  # Position legend in top-left corner
        temp_legend.setBrush(pg.mkBrush(0, 0, 0, 255))  # Black background with full opacity
        temp_legend.setPen(pg.mkPen(255, 255, 255, 255))  # White border
        self.temp_plot.showGrid(True, True)
        self.temp_plot.setYRange(0, 300)
        
        # Enable mouse interaction for temperature plot
        self.temp_plot.setMouseEnabled(x=True, y=True)  # Enable mouse panning/zooming
        self.temp_plot.enableAutoRange(enable=False)    # Disable auto-range
        # Enable rectangular selection for zooming
        self.temp_plot.getViewBox().setMenuEnabled(True)  # Enable right-click context menu
        self.temp_plot.getViewBox().setMouseMode(pg.ViewBox.RectMode)  # Enable rectangle selection by default
        
        # Configure rate plot
        self.rate_plot.setLabel('left', 'Rate of Change', '°C/min')
        self.rate_plot.setLabel('bottom', 'Time', 's')
        rate_legend = self.rate_plot.addLegend(offset=(10, 10))  # Position legend in top-left corner
        rate_legend.setBrush(pg.mkBrush(0, 0, 0, 255))  # Black background with full opacity
        rate_legend.setPen(pg.mkPen(255, 255, 255, 255))  # White border
        self.rate_plot.showGrid(True, True)
        self.rate_plot.setYRange(-10, 10)
        
        # Enable mouse interaction for rate plot
        self.rate_plot.setMouseEnabled(x=True, y=True)  # Enable mouse panning/zooming
        self.rate_plot.enableAutoRange(enable=False)    # Disable auto-range
        # Enable rectangular selection for zooming
        self.rate_plot.getViewBox().setMenuEnabled(True)  # Enable right-click context menu
        self.rate_plot.getViewBox().setMouseMode(pg.ViewBox.RectMode)  # Enable rectangle selection by default
        
        # Add reference lines to rate plot
        self.rate_plot.addLine(y=3, pen=pg.mkPen(color='white', style=QtCore.Qt.DashLine, width=2))
        self.rate_plot.addLine(y=-3, pen=pg.mkPen(color='white', style=QtCore.Qt.DashLine, width=2))
        
        # Create plot curves
        self.temp_curves = []
        self.rate_curves = []
        
        # Store initial ranges for reset functionality
        self.initial_temp_range = {'x': (0, 1800), 'y': (0, 300)}
        self.initial_rate_range = {'x': (0, 1800), 'y': (-10, 10)}
        
        for i in range(NUM_SENSORS):
            # Temperature curves  
            label = f"{i+1} {LABELS[i]}"
            temp_curve = self.temp_plot.plot(
                pen=pg.mkPen(color=COLORS[i], width=2),
                name=label
            )
            self.temp_curves.append(temp_curve)
            
            # Rate curves
            rate_curve = self.rate_plot.plot(
                pen=pg.mkPen(color=COLORS[i], width=2),
                name=label
            )
            self.rate_curves.append(rate_curve)
            
    def setup_timer(self):
        """Setup update timer"""
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(UPDATE_INTERVAL)
    
    def reset_temp_zoom(self):
        """Reset temperature plot zoom to show all data"""
        times, temp_data, rate_data = self.data_handler.get_plot_data()
        if times is not None and len(times) > 0:
            self.temp_plot.setXRange(0, times[-1])
            # Find min/max temperatures for better Y range
            all_temps = np.concatenate([temp for temp in temp_data if len(temp) > 0])
            if len(all_temps) > 0:
                min_temp = max(0, np.min(all_temps) - 10)
                max_temp = np.max(all_temps) + 10
                self.temp_plot.setYRange(min_temp, max_temp)
        else:
            self.temp_plot.setXRange(*self.initial_temp_range['x'])
            self.temp_plot.setYRange(*self.initial_temp_range['y'])
    
    def reset_rate_zoom(self):
        """Reset rate plot zoom to show all data"""
        times, temp_data, rate_data = self.data_handler.get_plot_data()
        if times is not None and len(times) > 0:
            self.rate_plot.setXRange(0, times[-1])
        else:
            self.rate_plot.setXRange(*self.initial_rate_range['x'])
        # Always set Y range to +/-10 for rate plot
        self.rate_plot.setYRange(-10, 10)
    
    def reset_all_zoom(self):
        """Reset both plots to show all data"""
        self.reset_temp_zoom()
        self.reset_rate_zoom()
        
    def update_plots(self):
        """Update plot data"""
        if self.data_handler.update_data():
            times, temp_data, rate_data = self.data_handler.get_plot_data()
            
            if times is not None:
                # Update temperature plots
                for i in range(NUM_SENSORS):
                    if len(temp_data[i]) > 0:
                        self.temp_curves[i].setData(times, temp_data[i])
                        self.rate_curves[i].setData(times, rate_data[i])
                        
                # Only auto-range if not manually zoomed
                # Check if plots are at default ranges (indicating no manual zoom)
                temp_vb = self.temp_plot.getViewBox()
                rate_vb = self.rate_plot.getViewBox()
                
                if not temp_vb.state['mouseEnabled'][0] or not hasattr(self, '_temp_manually_zoomed'):
                    if len(times) > 0:
                        self.temp_plot.setXRange(max(0, times[-1] - 1800), times[-1])  # Last 30 minutes
                        
                if not rate_vb.state['mouseEnabled'][0] or not hasattr(self, '_rate_manually_zoomed'):
                    if len(times) > 0:
                        self.rate_plot.setXRange(max(0, times[-1] - 1800), times[-1])  # Last 30 minutes

def main():
    """Main function"""
    app = QtWidgets.QApplication([])
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show plotter
    plotter = TemperaturePlotter()
    plotter.show()
    
    # Run application
    app.exec_()

if __name__ == '__main__':
    main()