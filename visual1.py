import sys
import mplcursors
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QMainWindow, QComboBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

# Define a dictionary to store DataFrames for each stock
stock_data = {}


def load_market_events(excel_path):
    try:
        # Read the Excel file
        events_df = pd.read_excel(excel_path, sheet_name='Sheet1')

        # Convert dates to datetime
        events_df['Start Date'] = pd.to_datetime(events_df['Start Date'])
        events_df['End Date'] = pd.to_datetime(events_df['End Date'])

        return events_df
    except Exception as e:
        print(f"Error loading market events: {e}")
        return pd.DataFrame()


# Load market events from Excel
market_events = load_market_events('CS 439 final project data/stock_market_events_with_dates.xlsx')

# List of stock tickers and their respective CSV file paths
tickers = ["AAPL", "ABBV", "AVGO", "BAC", "BRK.A", "BRK.B", "COST", "GOOGL", "HD", "JNJ", "JPM", "LLY", "MA", "META",
           "MSFT", "NFLX", "NVDA", "ORCL", "PG", "TSLA", "UNH", "V", "WMT", "XOM"]
file_paths = [
    "CS 439 final project data/MacroTrends_Data_Download_AAPL.csv",
    "CS 439 final project data/MacroTrends_Data_Download_ABBV.csv",
    "CS 439 final project data/MacroTrends_Data_Download_AVGO.csv",
    "CS 439 final project data/MacroTrends_Data_Download_BAC.csv",
    "CS 439 final project data/MacroTrends_Data_Download_BRK.A.csv",
    "CS 439 final project data/MacroTrends_Data_Download_BRK.B.csv",
    "CS 439 final project data/MacroTrends_Data_Download_COST.csv",
    "CS 439 final project data/MacroTrends_Data_Download_GOOGL.csv",
    "CS 439 final project data/MacroTrends_Data_Download_HD.csv",
    "CS 439 final project data/MacroTrends_Data_Download_JNJ.csv",
    "CS 439 final project data/MacroTrends_Data_Download_JPM.csv",
    "CS 439 final project data/MacroTrends_Data_Download_LLY.csv",
    "CS 439 final project data/MacroTrends_Data_Download_MA.csv",
    "CS 439 final project data/MacroTrends_Data_Download_META.csv",
    "CS 439 final project data/MacroTrends_Data_Download_MSFT.csv",
    "CS 439 final project data/MacroTrends_Data_Download_NFLX.csv",
    "CS 439 final project data/MacroTrends_Data_Download_NVDA.csv",
    "CS 439 final project data/MacroTrends_Data_Download_ORCL.csv",
    "CS 439 final project data/MacroTrends_Data_Download_PG.csv",
    "CS 439 final project data/MacroTrends_Data_Download_TSLA.csv",
    "CS 439 final project data/MacroTrends_Data_Download_UNH.csv",
    "CS 439 final project data/MacroTrends_Data_Download_V.csv",
    "CS 439 final project data/MacroTrends_Data_Download_WMT.csv",
    "CS 439 final project data/MacroTrends_Data_Download_XOM.csv"
]

# Load each CSV file into a DataFrame and store it in the dictionary
for ticker, file_path in zip(tickers, file_paths):
    stock_data[ticker] = pd.read_csv(file_path)
    stock_data[ticker]['date'] = pd.to_datetime(stock_data[ticker]['date'])


class StockPlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self.setParent(parent)
        self.price_cursor = None
        self.event_cursor = None
        self.event_spans = []
        self.event_lines = []
        self.event_artists = []

    def plot_stock(self, ticker, start_year=None, end_year=None):
        self.ax.clear()
        if ticker in stock_data:
            df = stock_data[ticker]

            # Plot the main line for closing prices
            line, = self.ax.plot(df['date'], df['close'], label=ticker)

            # Highlight specified year range
            if start_year and end_year:
                highlight = df[(df['date'].dt.year >= start_year) & (df['date'].dt.year <= end_year)]
                highlight_line = self.ax.plot(highlight['date'], highlight['close'],
                                              color='orange',
                                              linewidth=2,
                                              label='Highlighted Range')

            # Add market events
            self.plot_market_events(start_year, end_year)

            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Closing Price")
            self.ax.set_title(f"Closing Prices for {ticker}")
            self.ax.legend()

            plt.tight_layout()

            # Remove old price cursor if it exists
            if self.price_cursor is not None:
                self.price_cursor.remove()

            # Add new cursor for the price data
            self.price_cursor = mplcursors.cursor(line, hover=True)

            @self.price_cursor.connect("add")
            def on_add(sel):
                date = mdates.num2date(sel.target[0])
                price = sel.target[1]
                sel.annotation.set_text(f'Date: {date.strftime("%Y-%m-%d")}\nPrice: ${price:.2f}')
                sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.8)

            self.draw()

    def plot_market_events(self, start_year=None, end_year=None):
        # Clear previous events
        for span in self.event_spans:
            span.remove()
        self.event_spans = []

        for line in self.event_lines:
            line.remove()
        self.event_lines = []

        # Clear the event artists list
        self.event_artists = []

        if market_events.empty:
            return

        # Filter events based on year range if specified
        filtered_events = market_events.copy()
        if start_year and end_year:
            filtered_events = market_events[
                (market_events['Start Date'].dt.year <= end_year) &
                (market_events['End Date'].dt.year >= start_year)
                ]

        for _, event in filtered_events.iterrows():
            if event['Start Date'] == event['End Date']:
                # Single-day event: vertical line
                line = self.ax.axvline(x=event['Start Date'], color='red', linestyle='--', alpha=0.3)
                self.event_lines.append(line)
                self.event_artists.append((line, event))

            else:
                # Date range event: shaded region
                span = self.ax.axvspan(
                    event['Start Date'],
                    event['End Date'],
                    alpha=0.2,
                    color='red'
                )
                self.event_spans.append(span)
                self.event_artists.append((span, event))

        # Remove old event cursor if it exists
        if self.event_cursor is not None:
            self.event_cursor.remove()

        # Create a single cursor for all event artists
        self.event_cursor = mplcursors.cursor(
            [artist for artist, _ in self.event_artists],
            hover=True
        )

        @self.event_cursor.connect("add")
        def on_add(sel):
            # Find the corresponding event data
            for artist, event in self.event_artists:
                if artist == sel.artist:
                    if event['Start Date'] == event['End Date']:
                        sel.annotation.set_text(
                            f"Event: {event['Event']}\n"
                            f"Date: {event['Start Date'].strftime('%Y-%m-%d')}"
                        )
                    else:
                        sel.annotation.set_text(
                            f"Event: {event['Event']}\n"
                            f"Period: {event['Start Date'].strftime('%Y-%m-%d')} to\n"
                            f"        {event['End Date'].strftime('%Y-%m-%d')}"
                        )
                    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)
                    break

    def calculate_cumulative_gain(self, ticker, start_year, end_year):
        """Calculate the cumulative gain for a stock over a specified period."""
        if ticker in stock_data:
            df = stock_data[ticker]
            selected_data = df[(df['date'].dt.year >= start_year) & (df['date'].dt.year <= end_year)]
            if not selected_data.empty:
                start_price = selected_data['close'].iloc[0]
                end_price = selected_data['close'].iloc[-1]
                cumulative_gain = ((end_price - start_price) / start_price) * 100
                return cumulative_gain
        return None

class StockViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main widget and layout
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)

        # Create a horizontal layout for the label and dropdown
        self.ticker_layout = QHBoxLayout()
        self.label = QLabel("Choose Ticker:")

        # Dropdown to select stock ticker
        self.ticker_dropdown = QComboBox(self)
        self.ticker_dropdown.addItems(tickers)
        self.ticker_dropdown.currentTextChanged.connect(self.update_plot)

        # Add label and dropdown to the horizontal layout
        self.ticker_layout.addWidget(self.label)
        self.ticker_layout.addWidget(self.ticker_dropdown)

        # Create a horizontal layout for year selection
        self.year_layout = QHBoxLayout()

        # Start year selection
        self.start_year_label = QLabel("Start Year:")
        self.start_year_spinbox = QSpinBox(self)
        self.start_year_spinbox.setMinimum(1980)
        self.start_year_spinbox.setMaximum(2024)
        self.start_year_spinbox.setValue(1980)
        self.start_year_spinbox.valueChanged.connect(self.update_plot)

        # End year selection
        self.end_year_label = QLabel("End Year:")
        self.end_year_spinbox = QSpinBox(self)
        self.end_year_spinbox.setMinimum(1980)
        self.end_year_spinbox.setMaximum(2024)
        self.end_year_spinbox.setValue(2024)
        self.end_year_spinbox.valueChanged.connect(self.update_plot)

        # Cumulative gain label
        self.cumulative_gain_label = QLabel("Cumulative Gain: N/A")

        # Add year selection widgets to the year layout
        self.year_layout.addWidget(self.start_year_label)
        self.year_layout.addWidget(self.start_year_spinbox)
        self.year_layout.addWidget(self.end_year_label)
        self.year_layout.addWidget(self.end_year_spinbox)
        self.year_layout.addWidget(self.cumulative_gain_label)

        # Matplotlib canvas for plotting
        self.plot_canvas = StockPlotCanvas(self, width=8, height=6)

        # Add navigation toolbar
        self.toolbar = NavigationToolbar2QT(self.plot_canvas, self)

        # Add layouts and widgets to the main vertical layout
        self.layout.addLayout(self.ticker_layout)
        self.layout.addLayout(self.year_layout)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.plot_canvas)
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

        # Initial plot for the default selection
        self.update_plot()

    def update_plot(self):
        ticker = self.ticker_dropdown.currentText()
        start_year = self.start_year_spinbox.value()
        end_year = self.end_year_spinbox.value()
        self.plot_canvas.plot_stock(ticker, start_year, end_year)

        # Calculate and display cumulative gain
        cumulative_gain = self.plot_canvas.calculate_cumulative_gain(ticker, start_year, end_year)
        if cumulative_gain is not None:
            self.cumulative_gain_label.setText(f"Cumulative Gain: {cumulative_gain:.2f}%")
        else:
            self.cumulative_gain_label.setText("Cumulative Gain: N/A")


def main():
    app = QApplication(sys.argv)
    viewer = StockViewerApp()
    viewer.setWindowTitle("Stock Viewer")
    viewer.resize(800, 600)
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()