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


# Define a dictionary mapping tickers to company names
ticker_company_map = {
    "AAPL": "Apple", "ABBV": "AbbVie", "AVGO": "Broadcom", "BAC": "Bank of America",
    "BRK.A": "Berkshire Hathaway A", "BRK.B": "Berkshire Hathaway B", "COST": "Costco",
    "GOOGL": "Alphabet", "HD": "Home Depot", "JNJ": "Johnson & Johnson", "JPM": "JPMorgan Chase",
    "LLY": "Eli Lilly", "MA": "MasterCard", "META": "Meta Platforms", "MSFT": "Microsoft",
    "NFLX": "Netflix", "NVDA": "NVIDIA", "ORCL": "Oracle", "PG": "Procter & Gamble",
    "TSLA": "Tesla", "UNH": "UnitedHealth", "V": "Visa", "WMT": "Walmart", "XOM": "ExxonMobil"
}

# Update tickers list to display both ticker and company names
formatted_tickers = [f"{ticker} - {name}" for ticker, name in ticker_company_map.items()]

def load_market_events(excel_path):
    try:
        # Read the Excel file
        events_df = pd.read_excel(excel_path, sheet_name='Sheet1')
        events_df['Start Date'] = pd.to_datetime(events_df['Start Date'])
        events_df['End Date'] = pd.to_datetime(events_df['End Date'])
        return events_df
    except Exception as e:
        print(f"Error loading market events: {e}")
        return pd.DataFrame()

# Load market events from Excel
market_events = load_market_events('CS 439 final project data/stock_market_events_with_dates.xlsx')

# List of stock tickers and their respective CSV file paths
tickers = list(ticker_company_map.keys())
file_paths = [
    f"CS 439 final project data/MacroTrends_Data_Download_{ticker}.csv" for ticker in tickers
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

    def plot_stock(self, ticker, start_year=None, end_year=None, company_name=""):
        self.ax.clear()
        if ticker in stock_data:
            df = stock_data[ticker]
            line, = self.ax.plot(df['date'], df['close'], label=ticker)

            if start_year and end_year:
                highlight = df[(df['date'].dt.year >= start_year) & (df['date'].dt.year <= end_year)]
                self.ax.plot(highlight['date'], highlight['close'], color='orange', linewidth=2, label='Highlighted Range')

            self.plot_market_events(start_year, end_year)
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Closing Price")
            self.ax.set_title(f"Closing Prices for {company_name} ({ticker})")
            self.ax.legend()
            plt.tight_layout()

            if self.price_cursor is not None:
                self.price_cursor.remove()

            self.price_cursor = mplcursors.cursor(line, hover=True)
            @self.price_cursor.connect("add")
            def on_add(sel):
                date = mdates.num2date(sel.target[0])
                price = sel.target[1]
                sel.annotation.set_text(f'Date: {date.strftime("%Y-%m-%d")}\nPrice: ${price:.2f}')
                sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.8)

            self.draw()

    def plot_market_events(self, start_year=None, end_year=None):
        for span in self.event_spans:
            span.remove()
        self.event_spans = []

        for line in self.event_lines:
            line.remove()
        self.event_lines = []
        self.event_artists = []

        if market_events.empty:
            return

        filtered_events = market_events.copy()
        if start_year and end_year:
            filtered_events = market_events[
                (market_events['Start Date'].dt.year <= end_year) &
                (market_events['End Date'].dt.year >= start_year)
            ]

        for _, event in filtered_events.iterrows():
            if event['Start Date'] == event['End Date']:
                line = self.ax.axvline(x=event['Start Date'], color='red', linestyle='--', alpha=0.3)
                self.event_lines.append(line)
                self.event_artists.append((line, event))
            else:
                span = self.ax.axvspan(event['Start Date'], event['End Date'], alpha=0.2, color='red')
                self.event_spans.append(span)
                self.event_artists.append((span, event))

        if self.event_cursor is not None:
            self.event_cursor.remove()

        self.event_cursor = mplcursors.cursor([artist for artist, _ in self.event_artists], hover=True)
        @self.event_cursor.connect("add")
        def on_add(sel):
            for artist, event in self.event_artists:
                if artist == sel.artist:
                    if event['Start Date'] == event['End Date']:
                        sel.annotation.set_text(f"Event: {event['Event']}\nDate: {event['Start Date'].strftime('%Y-%m-%d')}")
                    else:
                        sel.annotation.set_text(f"Event: {event['Event']}\nPeriod: {event['Start Date'].strftime('%Y-%m-%d')} to\n        {event['End Date'].strftime('%Y-%m-%d')}")
                    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)
                    break

    def calculate_cumulative_gain(self, ticker, start_year, end_year):
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
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)

        self.ticker_layout = QHBoxLayout()
        self.label = QLabel("Choose Ticker:")

        self.ticker_dropdown = QComboBox(self)
        self.ticker_dropdown.addItems(formatted_tickers)
        self.ticker_dropdown.currentTextChanged.connect(self.update_plot)

        self.ticker_layout.addWidget(self.label)
        self.ticker_layout.addWidget(self.ticker_dropdown)

        self.year_layout = QHBoxLayout()
        self.start_year_label = QLabel("Start Year:")
        self.start_year_spinbox = QSpinBox(self)
        self.start_year_spinbox.setMinimum(1980)
        self.start_year_spinbox.setMaximum(2024)
        self.start_year_spinbox.setValue(1980)
        self.start_year_spinbox.valueChanged.connect(self.update_plot)

        self.end_year_label = QLabel("End Year:")
        self.end_year_spinbox = QSpinBox(self)
        self.end_year_spinbox.setMinimum(1980)
        self.end_year_spinbox.setMaximum(2024)
        self.end_year_spinbox.setValue(2024)
        self.end_year_spinbox.valueChanged.connect(self.update_plot)

        self.cumulative_gain_label = QLabel("Cumulative Gain: N/A")
        self.year_layout.addWidget(self.start_year_label)
        self.year_layout.addWidget(self.start_year_spinbox)
        self.year_layout.addWidget(self.end_year_label)
        self.year_layout.addWidget(self.end_year_spinbox)
        self.year_layout.addWidget(self.cumulative_gain_label)

        self.plot_canvas = StockPlotCanvas(self, width=8, height=6)
        self.toolbar = NavigationToolbar2QT(self.plot_canvas, self)

        self.layout.addLayout(self.ticker_layout)
        self.layout.addLayout(self.year_layout)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.plot_canvas)
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)
        self.update_plot()

    def update_plot(self):
        selected_text = self.ticker_dropdown.currentText()
        ticker, company_name = selected_text.split(" - ")
        start_year = self.start_year_spinbox.value()
        end_year = self.end_year_spinbox.value()

        self.plot_canvas.plot_stock(ticker, start_year, end_year, company_name)

        cumulative_gain = self.plot_canvas.calculate_cumulative_gain(ticker, start_year, end_year)
        if cumulative_gain is not None:
            self.cumulative_gain_label.setText(f"Cumulative Gain: {cumulative_gain:.2f}%")
        else:
            self.cumulative_gain_label.setText("Cumulative Gain: N/A")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = StockViewerApp()
    viewer.show()
    sys.exit(app.exec())
