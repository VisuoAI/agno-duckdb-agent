# interactive_dashboard_agent.py
from agno.agent import Agent
from agno.models.openai import OpenAIChat
import duckdb
import pandas as pd
import plotly.express as px
import sys

def fetch_data():
    """
    Connects DuckDB to BigQuery using the DuckDB BigQuery extension,
    and fetches data from the specified BigQuery table.
    """
    # Load BigQuery extension and attach your BigQuery project.
    duckdb.sql("LOAD 'bigquery';")
    duckdb.sql("ATTACH 'project=my_gcp_project' AS bq (TYPE bigquery, READ_ONLY);")
    
    # Run a sample query – change the dataset/table as needed.
    query = "SELECT * FROM bq.my_dataset.my_table LIMIT 1000"
    df = duckdb.sql(query).to_df()
    return df

def interactive_mapping(df):
    """
    Interactively lists the available columns and asks the user to choose:
      - The column for the X-axis (e.g. category)
      - The column for the Y-axis (e.g. numeric values)
      - The chart type to generate (bar, line, scatter)
    """
    print("\nAvailable columns:")
    for i, col in enumerate(df.columns):
        print(f"{i+1}. {col} (type: {df[col].dtype})")
    
    # Ask user to select the X-axis column
    x_column = input("\nEnter the column name to be used for the X-axis (category): ").strip()
    while x_column not in df.columns:
        print("Column not found. Try again.")
        x_column = input("Enter the column name for X-axis: ").strip()
    
    # Ask user to select the Y-axis column
    y_column = input("Enter the column name to be used for the Y-axis (value): ").strip()
    while y_column not in df.columns:
        print("Column not found. Try again.")
        y_column = input("Enter the column name for Y-axis: ").strip()

    # Ask user for chart type choice
    print("\nChart types available: bar, line, scatter")
    chart_type = input("Enter the chart type you want: ").strip().lower()
    while chart_type not in ['bar', 'line', 'scatter']:
        print("Invalid chart type. Please choose from bar, line, or scatter.")
        chart_type = input("Enter chart type: ").strip().lower()
    
    return x_column, y_column, chart_type

def generate_chart(df, x_column, y_column, chart_type):
    """
    Generates a Plotly chart based on the user's column mappings and selected chart type.
    """
    if chart_type == "bar":
        fig = px.bar(df, x=x_column, y=y_column, title=f"Bar Chart of {y_column} by {x_column}")
    elif chart_type == "line":
        fig = px.line(df, x=x_column, y=y_column, title=f"Line Chart of {y_column} over {x_column}")
    elif chart_type == "scatter":
        fig = px.scatter(df, x=x_column, y=y_column, title=f"Scatter Plot of {y_column} vs {x_column}")
    else:
        print("Unexpected chart type.")
        sys.exit(1)
    return fig

def generate_dashboard_html(fig, mapping_info, output_file="dashboard_improved.html"):
    """
    Generates an HTML dashboard that embeds the interactive Plotly chart
    and displays the mapping information.
    """
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Interactive Analytics Dashboard</title>
      <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
      <style>
         body {{ font-family: Arial, sans-serif; margin: 40px; }}
         h1 {{ color: #333; }}
         .mapping-info {{ margin-bottom: 20px; }}
      </style>
    </head>
    <body>
      <h1>Interactive Analytics Dashboard</h1>
      <div class="mapping-info">
         <h2>Column Mapping</h2>
         <p><strong>X-axis (Category):</strong> {mapping_info['x_column']}</p>
         <p><strong>Y-axis (Value):</strong> {mapping_info['y_column']}</p>
         <p><strong>Chart Type:</strong> {mapping_info['chart_type']}</p>
      </div>
      <div id="chart-div">
         {fig.to_html(full_html=False, include_plotlyjs='cdn')}
      </div>
    </body>
    </html>
    """
    with open(output_file, "w") as f:
        f.write(dashboard_html)
    return output_file

# Define a custom tool that Agno can use to generate the dashboard interactively.
class InteractiveDashboardTool:
    name = "InteractiveDashboardTool"
    description = (
        "This tool connects DuckDB to BigQuery, extracts data, "
        "prompts you to map columns and select a chart type, then generates "
        "an interactive HTML dashboard with an embedded Plotly chart."
    )

    def run(self):
        # Fetch data from BigQuery
        df = fetch_data()
        if df.empty:
            return "No data fetched. Please check your query and credentials."
        
        # Let the user interactively map columns and choose chart type.
        x_column, y_column, chart_type = interactive_mapping(df)
        
        # Generate the chart based on user input.
        fig = generate_chart(df, x_column, y_column, chart_type)
        
        # Collect mapping info for the dashboard.
        mapping_info = {
            "x_column": x_column,
            "y_column": y_column,
            "chart_type": chart_type
        }
        
        # Generate the dashboard HTML.
        output_file = generate_dashboard_html(fig, mapping_info)
        return f"Dashboard generated and saved as {output_file}"

# Initialize the Agno agent with our interactive dashboard tool.
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),  # Use your preferred model
    description=(
        "You are a data analytics agent that connects DuckDB to BigQuery, "
        "extracts data, allows interactive column mapping, and generates an HTML dashboard."
    ),
    tools=[InteractiveDashboardTool()],
    markdown=True
)

# Have the agent execute the tool.
# The agent will call the run() method of InteractiveDashboardTool.
agent.print_response("Generate an interactive dashboard with column mapping.", stream=True)
