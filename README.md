# Bosch MAP5000 Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/felix/bosch-map5000)

Eine vollständige, professionelle und rein asynchrone Home Assistant Integration für Bosch MAP5000 Alarmzentralen mit REST API (ab Firmware/API-Version 1.4.0288). 

> **Wichtig**: Die Bosch MAP5000 Anlage muss entsprechend lizenziert sein und über eine aktivierte REST API verfügen. Bitte beachte die Handbücher zur Anlage ("MAP5000_REST-API_Instructions").

## Features

- **Resource Discovery**: Automatische Erkennung der Systemkonfiguration (`/desc`).
- **Areas (Bereiche)**: Vollständige Home Assistant `alarm_control_panel` Unterstützung (`Arm`, `Disarm`).
- **Devices (Geräte)**: Points, Bewegungsmelder und Türkontakte als Home Assistant `binary_sensor`.
- **Incidents**: Anzeige von aktuellen Störungen und technischen Warnungen als System-Sensor.
- **Controls**: Unterstützung von Ausgängen (Outputs) und Internal Programs als `switch`. Walktest-Status, Chime Mode.
- **Modernes Dashboard**: Mitgeliefertes React-basiertes Dashboard (Glassmorphism-Optik) für optimale Darstellung in der HA-Sidebar.
- **Secure by default**: Nutzt asynchrone HTTP Digest-Authentication.

## Voraussetzungen

1. Eine erreichbare **Bosch MAP5000**.
2. **REST-API Modul** auf der Anlage aktiviert.
3. Ein angelegter REST-API **Benutzer** mit vergebenem Passwort.
4. Berechtigungen: Für Statusabfragen reicht der "Monitoring Mode". Für Scharfschalten (`Arm`/`Disarm`) oder Walktest muss das Profil **Full Functionality** freigeschaltet sein.

## Installation

### Variante A: HACS (Empfohlen)
1. Gehe in Home Assistant zu **HACS** -> **Integrationen**.
2. Oben rechts auf die drei Punkte klicken -> **Benutzerdefinierte Repositories**.
3. Die URL dieses Repositories einfügen und als "Integration" markieren.
4. "Bosch MAP5000" suchen, herunterladen und Home Assistant neustarten.

### Variante B: Manuell
1. Lade das Repository als ZIP herunter.
2. Kopiere den Ordner `custom_components/bosch_map5000` in das `custom_components` Verzeichnis deines Home Assistant.
3. Starte Home Assistant neu.

## Konfiguration

1. In Home Assistant zu **Einstellungen** -> **Geräte & Dienste** navigieren.
2. Unten rechts auf **Integration hinzufügen** klicken.
3. Nach **Bosch MAP5000 Alarm System** suchen.
4. Folgende Daten eingeben:
   - **Host/IP**: IP-Adresse der MAP (z.B. `192.168.10.6`)
   - **Port**: `443`
   - **Benutzername**: z.B. `REST-API` oder `BoschSt99`
   - **Passwort**: Dein Digest-Passwort
   - **SSL-Überprüfung**: `Deaktiviert` (Das selbstsignierte Zertifikat der Bosch-Zentrale wird standardmäßig nicht validiert. Nur in vertrauenswürdigen lokalen Netzwerken nutzen!)
   - **Polling Intervall**: Standardmäßig `30` Sekunden.

## Dashboard (Frontend)

Die Integration beinhaltet den Quellcode für ein natives React-Dashboard im Ordner `/frontend`.

**Entwicklung & Kompilieren (Node.js benötigt):**
```bash
cd frontend
npm install
npm run build
```
Nach dem Build kann das Dashboard (sofern als HA-Panel konfiguriert) über die Seitenleiste aufgerufen werden.

## Home Assistant Services

Die Integration bietet HA-Services für Automatisierungen an:
- `bosch_map5000.arm_area`
- `bosch_map5000.disarm_area`
- `bosch_map5000.bypass_device`
- `bosch_map5000.start_walktest`

*Beispiel Automatisierung (Scharfschalten bei Abwesenheit):*
```yaml
alias: "Haus Scharfschalten"
trigger:
  - platform: state
    entity_id: group.family
    to: "not_home"
action:
  - service: bosch_map5000.arm_area
    target:
      entity_id: alarm_control_panel.map5000_area_1
```

## Security & Troubleshooting

- **Verbindungsfehler (401 Unauthorized)**: Achte peinlichst genau darauf, dass die bereitgestellten REST-API Credentials korrekt sind. Das RPS-Passwort (Remote Programming Software) ist NICHT immer identisch mit dem REST-API-Passwort. Digest-Authentifizierung bricht rigoros ab, falls Credentials inkonsistent sind.
- **Passwort-Leaks**: Passwörter und Digest-Responses werden in den Home Assistant-Logs gemäß `diagnostics.py` automatisch maskiert (`REDACTED`).

## Lizenz
MIT License. Dieses Projekt ist Open-Source und nicht offiziell von der Bosch Sicherheitssysteme GmbH unterstützt.
