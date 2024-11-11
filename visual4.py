import sys
import mplcursors
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QSizePolicy, QComboBox)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
import numpy as np
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle

# Dictionary to store DataFrames for each stock
stock_data = {}


def load_market_events(excel_path):
    try:
        events_df = pd.read_excel(excel_path, sheet_name='Sheet1')
        events_df['Start Date'] = pd.to_datetime(events_df['Start Date'])
        events_df['End Date'] = pd.to_datetime(events_df['End Date'])
        return events_df
    except Exception as e:
        print(f"Error loading market events: {e}")
        return pd.DataFrame()


# Load market events from Excel
market_events = load_market_events('CS 439 final project data/stock_market_events_with_dates.xlsx')

# List of stock tickers and CSV file paths
tickers = ["AAPL", "ABBV", "AVGO", "BAC", "BRK.A", "BRK.B", "COST", "GOOGL", "HD",
           "JNJ", "JPM", "LLY", "MA", "META", "MSFT", "NFLX", "NVDA", "ORCL",
           "PG", "TSLA", "UNH", "V", "WMT", "XOM"]
file_paths = [f"CS 439 final project data/MacroTrends_Data_Download_{ticker}.csv" for ticker in tickers]

# Load each CSV file into DataFrames
for ticker, file_path in zip(tickers, file_paths):
    try:
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        stock_data[ticker] = df
    except Exception as e:
        print(f"Error loading data for {ticker}: {e}")


class StockPlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Create figure with space for summary table
        fig = plt.figure(figsize=(width, height + 2), dpi=dpi)  # Added height for table

        # Create gridspec to manage subplots
        gs = fig.add_gridspec(2, 1, height_ratios=[4, 1])

        # Create main plot and table axes
        self.ax = fig.add_subplot(gs[0])
        self.table_ax = fig.add_subplot(gs[1])
        self.table_ax.axis('off')  # Hide table axes

        fig.subplots_adjust(top=0.85, bottom=0.15, hspace=0.3)
        super().__init__(fig)
        self.setParent(parent)
        self.cursors = []

    def calculate_event_impact(self, ticker, event_data, df):
        """Calculate percentage change during event period"""
        start_date = event_data['Start Date']
        end_date = event_data['End Date']

        # For single-day events, look at the change on that day
        if start_date == end_date:
            # Look at the next day's closing price for single-day events
            start_date = start_date - pd.Timedelta(days=1)
            end_date = end_date + pd.Timedelta(days=1)

        # Filter data for event period
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        event_data = df[mask]

        if len(event_data) < 2:
            return "N/A"

        start_price = event_data['close'].iloc[0]
        end_price = event_data['close'].iloc[-1]

        pct_change = ((end_price - start_price) / start_price) * 100
        return f"{pct_change:.2f}%"

    def create_impact_table(self, selected_tickers, selected_events):
        """Create a table showing the impact of each event on selected stocks"""
        # Create data for table
        table_data = []
        header = ['Event'] + selected_tickers

        # Calculate impact for each event
        for event in selected_events:
            event_data = market_events[market_events['Event'] == event].iloc[0]
            row = [event]

            for ticker in selected_tickers:
                if ticker in stock_data:
                    df = stock_data[ticker]
                    impact = self.calculate_event_impact(ticker, event_data, df)
                    row.append(impact)
                else:
                    row.append("N/A")

            table_data.append(row)

        # Clear previous table
        self.table_ax.clear()
        self.table_ax.axis('off')

        # Create table
        table = self.table_ax.table(
            cellText=table_data,
            colLabels=header,
            loc='center',
            cellLoc='center',
            bbox=[0, 0, 1, 1]
        )

        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        for cell in table._cells:
            table._cells[cell].set_height(0.1)
            # Make header cells bold
            if cell[0] == 0:
                table._cells[cell].set_text_props(weight='bold')
            # Color negative changes red and positive changes green
            elif cell[1] > 0:  # Skip event name column
                text = table._cells[cell].get_text().get_text()
                if text != "N/A":
                    value = float(text.strip('%'))
                    if value < 0:
                        table._cells[cell].set_facecolor('#ffcccc')  # Light red
                    elif value > 0:
                        table._cells[cell].set_facecolor('#ccffcc')  # Light green

        # Adjust column widths
        table.auto_set_column_width(range(len(header)))

    def plot_stocks(self, selected_tickers, selected_events):
        self.ax.clear()
        self.cursors = []

        if not selected_tickers:
            self.ax.text(0.5, 0.5,
                         "Please select one or more stocks",
                         horizontalalignment='center',
                         verticalalignment='center')
            self.draw()
            return

        # Get the overall date range for all selected events
        event_start_date, event_end_date = self.get_date_range(selected_events)

        # Find the earliest available data point among selected stocks
        earliest_stock_date = None
        for ticker in selected_tickers:
            if ticker in stock_data:
                stock_date = stock_data[ticker]['date'].min()
                if earliest_stock_date is None or stock_date < earliest_stock_date:
                    earliest_stock_date = stock_date

        # Use the later of event start date and earliest stock date
        effective_start_date = max(event_start_date, earliest_stock_date) if earliest_stock_date else event_start_date

        # Track if we successfully plotted any data
        plotted_any_data = False

        # Create a color map for the stocks
        colors = plt.cm.tab20(np.linspace(0, 1, len(selected_tickers)))

        # Plot stock data
        for idx, ticker in enumerate(selected_tickers):
            if ticker in stock_data:
                df = stock_data[ticker].copy()

                # Filter data based on date range
                if effective_start_date and event_end_date:
                    mask = (df['date'] >= effective_start_date) & (df['date'] <= event_end_date)
                    df = df[mask]

                if df.empty:
                    print(f"No data available for {ticker} in the selected date range")
                    continue

                try:
                    # Normalize prices to percentage change from first day
                    first_price = df['close'].iloc[0]
                    if pd.isna(first_price):
                        print(f"Invalid first price for {ticker}")
                        continue

                    normalized_prices = ((df['close'] - first_price) / first_price) * 100

                    line, = self.ax.plot(df['date'], normalized_prices,
                                         label=ticker,
                                         color=colors[idx])
                    cursor = mplcursors.cursor(line, hover=True)
                    self.cursors.append(cursor)
                    plotted_any_data = True

                    @cursor.connect("add")
                    def on_add(sel):
                        date = mdates.num2date(sel.target[0])
                        change = sel.target[1]
                        sel.annotation.set_text(
                            f'{sel.artist.get_label()}\n'
                            f'Date: {date.strftime("%Y-%m-%d")}\n'
                            f'Change: {change:.2f}%'
                        )
                        sel.annotation.get_bbox_patch().set(fc="yellow", alpha=0.8)
                except Exception as e:
                    print(f"Error plotting {ticker}: {str(e)}")
                    continue

        # Only proceed with event highlighting if we plotted any data
        if plotted_any_data and selected_events:
            ymin, ymax = self.ax.get_ylim()

            # Sort events by start date to handle label positioning
            event_positions = []
            for event in selected_events:
                event_data = market_events[market_events['Event'] == event].iloc[0]
                event_positions.append((event_data['Start Date'], event))
            event_positions.sort()  # Sort by start date

            # Calculate label heights to avoid overlap
            label_heights = []
            current_height = 1.0  # Start at the top
            min_gap = 0.05  # Minimum gap between labels

            for start_date, event in event_positions:
                try:
                    event_data = market_events[market_events['Event'] == event].iloc[0]
                    highlight_start = event_data['Start Date']
                    highlight_end = event_data['End Date']

                    # Check if it's a single-day event
                    is_single_day = highlight_start == highlight_end

                    # For single-day events, make the highlight visible but narrow
                    if is_single_day:
                        highlight_end += pd.Timedelta(days=1)

                    # Adjust highlight start date if it's before the earliest stock data
                    adjusted_highlight_start = max(highlight_start, effective_start_date)

                    # Convert dates to matplotlib format for Rectangle
                    highlight_start_ord = mdates.date2num(adjusted_highlight_start)
                    highlight_end_ord = mdates.date2num(highlight_end)

                    # Only create rectangle and label if the event overlaps with the visible range
                    if highlight_end >= effective_start_date:
                        if is_single_day:
                            # For single-day events, use a darker red vertical line
                            self.ax.axvline(x=highlight_start_ord,
                                            color='darkred',
                                            alpha=0.5,
                                            linewidth=2,
                                            linestyle='--',
                                            label=event)
                        else:
                            # For period events, use the regular rectangle
                            rect = Rectangle((highlight_start_ord, ymin),
                                             highlight_end_ord - highlight_start_ord,
                                             ymax - ymin,
                                             facecolor='red',
                                             alpha=0.1,
                                             label=event)
                            self.ax.add_patch(rect)

                        # Find appropriate label height
                        while any(abs(h - current_height) < min_gap for h in label_heights):
                            current_height -= min_gap

                        # Add event label at the adjusted position with staggered heights
                        self.ax.text(highlight_start_ord, ymax * current_height,
                                     event,
                                     rotation=45,
                                     verticalalignment='bottom',
                                     horizontalalignment='left',
                                     fontsize=8)

                        label_heights.append(current_height)
                        current_height -= min_gap  # Prepare for next label

                except Exception as e:
                    print(f"Error highlighting event {event}: {str(e)}")
                    continue

        if plotted_any_data:
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Percentage Change (%)")
            # Position title higher and make it bold
            self.ax.set_title("Stock Price Changes During Market Events",
                              pad=50,  # Increase padding above plot
                              fontweight='bold',
                              fontsize=12)
            self.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            self.ax.grid(True, alpha=0.3)

            # Create impact summary table
            self.create_impact_table(selected_tickers, selected_events)

            plt.tight_layout()
        else:
            self.ax.text(0.5, 0.5,
                         "No data available for the selected stocks and date range",
                         horizontalalignment='center',
                         verticalalignment='center')

        self.draw()

    def get_date_range(self, selected_events):
        if not selected_events:
            # Default to showing all data if no events selected
            all_dates = []
            for df in stock_data.values():
                all_dates.extend([df['date'].min(), df['date'].max()])
            return min(all_dates), max(all_dates)

        start_dates = []
        end_dates = []

        for event in selected_events:
            event_data = market_events[market_events['Event'] == event].iloc[0]
            start_date = event_data['Start Date']
            end_date = event_data['End Date']

            # For single-day events, extend by 3 weeks
            if start_date == end_date:
                start_date -= pd.Timedelta(weeks=3)
                end_date += pd.Timedelta(weeks=3)

            start_dates.append(start_date)
            end_dates.append(end_date)

        return min(start_dates), max(end_dates)


class StockViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Stock Market Event Analyzer")
        self.main_widget = QWidget(self)

        # Create main horizontal layout
        self.main_layout = QHBoxLayout(self.main_widget)

        # Left side for plot
        self.plot_layout = QVBoxLayout()

        # Plot canvas
        self.plot_canvas = StockPlotCanvas(self, width=12, height=6)
        self.toolbar = NavigationToolbar2QT(self.plot_canvas, self)

        # Add plot widgets to left layout
        self.plot_layout.addWidget(self.toolbar)
        self.plot_layout.addWidget(self.plot_canvas)

        # Right side for controls
        self.controls_layout = QVBoxLayout()
        self.controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Stock selection
        self.ticker_label = QLabel("Select Stocks:")
        self.ticker_combo = QComboBox()
        self.ticker_combo.addItems(['Select stocks...'] + sorted(tickers))
        self.ticker_combo.setCurrentText('Select stocks...')
        self.selected_tickers_label = QLabel("Selected stocks:")
        self.selected_tickers = QLabel("")
        self.ticker_combo.currentTextChanged.connect(self.add_ticker)

        # Event selection
        self.event_label = QLabel("Select Events:")
        self.event_combo = QComboBox()
        self.event_combo.addItems(['Select events...'] + market_events['Event'].tolist())
        self.event_combo.setCurrentText('Select events...')
        self.selected_events_label = QLabel("Selected events:")
        self.selected_events = QLabel("")
        self.event_combo.currentTextChanged.connect(self.add_event)

        # Store selections
        self.selected_ticker_list = []
        self.selected_event_list = []

        # Add widgets to controls layout
        controls_widgets = [
            self.ticker_label, self.ticker_combo,
            self.selected_tickers_label, self.selected_tickers,
            self.event_label, self.event_combo,
            self.selected_events_label, self.selected_events
        ]

        for widget in controls_widgets:
            self.controls_layout.addWidget(widget)
            if isinstance(widget, QLabel):
                widget.setWordWrap(True)
                widget.setMaximumWidth(200)

        # Set fixed width for combos
        self.ticker_combo.setFixedWidth(200)
        self.event_combo.setFixedWidth(200)

        # Add layouts to main layout
        self.main_layout.addLayout(self.plot_layout, stretch=4)
        self.main_layout.addLayout(self.controls_layout, stretch=1)

        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        self.resize(1600, 800)  # Wider window

    def add_ticker(self, ticker):
        if ticker != 'Select stocks...':
            if ticker not in self.selected_ticker_list:
                self.selected_ticker_list.append(ticker)
                self.selected_tickers.setText('\n'.join(self.selected_ticker_list))
                self.update_plot()
            self.ticker_combo.setCurrentText('Select stocks...')

    def add_event(self, event):
        if event != 'Select events...':
            if event not in self.selected_event_list:
                self.selected_event_list.append(event)
                self.selected_events.setText('\n'.join(self.selected_event_list))
                self.update_plot()
            self.event_combo.setCurrentText('Select events...')

    def update_plot(self):
        try:
            self.plot_canvas.plot_stocks(self.selected_ticker_list, self.selected_event_list)
        except Exception as e:
            print(f"Error updating plot: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = StockViewerApp()
    viewer.show()
    sys.exit(app.exec())