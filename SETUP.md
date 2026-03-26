# Lensa Setup Commands

## 1) Start the Python bridge server

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python bridge_server.py
```

## 2) Copy the DB into Flutter assets

```powershell
New-Item -ItemType Directory -Force -Path assets\database, assets\audio | Out-Null
Copy-Item museum_guide.db assets\database\museum_guide.db -Force
Copy-Item audio\*.mp3 assets\audio\ -Force
```

## 3) Run the Flutter app

```powershell
flutter create .
flutter pub get
flutter run
```

## 4) Run the benchmark test

```powershell
python benchmark_recognition.py --images-dir images --db-path museum_guide.db
```
