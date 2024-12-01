# Stock Performance Visualization of Fortune 25 Companies

## Project Overview
This project analyzes and visualizes the stock performance of the top 25 companies by market capitalization from 1980 to the present. By leveraging interactive visualizations, it explores historical trends and the impact of major financial events on stock prices. The project aims to provide insights for investors, analysts, and researchers interested in market dynamics.

---

## Key Objectives
1. **Analyze Cumulative Returns**: Examine long-term growth and trends across sectors, regions, and market caps.
2. **Assess Historical Event Impacts**: Study how financial events such as the 2008 crisis and COVID-19 pandemic influenced stocks.
3. **Identify Sectoral and Geographical Patterns**: Highlight performance differences based on industry and company headquarters.

---

## Visualizations

### 1. **Cumulative Returns Visualization (Visual1.py)**
- **Description**: This visualization shows cumulative stock gains over a selected timeframe. Users can filter by ticker, start year, and end year. Background highlights display major financial events, with tooltips providing details about the events and stock prices.
- **Features**: 
  - Adjustable date ranges.
  - Tooltips with event descriptions and stock data (price, date, percentage gain).
  - Differentiated line colors for periods within and outside the selected timeframe.
- **Demonstration**: For example, selecting Apple Inc., a start year of 2000, and an end year of 2020 highlights the cumulative returns and overlays major events like the 2008 financial crash.
- **Preview**:
  ![Cumulative Returns](path/to/cumulative_returns_image.png)

### 2. **Filtered Stock Line Graph (Visual2.py)**
- **Description**: Displays stock price trends for all companies with filtering options for sector, state, and region (East Coast, West Coast, Midwest, South). The graph dynamically adjusts to the selected start and end years.
- **Features**: 
  - Tooltips showing ticker, date, price, cumulative gain, lowest/highest points, and potential gains.
  - Widgets for sector and location-based filtering.
- **Demonstration**: Selecting the technology sector for 2010-2020 dynamically updates the graph, showing performance trends for tech companies.
- **Preview**:
  ![Stock Line Graph](path/to/stock_line_graph_image.png)

### 3. **Yearly Cumulative Gains Bar Chart (Visual3.py)**
- **Description**: Presents yearly cumulative gains for selected companies. Users can filter by sector, state, region, and market capitalization range.
- **Features**: 
  - Adjustable filters for minimum and maximum market caps.
  - Tooltips with yearly gain, cumulative return, and company details.
- **Demonstration**: Filtering for companies headquartered in California with a market cap above $100 billion highlights their yearly gains.
- **Preview**:
  ![Yearly Gains Bar Chart](path/to/yearly_gains_chart_image.png)

### 4. **Event Impact and Stock Comparison Table (Visual4.py)**
- **Description**: Combines stock performance during specific events with a comparative table. Users select stocks and events to generate a graph and a table summarizing the impact of events on stock prices.
- **Features**:
  - Visualizes stock trends during events.
  - Tabular data showing percentage changes in stock prices for each event.
- **Demonstration**: Selecting Tesla Inc. and Apple Inc. and the COVID-19 pandemic and 2008 Financial Crisis shows the stock trend overlayed with the event period and a table summarizing price changes during that time.
- **Preview**:
  ![Event Impact Table](path/to/event_impact_table_image.png)

---

## Data Processing
- **Data Cleaning**: Removed extraneous text and converted date strings into datetime format.
- **Data Transformation**: Calculated metrics like cumulative returns and percentage price changes.
- **Optional Enhancements**: Created supplementary files with company details (ticker, name, sector, location) and major financial events (name, start date, end date).

---

## Tools and Technologies
- **Programming Languages**: Python
- **Libraries**: Plotly, Matplotlib, Tkinter
- **Data Source**: [MacroTrends](https://www.macrotrends.net/stocks/research)

---

## Repository Structure
- `/data`: Contains raw and processed data files.
- `/images`: Includes visualization previews for the README.

---

## Usage Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/shatakshishelar/StockMarketHistoricalAnalysis.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run different visualizations one by one:
   ```bash
   python visual1.py
   python visual2.py
   python visual3.py
   python visual4.py
   ```

---

## Contact
For questions or suggestions, feel free to reach out via [email](mailto:shatakshi1010@gmail.com) or open an issue in this repository.
Alternative email: shatakshelar@gmail.com
[LinkedIn](https://www.linkedin.com/in/shatakshi-shelar-372b94203/))

