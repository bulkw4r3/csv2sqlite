import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import csv
import io
from contextlib import asynccontextmanager

# Funktion zur Initialisierung der Datenbank
def init_db():
    """Datenbank initialisieren und Tabelle erstellen, falls sie nicht existiert"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(TABLE_SCHEMA)
    conn.commit()
    conn.close()

# Lifespan-Kontext-Manager für FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bei Start der Anwendung
    init_db()
    yield
    # Bei Beendigung der Anwendung
    # Hier könnten weitere Aufräumarbeiten erfolgen

# Stellen Sie sicher, dass der Ordner für die Datenbank existiert
DB_PATH = "data/zdexport.db"

# Tabellenschema festlegen - passen Sie dies an Ihr eigenes CSV-Schema an
# Hier ein Beispiel für ein einfaches Schema
TABLE_NAME = "zendesk_export"
TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS zendesk_export (
    sid INTEGER PRIMARY KEY AUTOINCREMENT,
    ID INTEGER,
    Status TEXT,
    Gruppe TEXT,
    Mitarbeiter TEXT,
    Aktualisierungsdatum TEXT,
    Aktualisiert TEXT,
    SLA TEXT,
    Anfragender TEXT,
    Angefragt TEXT,
    Routing TEXT
)
"""

# FastAPI-Anwendung mit Lifespan-Kontext-Manager initialisieren
app = FastAPI(title="CSV zu SQLite Uploader", lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def get_upload_page():
    """Liefert die HTML-Seite für den Upload"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CSV zu SQLite Uploader</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .container {
                border: 1px solid #ddd;
                padding: 20px;
                border-radius: 5px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
            }
            .btn {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            .btn:hover {
                background-color: #45a049;
            }
            .result {
                margin-top: 20px;
                padding: 10px;
                border-left: 3px solid #4CAF50;
                background-color: #f9f9f9;
                display: none;
            }
            .error {
                border-left-color: #f44336;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CSV zu SQLite Uploader</h1>
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="csvFile">CSV-Datei auswählen:</label>
                    <input type="file" id="csvFile" name="file" accept=".csv" required>
                </div>
                <button type="submit" class="btn">Hochladen und Speichern</button>
            </form>
            <div id="result" class="result"></div>
        </div>

        <script>
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData();
                const fileInput = document.getElementById('csvFile');
                formData.append('file', fileInput.files[0]);
                
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'none';
                resultDiv.classList.remove('error');
                
                try {
                    const response = await fetch('/upload/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    resultDiv.textContent = data.message;
                    resultDiv.style.display = 'block';
                    
                    if (!response.ok) {
                        resultDiv.classList.add('error');
                    }
                    
                    if (response.ok) {
                        document.getElementById('uploadForm').reset();
                    }
                } catch (error) {
                    resultDiv.textContent = 'Ein Fehler ist aufgetreten: ' + error.message;
                    resultDiv.style.display = 'block';
                    resultDiv.classList.add('error');
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...)):
    """CSV-Datei hochladen und in SQLite-Datenbank speichern"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Nur CSV-Dateien sind erlaubt")
    
    try:
        # Dateiinhalt einlesen
        contents = await file.read()
        csv_data = io.StringIO(contents.decode('utf-8'))
        csv_reader = csv.reader(csv_data)
        
        # Header-Zeile einlesen
        header = next(csv_reader)
        
        # Verbindung zur Datenbank herstellen
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Daten einfügen
        rows_inserted = 0
        for row in csv_reader:
            # WICHTIG: Passen Sie diesen Teil an Ihr CSV-Schema an
            # Hier wird angenommen, dass die CSV 4 Spalten hat, die den Tabellenspalten entsprechen
            if len(row) != 10:
                continue  # Überspringe ungültige Zeilen
                
            # SQLite-Statement vorbereiten
            # WICHTIG: Passen Sie die Spaltenanzahl an Ihr Schema an
            cursor.execute(
                f"INSERT INTO {TABLE_NAME} (ID, Status, Gruppe, Mitarbeiter, Aktualisierungsdatum, Aktualisiert, SLA, Anfragender, Angefragt, Routing ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (int(row[0]), row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
            )
            rows_inserted += 1
        
        conn.commit()
        conn.close()
        
        return {"message": f"CSV erfolgreich hochgeladen und {rows_inserted} Datensätze in die Datenbank eingefügt!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Verarbeiten der CSV-Datei: {str(e)}")

# Run the app with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)