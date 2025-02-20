# app.py
from flask import Flask, render_template, request, jsonify
import sqlanydb
import os

app = Flask(__name__)

# Database connection parameters
DB_CONFIG = {
    "userid": "supervisortopuid",
    "password": "thisisthetopuserlevelpwd",
    "host": "103.118.151.42",
    "dbn": "gm2024"
}


def get_db_connection():
    """Establish connection to SQL Anywhere database"""
    try:
        conn = sqlanydb.connect(
            userid=DB_CONFIG["userid"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            dbn=DB_CONFIG["dbn"]
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/sales')
def sales():
    """Display full sales details"""
    try:
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return render_template('error.html', error="Failed to connect to database")

        # Execute query to get all sales data
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM salesm")

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        # Fetch all results
        results = cursor.fetchall()

        # Convert results to list of dicts
        sales_data = []
        for row in results:
            sales_data.append(dict(zip(columns, row)))

        # Close connection
        cursor.close()
        conn.close()

        return render_template('sales.html', columns=columns, sales_data=sales_data)

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/fetch-data', methods=['POST'])
def fetch_data():
    """API endpoint to fetch data from the database"""
    try:
        # Get query from request
        data = request.get_json()
        query = data.get('query', 'SELECT * FROM salesm LIMIT 100')

        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Failed to connect to database"}), 500

        # Execute query
        cursor = conn.cursor()
        cursor.execute(query)

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        # Fetch results
        results = cursor.fetchall()

        # Convert results to list of dicts
        formatted_results = []
        for row in results:
            formatted_results.append(dict(zip(columns, row)))

        # Close connection
        cursor.close()
        conn.close()

        return jsonify({
            "columns": columns,
            "data": formatted_results
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/tables')
def get_tables():
    """Get list of tables in the database"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Failed to connect to database"}), 500

        cursor = conn.cursor()
        # SQL Anywhere syntax for getting tables
        cursor.execute("SELECT table_name FROM sys.systable WHERE table_type = 'BASE'")

        tables = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({"tables": tables})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')

    # Write the template files with explicit encoding
    # Index template
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Anywhere Data Viewer</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .container { max-width: 1200px; margin-top: 30px; }
        #results-container { margin-top: 20px; overflow-x: auto; }
        #loading { display: none; margin-top: 10px; }
        .query-container { position: relative; }
        .query-editor { width: 100%; height: 100px; padding: 10px; font-family: monospace; }
        .table-list { max-height: 300px; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">SQL Anywhere Data Viewer</h1>

        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <a href="/" class="btn btn-outline-primary">Home</a>
                <a href="/sales" class="btn btn-outline-success">View All Sales</a>
            </div>
        </div>

        <div class="row">
            <div class="col-md-3">
                <div class="card">
                    <div class="card-header">Tables</div>
                    <div class="card-body table-list" id="tables-list">
                        <div class="d-flex justify-content-center">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-9">
                <div class="card mb-4">
                    <div class="card-header">SQL Query</div>
                    <div class="card-body">
                        <div class="query-container">
                            <textarea id="query-input" class="query-editor form-control">SELECT * FROM salesm LIMIT 100</textarea>
                        </div>
                        <div class="mt-3">
                            <button id="execute-btn" class="btn btn-primary">Execute Query</button>
                            <div id="loading" class="spinner-border spinner-border-sm text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="error-alert" class="alert alert-danger" style="display: none;"></div>

                <div id="results-container" class="card">
                    <div class="card-header">Results</div>
                    <div class="card-body">
                        <div id="results-table" class="table-responsive">
                            <p class="text-muted">Execute a query to see results</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Load tables on page load
            fetchTables();

            // Set up event listener for execute button
            document.getElementById('execute-btn').addEventListener('click', executeQuery);
        });

        function fetchTables() {
            fetch('/tables')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showError(data.error);
                        return;
                    }

                    const tablesList = document.getElementById('tables-list');
                    tablesList.innerHTML = '';

                    if (data.tables && data.tables.length > 0) {
                        const ul = document.createElement('ul');
                        ul.className = 'list-group';

                        data.tables.forEach(table => {
                            const li = document.createElement('li');
                            li.className = 'list-group-item';
                            li.textContent = table;
                            li.style.cursor = 'pointer';
                            li.addEventListener('click', () => {
                                document.getElementById('query-input').value = `SELECT * FROM ${table} LIMIT 100`;
                            });
                            ul.appendChild(li);
                        });

                        tablesList.appendChild(ul);
                    } else {
                        tablesList.innerHTML = '<p class="text-muted">No tables found</p>';
                    }
                })
                .catch(error => {
                    showError('Failed to fetch tables: ' + error.message);
                });
        }

        function executeQuery() {
            const query = document.getElementById('query-input').value.trim();
            if (!query) {
                showError('Please enter a SQL query');
                return;
            }

            // Show loading indicator
            document.getElementById('loading').style.display = 'inline-block';
            document.getElementById('error-alert').style.display = 'none';

            // Send query to server
            fetch('/fetch-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading indicator
                document.getElementById('loading').style.display = 'none';

                if (data.error) {
                    showError(data.error);
                    return;
                }

                displayResults(data);
            })
            .catch(error => {
                document.getElementById('loading').style.display = 'none';
                showError('Error executing query: ' + error.message);
            });
        }

        function displayResults(data) {
            const resultsTable = document.getElementById('results-table');

            if (!data.columns || data.columns.length === 0) {
                resultsTable.innerHTML = '<p class="text-muted">Query executed successfully but no results returned</p>';
                return;
            }

            // Create table
            let tableHtml = '<table class="table table-striped table-hover"><thead><tr>';

            // Add headers
            data.columns.forEach(column => {
                tableHtml += `<th>${column}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';

            // Add rows
            if (data.data && data.data.length > 0) {
                data.data.forEach(row => {
                    tableHtml += '<tr>';
                    data.columns.forEach(column => {
                        let cellValue = row[column];
                        if (cellValue === null) cellValue = '<em>NULL</em>';
                        tableHtml += `<td>${cellValue}</td>`;
                    });
                    tableHtml += '</tr>';
                });
            } else {
                tableHtml += `<tr><td colspan="${data.columns.length}" class="text-center">No data found</td></tr>`;
            }

            tableHtml += '</tbody></table>';

            // Add row count
            const rowCount = data.data ? data.data.length : 0;
            tableHtml += `<p class="text-muted">Showing ${rowCount} row(s)</p>`;

            resultsTable.innerHTML = tableHtml;
        }

        function showError(message) {
            const errorAlert = document.getElementById('error-alert');
            errorAlert.textContent = message;
            errorAlert.style.display = 'block';
        }
    </script>
</body>
</html>
        """)

    # Sales template
    with open('templates/sales.html', 'w', encoding='utf-8') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Data - Full Details</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/datatables.net-bs5@1.13.1/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <style>
        .container { max-width: 1400px; margin-top: 30px; }
        .sales-table-container { overflow-x: auto; }
        .btn-back { margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">Sales Data - Full Details</h1>

        <div class="mb-4">
            <a href="/" class="btn btn-primary btn-back">Back to Query Tool</a>
        </div>

        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span>Complete Sales Records</span>
                <div>
                    <button id="btn-export-csv" class="btn btn-sm btn-outline-secondary">Export CSV</button>
                    <button id="btn-print" class="btn btn-sm btn-outline-secondary ms-2">Print</button>
                </div>
            </div>
            <div class="card-body sales-table-container">
                {% if sales_data %}
                    <table id="sales-table" class="table table-striped table-bordered">
                        <thead>
                            <tr>
                                {% for column in columns %}
                                <th>{{ column }}</th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in sales_data %}
                            <tr>
                                {% for column in columns %}
                                <td>{{ row[column] if row[column] is not none else '' }}</td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                {% else %}
                    <p class="text-center">No sales data found</p>
                {% endif %}
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.1/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.1/js/dataTables.bootstrap5.min.js"></script>
    <script>
        $(document).ready(function() {
            // Initialize DataTable with features
            const salesTable = $('#sales-table').DataTable({
                pageLength: 25,
                lengthMenu: [10, 25, 50, 100, 250, 500],
                order: [],
                responsive: true,
                dom: 'Bfrtilp',
                language: {
                    search: "Filter records:"
                }
            });

            // Export to CSV
            $('#btn-export-csv').click(function() {
                const csvContent = [];

                // Add header row
                const headerRow = [];
                $('#sales-table thead th').each(function() {
                    headerRow.push($(this).text());
                });
                csvContent.push(headerRow.join(','));

                // Add data rows (get all rows, not just visible ones)
                salesTable.rows().every(function() {
                    const rowData = this.data();
                    const csvRow = [];
                    rowData.forEach(cell => {
                        // Handle commas and quotes in CSV
                        if (cell === null || cell === undefined) {
                            csvRow.push('');
                        } else {
                            const cellStr = String(cell);
                            if (cellStr.includes(',') || cellStr.includes('"')) {
                                csvRow.push(`"${cellStr.replace(/"/g, '""')}"`);
                            } else {
                                csvRow.push(cellStr);
                            }
                        }
                    });
                    csvContent.push(csvRow.join(','));
                });

                // Create and download CSV file
                const csvString = csvContent.join('\\n');
                const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', 'sales_data.csv');
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });

            // Print function
            $('#btn-print').click(function() {
                window.print();
            });
        });
    </script>
</body>
</html>
        """)

    # Error template
    with open('templates/error.html', 'w', encoding='utf-8') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .error-container {
            max-width: 600px;
            margin: 100px auto;
            text-align: center;
        }
        .error-icon {
            font-size: 64px;
            color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="error-container">
            <div class="error-icon">⚠️</div>
            <h1 class="mt-4">Error</h1>
            <div class="alert alert-danger mt-4">
                {{ error }}
            </div>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
    </div>
</body>
</html>
        """)

    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
