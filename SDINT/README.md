
github : https://github.com/Saiprakash-git/AI_SD_INT

# SDINT: Social Data Intelligence Platform

SDINT is an advanced, production-ready OSINT (Open Source Intelligence) and Social Data Analytics platform. It analyzes social media trends, computes echo chambers, traces digital footprints using NLP and Facial Recognition, and builds corroborated intelligence dossiers.

## Prerequisites
- **Python 3.10+** (Required for the Flask backend, SpaCy NLP, and InsightFace models)
- **Node.js 18+** (Required for the React frontend)
- **MongoDB** (Local instance or Atlas cluster running on the default port `27017`)

## How to Run (1-Click Execution)

For Windows users, we have provided an executable batch script:
1. Double-click the **`run_sdint.bat`** file located in the root directory.
2. The script will automatically:
   - Check if Python and Node.js are installed.
   - Install backend dependencies and download the necessary AI models (`en_core_web_sm`).
   - Launch the Backend server in a new window (`http://localhost:5000`).
   - Install frontend dependencies and launch the Frontend server in a new window (`http://localhost:5173`).

## Manual Execution Steps

If you prefer to run the application manually or are on a non-Windows OS, follow these steps:

### 1. Start the Backend
```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Download the required NLP model
python -m spacy download en_core_web_sm

# Run the Flask server
python app.py
```
*The backend will run at `http://localhost:5000`.*

### 2. Start the Frontend
```bash
# Open a new terminal and navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```
*The frontend will run at `http://localhost:5173` (or the port specified by Vite in the terminal).*

## Features
- **OSINT Identity Discovery**: Give the system a descriptive prompt (with name, location, dob, and an image) to automatically harvest intelligence across 15+ sources (GitHub, LeakCheck, Reddit, SauceNAO, DuckDuckGo, etc.).
- **Social Analytics**: Track real-time narrative arcs, opinion divergence, echo chamber scoring, and incident detection on Reddit data.
- **Corroborated Dossiers**: View entity networks and timeline intelligence with robust, dynamically-computed confidence scores.
