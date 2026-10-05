# Smart Todo

App desktop in Python per gestire attività con promemoria automatici di sistema.

## Funzionalità
- Aggiunta, modifica ed eliminazione attività
- Scadenza con data e ora
- Notifica di sistema automatica alla scadenza (una sola volta)
- Filtri: tutte / attive / completate
- Persistenza su file JSON

## Tecnologie
- Python 3
- CustomTkinter (UI)
- Plyer (notifiche di sistema)
- Threading (controllo scadenze in background)

## Come avviare
```bash
pip install -r requirements.txt
python main.py
