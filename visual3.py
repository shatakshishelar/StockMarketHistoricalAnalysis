import sys
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QComboBox, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QToolTip)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib import colors as mcolors

# Define a dictionary to store DataFrames for each stock
stock_data = {}
stock_metadata = pd.read_excel("CS 439 final project data/top_25_us_stocks.xlsx")

# Convert market cap strings to numeric values
stock_metadata['Market Cap'] = stock_metadata['Market Cap'].str.extract(r'(\d+\.?\d*)').astype(float)

# Load each stock's data
tickers = ["AAPL", "ABBV", "AVGO", "BAC", "BRK.A", "BRK.B", "COST", "GOOGL", "HD", "JNJ", "JPM", "LLY", "MA", "META",
           "MSFT", "NFLX", "NVDA", "ORCL", "PG", "TSLA", "UNH", "V", "WMT", "XOM"]
file_paths = [f"CS 439 final project data/MacroTrends_Data_Download_{ticker}.csv" for ticker in tickers]
for ticker, file_path in zip(tickers, file_paths):
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    stock_data[ticker] = df


def calculate_yearly_percentage_change(df):
    df = df.resample('Y').last()
    df['yearly_pct_change'] = df['close'].pct_change() * 100
    df['cumulative_return'] = (1 + df['close'].pct_change()).cumprod() - 1
    df['cumulative_return'] = df['cumulative_return'] * 100
    return df


class YearlyChangePlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=15, height=10, dpi=100):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setMouseTracking(True)
        self.bars_data = {}
        self.current_annotation = None

        # Define the ticker to company name mapping
        self.ticker_company_map = {
            "AAPL": "Apple", "ABBV": "AbbVie", "AVGO": "Broadcom", "BAC": "Bank of America",
            "BRK.A": "Berkshire Hathaway A", "BRK.B": "Berkshire Hathaway B", "COST": "Costco",
            "GOOGL": "Alphabet", "HD": "Home Depot", "JNJ": "Johnson & Johnson", "JPM": "JPMorgan Chase",
            "LLY": "Eli Lilly", "MA": "MasterCard", "META": "Meta Platforms", "MSFT": "Microsoft",
            "NFLX": "Netflix", "NVDA": "NVIDIA", "ORCL": "Oracle", "PG": "Procter & Gamble",
            "TSLA": "Tesla", "UNH": "UnitedHealth", "V": "Visa", "WMT": "Walmart", "XOM": "ExxonMobil"
        }

        # Create a frame for annotations that persists
        self.annotation_frame = dict(
            boxstyle="round,pad=0.5",
            fc="white",
            ec="gray",
            alpha=0.8,
            zorder=100
        )

    def mouseMoveEvent(self, event):
        """Handle Qt mouse move events with custom annotation bubbles"""
        try:
            # Get the mouse position in widget coordinates
            pos = event.position()

            # Convert Qt widget coordinates to figure coordinates
            dpi_scale_factor = self.devicePixelRatioF()
            width = self.width() * dpi_scale_factor
            height = self.height() * dpi_scale_factor

            # Calculate the relative position within the widget
            x_rel = pos.x() * dpi_scale_factor
            y_rel = pos.y() * dpi_scale_factor

            # Convert to data coordinates
            data_x, data_y = self.ax.transData.inverted().transform((x_rel, height - y_rel))

            # Find the bar at the cursor position
            found_bar = None
            closest_distance = float('inf')

            for bar in self.ax.patches:
                if bar in self.bars_data:
                    bar_x = bar.get_x()
                    bar_width = bar.get_width()
                    bar_height = bar.get_height()
                    bar_y = bar.get_y()

                    # Calculate center of the bar
                    bar_center_x = bar_x + bar_width / 2

                    # Check if cursor is within reasonable distance of the bar
                    x_distance = abs(data_x - bar_center_x)

                    if x_distance < bar_width / 2:  # Within bar width
                        # For positive bars
                        if bar_height >= 0 and data_y <= (bar_y + bar_height) and data_y >= bar_y:
                            if x_distance < closest_distance:
                                found_bar = bar
                                closest_distance = x_distance
                        # For negative bars
                        elif bar_height < 0 and data_y >= (bar_y + bar_height) and data_y <= bar_y:
                            if x_distance < closest_distance:
                                found_bar = bar
                                closest_distance = x_distance

            # Remove existing annotation if it exists
            if self.current_annotation:
                self.current_annotation.remove()
                self.current_annotation = None
                self.draw_idle()

            if found_bar:
                # Get data for the found bar
                ticker, year, yearly_change, cum_return = self.bars_data[found_bar]

                # Get company name from the mapping
                company_name = self.ticker_company_map.get(ticker, "Unknown Company")

                # Create annotation text with company name
                annotation_text = (
                    f"Company: {company_name}\n"
                    f"Ticker: {ticker}\n"
                    f"Year: {year}\n"
                    f"Yearly Change: {yearly_change:.1f}%\n"
                    f"Cumulative Return: {cum_return:.1f}%"
                )

                # Get bar properties for positioning
                bar_x = found_bar.get_x()
                bar_width = found_bar.get_width()
                bar_y = found_bar.get_y()
                bar_height = found_bar.get_height()
                bar_center = bar_x + bar_width / 2

                # Position tooltip close to cursor but ensure it's anchored to the bar
                if bar_height >= 0:
                    xy = (bar_center, bar_y + bar_height)
                    xytext = (0, 10)  # Reduced vertical offset
                    va = 'bottom'
                else:
                    xy = (bar_center, bar_y + bar_height)
                    xytext = (0, -10)  # Reduced vertical offset
                    va = 'top'

                # Create the annotation with arrow
                self.current_annotation = self.ax.annotate(
                    annotation_text,
                    xy=xy,
                    xytext=xytext,
                    textcoords='offset points',
                    bbox=self.annotation_frame,
                    ha='center',
                    va=va,
                    arrowprops=dict(
                        arrowstyle='-|>',
                        connectionstyle='arc3,rad=0',
                        color='gray',
                        alpha=0.8,
                        linewidth=1,
                        zorder=99
                    )
                )

                self.draw_idle()

        except Exception as e:
            print(f"Error in mouseMoveEvent: {e}")

    def leaveEvent(self, event):
        """Handle mouse leaving the widget"""
        if self.current_annotation:
            self.current_annotation.remove()
            self.current_annotation = None
            self.draw_idle()
        super().leaveEvent(event)

    def plot_yearly_changes(self, tickers, start_year=None, end_year=None):
        """Plot a grouped bar chart for yearly price changes with tooltips."""
        self.ax.clear()
        self.bars_data.clear()

        # Remove any existing annotation when replotting
        if self.current_annotation:
            self.current_annotation.remove()
            self.current_annotation = None

        yearly_changes = []

        # Collect yearly percentage changes for each ticker
        for ticker in tickers:
            if ticker in stock_data:
                df = calculate_yearly_percentage_change(stock_data[ticker])
                df = df[(df.index.year >= start_year) & (df.index.year <= end_year)]
                if not df.empty:
                    yearly_changes.append((ticker, df))

        if yearly_changes:
            # Prepare data for plotting
            years = sorted(set(year for _, data in yearly_changes for year in data.index.year))
            n_tickers = len(yearly_changes)
            bar_width = 0.8 / n_tickers
            offsets = [(i - n_tickers / 2) * bar_width for i in range(n_tickers)]

            # Use a color cycle and hatch patterns
            color_cycle = plt.cm.tab20.colors  # Choose a color map with many distinct colors
            hatches = ['', '/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']  # List of hatch patterns
            color_count = len(color_cycle)
            hatch_count = len(hatches)

            # Plot each ticker's yearly changes
            for i, (offset, (ticker, data)) in enumerate(zip(offsets, yearly_changes)):
                data = data.dropna()
                x_positions = [years.index(year) + offset for year in data.index.year]

                # Cycle through colors and patterns
                color = color_cycle[i % color_count]
                hatch = hatches[i % hatch_count] if i >= color_count else None

                bars = self.ax.bar(x_positions, data['yearly_pct_change'].values,
                                   width=bar_width, label=ticker, color=color, hatch=hatch)

                # Store bar data for tooltips
                for bar, year, yearly_change, cum_return in zip(bars, data.index.year,
                                                                data['yearly_pct_change'],
                                                                data['cumulative_return']):
                    self.bars_data[bar] = (ticker, year, yearly_change, cum_return)

            self.ax.set_xticks(range(len(years)))
            self.ax.set_xticklabels(years, rotation=45)
            self.ax.set_xlabel("Year")
            self.ax.set_ylabel("Yearly % Change")
            self.ax.set_title("Yearly Price Change by Ticker")

            # Add grid for better readability
            self.ax.grid(True, linestyle='--', alpha=0.7)

            # Place legend outside the plot on the right
            self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

            # Adjust layout to prevent legend cutoff
            plt.tight_layout()
        else:
            self.ax.set_title("No data available for selected criteria")

        self.draw()


class StockViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main widget and layout
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)

        # Filter layouts
        self.filter_layout = QHBoxLayout()
        self.market_cap_layout = QHBoxLayout()
        self.year_layout = QHBoxLayout()

        # Dropdowns for filtering
        self.sector_dropdown = QComboBox(self)
        self.state_dropdown = QComboBox(self)
        self.location_dropdown = QComboBox(self)

        # Populate dropdowns with unique values from metadata
        self.sector_dropdown.addItem("All")
        self.state_dropdown.addItem("All")
        self.location_dropdown.addItem("All")
        self.sector_dropdown.addItems(sorted(stock_metadata['Sector'].unique()))
        self.state_dropdown.addItems(sorted(stock_metadata['Headquarters State'].unique()))
        self.location_dropdown.addItems(sorted(stock_metadata['Headquarters Location'].unique()))

        # Market Cap Range Filter with improved width
        self.min_market_cap = QDoubleSpinBox(self)
        self.max_market_cap = QDoubleSpinBox(self)

        # Configure the market cap spinboxes
        for spinbox in [self.min_market_cap, self.max_market_cap]:
            # Set minimum width to accommodate larger numbers
            spinbox.setMinimumWidth(150)

            # Increase the maximum number of digits that can be displayed
            spinbox.setMaximum(999999.9)
            spinbox.setDecimals(1)
            spinbox.setSuffix("B")

            # Right-align the text for better reading
            spinbox.setAlignment(Qt.AlignmentFlag.AlignRight)

            # Set step to 0.1 billion for finer control
            spinbox.setSingleStep(0.1)

            # Optional: Add thousands separator for better readability
            spinbox.setGroupSeparatorShown(True)

        # Set initial values
        max_cap = stock_metadata['Market Cap'].max()
        min_cap = stock_metadata['Market Cap'].min()
        self.min_market_cap.setValue(min_cap)
        self.max_market_cap.setValue(max_cap)

        # Add dropdowns to layout
        self.filter_layout.addWidget(QLabel("Sector:"))
        self.filter_layout.addWidget(self.sector_dropdown)
        self.filter_layout.addWidget(QLabel("State:"))
        self.filter_layout.addWidget(self.state_dropdown)
        self.filter_layout.addWidget(QLabel("Location:"))
        self.filter_layout.addWidget(self.location_dropdown)

        # Create a more organized market cap layout
        market_cap_label = QLabel("Market Cap Range ($B):")
        market_cap_label.setMinimumWidth(120)  # Ensure label is fully visible

        self.market_cap_layout.addWidget(market_cap_label)
        self.market_cap_layout.addWidget(QLabel("Min:"))
        self.market_cap_layout.addWidget(self.min_market_cap)
        self.market_cap_layout.addWidget(QLabel("Max:"))
        self.market_cap_layout.addWidget(self.max_market_cap)
        self.market_cap_layout.addStretch()

        # Start and End year
        self.start_year_spinbox = QSpinBox(self)
        self.start_year_spinbox.setRange(1980, 2024)
        self.start_year_spinbox.setValue(1980)
        self.end_year_spinbox = QSpinBox(self)
        self.end_year_spinbox.setRange(1980, 2024)
        self.end_year_spinbox.setValue(2024)

        self.year_layout.addWidget(QLabel("Start Year:"))
        self.year_layout.addWidget(self.start_year_spinbox)
        self.year_layout.addWidget(QLabel("End Year:"))
        self.year_layout.addWidget(self.end_year_spinbox)

        # Connect all filters to plot update
        self.sector_dropdown.currentTextChanged.connect(self.update_plot)
        self.state_dropdown.currentTextChanged.connect(self.update_plot)
        self.location_dropdown.currentTextChanged.connect(self.update_plot)
        self.min_market_cap.valueChanged.connect(self.update_plot)
        self.max_market_cap.valueChanged.connect(self.update_plot)
        self.start_year_spinbox.valueChanged.connect(self.update_plot)
        self.end_year_spinbox.valueChanged.connect(self.update_plot)

        # Matplotlib canvas and toolbar
        self.plot_canvas = YearlyChangePlotCanvas(self, width=15, height=10)
        self.toolbar = NavigationToolbar2QT(self.plot_canvas, self)

        # Add layouts and widgets to the main layout
        self.layout.addLayout(self.filter_layout)
        self.layout.addLayout(self.market_cap_layout)
        self.layout.addLayout(self.year_layout)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.plot_canvas)
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

        # Initial plot
        self.update_plot()

    def get_filtered_tickers(self):
        filtered_data = stock_metadata.copy()

        # Apply existing filters
        if self.sector_dropdown.currentText() != "All":
            filtered_data = filtered_data[filtered_data['Sector'] == self.sector_dropdown.currentText()]
        if self.state_dropdown.currentText() != "All":
            filtered_data = filtered_data[filtered_data['Headquarters State'] == self.state_dropdown.currentText()]
        if self.location_dropdown.currentText() != "All":
            filtered_data = filtered_data[
                filtered_data['Headquarters Location'] == self.location_dropdown.currentText()]

        # Apply market cap filter
        min_cap = self.min_market_cap.value()
        max_cap = self.max_market_cap.value()
        filtered_data = filtered_data[
            (filtered_data['Market Cap'] >= min_cap) &
            (filtered_data['Market Cap'] <= max_cap)
            ]

        return filtered_data['Ticker'].tolist()

    def update_plot(self):
        start_year = self.start_year_spinbox.value()
        end_year = self.end_year_spinbox.value()
        tickers = self.get_filtered_tickers()
        self.plot_canvas.plot_yearly_changes(tickers, start_year, end_year)


def main():
    app = QApplication(sys.argv)
    viewer = StockViewerApp()
    viewer.setWindowTitle("Yearly Price Change Viewer")
    viewer.resize(1200, 800)
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
