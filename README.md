# Pastelaria Mafraria Analytics Dashboard

This project provides an interactive analytics dashboard for "Pastelaria Mafraria," allowing for sales and breakage analysis with per-store data filtering and date range selection. It aims to visualize key business metrics, identify trends, and support data-driven decision-making.

## Features

-   **Interactive Dashboard:** Visualize sales, breakage, average ticket, and waste ratio.
-   **Store-Specific Filtering:** Filter all dashboard metrics by individual store locations (Barreiro, Quinta da Lomba, Pinhal Novo).
-   **Date Range Selection:** Analyze data within custom date ranges, with validation to prevent selecting an end date earlier than the start date.
-   **Comparative Store Analysis:** View sales comparisons across all stores.
-   **Sales by Hour:** Identify peak and off-peak sales hours.
-   **Top Selling Products:** Discover the top 5 most sold products.
-   **Product Profitability:** Analyze product profitability considering sales versus breakage.
-   **Excel Export:** Download comprehensive reports in `.xlsx` format.
-   **SQLite Database:** Efficient and scalable data storage using SQLite, replacing direct Excel file manipulation for better performance and data integrity.
-   **Asynchronous Operations:** Backend API utilizes `aiosqlite` for non-blocking database operations, enhancing responsiveness and performance.

## Technologies Used

-   **Backend:**
    -   **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python 3.7+.
    -   **Python:** The primary programming language.
    -   **SQLite:** A lightweight, file-based relational database for data storage.
    -   **aiosqlite:** Asynchronous wrapper for `sqlite3` to enable non-blocking database interactions.
    -   **Pandas:** Used for data manipulation and Excel export functionality.
-   **Frontend:**
    -   **HTML5:** Structure of the web pages.
    -   **JavaScript:** For dynamic dashboard interactions, API calls, and chart rendering.
    -   **Chart.js:** A flexible JavaScript charting library for creating various types of charts.
    -   **Tailwind CSS:** A utility-first CSS framework for styling the dashboard.

## Setup and Installation

To get this project up and running on your local machine, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd managementcoffee
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    ```

3.  **Activate the virtual environment:**
    -   **Windows:**
        ```bash
        .venv\Scripts\activate
        ```
    -   **macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If `requirements.txt` is not present, you might need to create it by running `pip freeze > requirements.txt` after installing the necessary packages like `fastapi`, `uvicorn`, `pandas`, `openpyxl`, `aiosqlite`)*

5.  **Run the FastAPI application:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The application will typically run on `http://127.0.0.1:8000`.

6.  **Access the Dashboard:**
    Open your web browser and navigate to `http://127.0.0.1:8000/static/index.html`.

## Usage

-   **Select a Store:** Use the dropdown menu in the navigation bar to filter data by "Barreiro," "Quinta da Lomba," or "Pinhal Novo."
-   **Select Date Range:** Use the "Data Início" (Start Date) and "Data Fim" (End Date) input fields to specify the period for analysis. The end date cannot be earlier than the start date.
-   **Update Dashboard:** Click the "Atualizar" (Update) button to refresh all charts and statistics based on your selected filters.
-   **Download Excel:** Click the "Baixar Excel (.xlsx)" button to download a detailed Excel report for the selected date range.

## Project Structure

```
.
├── app/
│   ├── main.py                 # FastAPI application entry point and API routes
│   ├── models/
│   │   └── models.py           # Pydantic models for data validation
│   ├── services/
│   │   └── excel_manager.py    # Handles data storage (SQLite) and Excel export logic
│   └── static/
│       ├── index.html          # Main dashboard frontend HTML
│       └── js/
│           └── dashboard.js    # JavaScript for dashboard interactivity and chart rendering
├── README.md                   # Project README file
└── requirements.txt            # Python dependencies
```
