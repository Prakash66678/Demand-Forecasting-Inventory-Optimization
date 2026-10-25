# DemandPilot AI — Demand Forecasting & Inventory Optimization

An AI-powered analytics dashboard designed to analyze product demand, forecast future sales, monitor inventory, and support data-driven inventory planning.

## 📌 Project Overview

DemandPilot AI combines data analytics, time-series forecasting, and inventory optimization concepts in an interactive dashboard. It helps users explore historical demand patterns, understand future demand, and make better inventory planning decisions.

The project demonstrates practical applications of Python, data science, forecasting, and business intelligence.

## 🎯 Project Objectives

- Analyze historical demand and inventory data.
- Identify trends and patterns in product demand.
- Forecast future demand using time-series forecasting techniques.
- Support inventory planning and stock management.
- Visualize important business metrics through interactive charts.
- Provide an AI-powered chatbot for project-related analytical assistance.
- Enable users to download data and analysis results in Excel format.

## ✨ Key Features

### 1. Demand Analysis
- Explore historical demand data.
- Analyze demand trends and patterns.
- Compare demand across available products and time periods.

### 2. Demand Forecasting
- Analyze time-series demand data.
- Generate demand forecasts using forecasting techniques.
- Visualize historical and forecasted demand.
- Support data-driven demand planning.

### 3. Inventory Optimization
- Explore available inventory information.
- Identify potential inventory shortages and overstocking risks where supported by the data.
- Support inventory planning and replenishment decisions.

### 4. Interactive Dashboard
- Interactive charts and visualizations.
- Data exploration and filtering.
- Clear presentation of analytical results.
- Business-focused insights.

### 5. AI Chatbot
- AI-powered conversational interface.
- Ask questions about demand forecasting and inventory analysis.
- Get assistance interpreting analytical results.

The chatbot requires a valid Gemini API key configured through Streamlit secrets.

### 6. Excel Export
- Download supported analytical data in Excel format.
- Uses `openpyxl` for Excel file handling.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web dashboard |
| Pandas | Data cleaning and manipulation |
| NumPy | Numerical operations |
| Scikit-learn | Machine learning utilities |
| Statsmodels | Statistical and time-series analysis |
| Matplotlib & Seaborn | Data visualization |
| Plotly | Interactive visualizations |
| Google Gemini API | AI chatbot integration |
| OpenPyXL | Excel file handling |
| Git & GitHub | Version control and collaboration |

## 📂 Project Structure

```text
Demand-Forecasting-Inventory-Optimization/
│
├── app.py
├── chatbot.py
├── requirements.txt
├── README.md
│
├── .streamlit/
│   └── secrets.toml
│
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── notebooks/
├── src/
├── tests/
├── reports/
├── .gitignore
└── .venv/
```

*Note: The `.venv/` directory and `secrets.toml` file are local configuration items and should not be committed to GitHub. Folder contents may vary depending on your current project version.*

## ⚙️ Installation and Setup

### Prerequisites

Install the following:

- Python 3.10 or a compatible version supported by the project dependencies
- Git
- A web browser

### Step 1: Clone the repository

Open PowerShell or a terminal and run:

```bash
git clone https://github.com/Prakash66678/Demand-Forecasting-Inventory-Optimization.git
cd Demand-Forecasting-Inventory-Optimization
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure the Gemini API key

Create the following file locally:

`.streamlit/secrets.toml`

Add your API key:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
```

Replace the placeholder with your own Gemini API key.

**Security:** Never publish your API key or commit `secrets.toml` to GitHub. For Streamlit Community Cloud, configure the key in your app's **Settings → Secrets** section.

### Step 5: Run the dashboard

```bash
streamlit run app.py
```

Streamlit will provide a local URL, usually:

`http://localhost:8501`

Open that URL in your browser.

## 📊 How to Use

1. Launch the application.
2. Open the available dashboard sections.
3. Explore the historical demand and inventory data.
4. Review the available forecasts and visualizations.
5. Examine inventory-related insights.
6. Download supported results in Excel format.
7. Use the AI chatbot after configuring the Gemini API key.

Available outputs depend on the dataset and features implemented in the current version.

## 🚀 Deployment

The application can be deployed using Streamlit Community Cloud.

General deployment steps:

1. Push the project to a GitHub repository.
2. Sign in to Streamlit Community Cloud.
3. Create a new app and select the repository.
4. Choose the correct branch and `app.py` as the entry point.
5. Add the required API key under the app's Secrets settings.
6. Deploy and test the public application.

**Live Demo:** Add your deployed Streamlit URL here.

## 🧪 Testing

If automated tests are available in the repository, activate the virtual environment and run:

```bash
python -m pytest -v
```

Check that the dashboard starts successfully and test the main features, including data loading, visualizations, Excel export, and chatbot responses.

## 🔐 Security and Best Practices

- Keep API keys and credentials private.
- Exclude `.venv/`, temporary files, and local secrets from version control.
- Validate datasets before using them for forecasting.
- Evaluate forecasting performance before relying on predictions for business decisions.
- Do not treat forecasts as guaranteed future demand.

## 🔮 Future Enhancements

- Compare multiple forecasting models.
- Add forecasting accuracy metrics such as MAE, RMSE, and MAPE where appropriate.
- Develop automated reorder recommendations.
- Add safety-stock and reorder-point calculations.
- Include supplier performance analysis.
- Add alerts for potential stockouts and excess inventory.
- Improve model monitoring and forecast explainability.

## 🎓 Academic Use

This project demonstrates the application of data analytics, time-series forecasting, inventory management concepts, and interactive dashboards to a practical business problem.

It is intended for educational and analytical purposes. Forecast quality and inventory recommendations depend on data quality, model performance, and business constraints.

## 👨‍💻 Author

**Gnana Prakash S**

B.Tech Information Technology — Final Year

GitHub: [Prakash66678](https://github.com/Prakash66678)

Project Repository: [Demand Forecasting & Inventory Optimization](https://github.com/Prakash66678/Demand-Forecasting-Inventory-Optimization)

---


(https://demandforecastqwe.streamlit.app/)

⭐ If you find this project useful, consider starring the repository on GitHub.
