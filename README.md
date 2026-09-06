# MI Inspire – MVP Raspberry Pi

Sistema locale di digital signage per Meridionale Impianti. Il Raspberry Pi ospita il database e il server, riproduce il palinsesto sulla TV e rende la regia disponibile ai PC collegati alla stessa rete.

## Cosa funziona

- Regia web accessibile da PC, tablet e telefono nella rete locale.
- Creazione e generazione guidata dei messaggi.
- Coda di approvazione con pubblicazione e rifiuto.
- Destinazione: tutte le TV, uffici, produzione o cantieri.
- Player TV automatico con rotazione e aggiornamento ogni 5 secondi.
- Database SQLite persistente.
- Rilevamento degli schermi collegati.
- Cache dell'ultimo palinsesto in caso di momentanea perdita della connessione.
- Avvio automatico del server e di Chromium in modalità kiosk.

## Requisiti

- Raspberry Pi 4 o 5 consigliato, con Raspberry Pi OS Desktop 64 bit.
- Collegamento HDMI alla TV.
- Connessione Ethernet o Wi-Fi alla rete aziendale.

## Installazione sul Raspberry

1. Copiare ed estrarre la cartella `mi-inspire-raspberry` sul Raspberry.
2. Aprire il terminale dentro la cartella.
3. Eseguire:

```bash
chmod +x install.sh
./install.sh
sudo reboot
```

Dopo il riavvio la TV apre automaticamente il player.

## Aprire la regia dal PC

Il programma di installazione mostra l'indirizzo, normalmente simile a:

```text
http://192.168.1.50:8080
```

In alternativa provare:

```text
http://raspberrypi.local:8080
```

Il PC deve essere collegato alla stessa rete del Raspberry.

## Flusso operativo

1. Aprire la regia dal PC.
2. Creare un messaggio e selezionare il reparto.
3. Inviare il messaggio alla coda.
4. Premere **Approva e pubblica**.
5. Entro 5 secondi il Raspberry aggiorna la TV.

## Più schermi

Per un secondo Raspberry cambiare l'URL del file `systemd/mi-inspire-kiosk.desktop`, per esempio:

```text
http://IP-RASPBERRY-SERVER:8080/player?screen=tv-produzione&department=produzione
```

Il primo Raspberry continua a essere il server centrale; gli altri funzionano come player.

## Avvio manuale per prova

Su qualsiasi computer con Python 3:

```bash
python3 server.py
```

Aprire `http://127.0.0.1:8080` per la regia e `http://127.0.0.1:8080/player` per la TV.

## Sicurezza dell'MVP

Questa versione è progettata per una rete locale protetta. Non esporre direttamente la porta 8080 su Internet. Prima di un utilizzo aziendale definitivo saranno aggiunti autenticazione, HTTPS, ruoli nominativi e backup amministrato.
