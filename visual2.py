import sys
import mplcursors
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QMainWindow, QComboBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

# Define the ticker to company name mapping
ticker_company_map = {
    "AAPL": "Apple", "ABBV": "AbbVie", "AVGO": "Broadcom", "BAC": "Bank of America",
    "BRK.A": "Berkshire Hathaway A", "BRK.B": "Berkshire Hathaway B", "COST": "Costco",
    "GOOGL": "Alphabet", "HD": "Home Depot", "JNJ": "Johnson & Johnson", "JPM": "JPMorgan Chase",
    "LLY": "Eli Lilly", "MA": "MasterCard", "META": "Meta Platforms", "MSFT": "Microsoft",
    "NFLX": "Netflix", "NVDA": "NVIDIA", "ORCL": "Oracle", "PG": "Procter & Gamble",
    "TSLA": "Tesla", "UNH": "UnitedHealth", "V": "Visa", "WMT": "Walmart", "XOM": "ExxonMobil"
}

# Define a dictionary to store DataFrames for each stock
stock_data = {}

stock_metadata = pd.read_excel("CS 439 final project data/top_25_us_stocks.xlsx")

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
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        fig = plt.figure(figsize=(width, height), dpi=dpi)
        self.ax = fig.add_subplot(111)
        fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)
        super().__init__(fig)
        self.setParent(parent)
        self.price_cursors = None
        self.line_data = {}

    def plot_stocks(self, tickers, start_year=None, end_year=None):
        self.ax.clear()
        self.line_data.clear()

        # Safely remove existing cursors
        if self.price_cursors and hasattr(self.price_cursors, 'selections'):
            for selector in self.price_cursors.selections:
                selector.annotation.remove()
            self.price_cursors = None

        data_plotted = False
        lines = []

        for ticker in tickers:
            if ticker in stock_data:
                df = stock_data[ticker]
                selected_data = df[(df['date'].dt.year >= start_year) & (df['date'].dt.year <= end_year)]
                if not selected_data.empty:
                    data_plotted = True
                    line, = self.ax.plot(selected_data['date'], selected_data['close'], label=ticker)

                    initial_price = selected_data['close'].iloc[0]
                    final_price = selected_data['close'].iloc[-1]
                    cumulative_return = (final_price - initial_price) / initial_price * 100

                    # Calculate highest and lowest price info
                    min_price = selected_data['close'].min()
                    max_price = selected_data['close'].max()
                    min_date = selected_data[selected_data['close'] == min_price]['date'].iloc[0]
                    max_date = selected_data[selected_data['close'] == max_price]['date'].iloc[0]
                    potential_gain = (max_price - min_price) / min_price * 100

                    self.line_data[line] = {
                        'ticker': ticker,
                        'company_name': ticker_company_map.get(ticker, ticker),  # Get company name or use ticker if not found
                        'data': selected_data,
                        'cumulative_return': cumulative_return,
                        'min_price': min_price,
                        'max_price': max_price,
                        'min_date': min_date,
                        'max_date': max_date,
                        'potential_gain': potential_gain
                    }

                    lines.append(line)

        if data_plotted:
            self.price_cursors = mplcursors.cursor(
                lines,
                hover=True,
                highlight=True,
                annotation_kwargs={'bbox': dict(fc="yellow", alpha=0.8)}
            )

            @self.price_cursors.connect("add")
            def on_add(sel):
                line = sel.artist
                if line in self.line_data:
                    data = self.line_data[line]
                    date = mdates.num2date(sel.target[0])
                    price = sel.target[1]
                    sel.annotation.set_text(
                        f'{data["ticker"]} - {data["company_name"]}\n'  # Added company name here
                        f'Date: {date.strftime("%Y-%m-%d")}\n'
                        f'Price: ${price:.2f}\n'
                        f'Cumulative Return: {data["cumulative_return"]:.2f}%\n'
                        f'Lowest Price: ${data["min_price"]:.2f} on {data["min_date"].strftime("%Y-%m-%d")}\n'
                        f'Highest Price: ${data["max_price"]:.2f} on {data["max_date"].strftime("%Y-%m-%d")}\n'
                        f'Potential Gain: {data["potential_gain"]:.2f}% if bought low & sold high'
                    )

            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Closing Price")
            self.ax.set_title("Closing Prices for Selected Stocks")
            self.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        else:
            self.ax.set_title("No data available for selected criteria")

        self.draw()

# Rest of the code remains the same...
class StockViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main widget and layout
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)

        # Filter layouts
        self.filter_layout = QHBoxLayout()
        self.ticker_layout = QHBoxLayout()
        self.year_layout = QHBoxLayout()
        self.setMinimumSize(1000, 800)

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

        # Labels
        self.filter_layout.addWidget(QLabel("Sector:"))
        self.filter_layout.addWidget(self.sector_dropdown)
        self.filter_layout.addWidget(QLabel("State:"))
        self.filter_layout.addWidget(self.state_dropdown)
        self.filter_layout.addWidget(QLabel("Location:"))
        self.filter_layout.addWidget(self.location_dropdown)

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

        # Connect dropdown changes to plot update
        self.sector_dropdown.currentTextChanged.connect(self.update_plot)
        self.state_dropdown.currentTextChanged.connect(self.update_plot)
        self.location_dropdown.currentTextChanged.connect(self.update_plot)
        self.start_year_spinbox.valueChanged.connect(self.update_plot)
        self.end_year_spinbox.valueChanged.connect(self.update_plot)

        # Matplotlib canvas and toolbar
        self.plot_canvas = StockPlotCanvas(self, width=10, height=8)
        self.toolbar = NavigationToolbar2QT(self.plot_canvas, self)

        # Add layouts and widgets to the main layout
        self.layout.addLayout(self.filter_layout)
        self.layout.addLayout(self.year_layout)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.plot_canvas)
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

        # Initial plot
        self.update_plot()

    def get_filtered_tickers(self):
        # Filter tickers based on dropdown selections
        filtered_data = stock_metadata
        if self.sector_dropdown.currentText() != "All":
            filtered_data = filtered_data[filtered_data['Sector'] == self.sector_dropdown.currentText()]
        if self.state_dropdown.currentText() != "All":
            filtered_data = filtered_data[filtered_data['Headquarters State'] == self.state_dropdown.currentText()]
        if self.location_dropdown.currentText() != "All":
            filtered_data = filtered_data[
                filtered_data['Headquarters Location'] == self.location_dropdown.currentText()]

        return filtered_data['Ticker'].tolist()

    def update_plot(self):
        start_year = self.start_year_spinbox.value()
        end_year = self.end_year_spinbox.value()
        tickers = self.get_filtered_tickers()
        self.plot_canvas.plot_stocks(tickers, start_year, end_year)


def main():
    app = QApplication(sys.argv)
    viewer = StockViewerApp()
    viewer.setWindowTitle("Stock Viewer with Filtering")
    viewer.resize(800, 600)
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
