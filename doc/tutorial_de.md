# Tutorial: Waste Collection Schedule

Dieses Tutorial zeigt anhand des ***GIPS***-Projektes der Domstadt Speyer am Rhein, wie die HACS-Integration ***Waste Collection Schedule*** installiert, konfirguriert und letztendlich verwendet beziehungsweise eingesetzt wird.

In diesem Tutorial wird die **YAML-Variante** mit einer `.ics`-Datei beschrieben, welche als Download-Link vom entsprechenden Entsorgungsdienst (oder der Stadtverwaltung) zur Verfügung gestellt wird, und dadurch automatisch täglich aktualisiert werden kann.

## (1) Beschreibung

***Waste Collection Schedule*** ist eine HACS-Komponente für Home Assistant, welche die Müllentsorgungspläne des zuständigen Dienstleisters (oder der Stadtverwaltung) - falls vorhanden - abruft.

Die täglich aktualisierten Termine für die Abfall-Entsorgung werden:

- entweder aus den Webseiten der entsprechenden Dienstleister (oder der Stadtverwaltung) gewonnen
- oder aus den vom Entsorger (oder der Stadtverwaltung) zur Verfügung gestellten `iCal`-Dateien (`.ics`) abgeleitet
- oder aus den vom Nutzer festgelegten Daten und aus den sich regelmäßig wiederholenden Datumsmustern generiert.

Der integrierte lokale Kalender von Home Assistant wird automatisch mit Zeitplänen gefüllt, und es besteht ein hohes Maß an Flexibilität bei der Formatierung und Anzeige von Informationen in den sogenannten Entitätskarten oder Pop-ups.

Das Rahmenwerk kann jederzeit problemlos um zusätzliche Anbieter von Entsorgern oder anderen Diensten erweitert werden, vorausgesetzt, dass diese auch die dafür erforderlichen Daten zur Verfügung stellen (können).

## (2) Ziel

Anzeige des jeweils nächsten Termins der entsprechenden Müllentsorgung (*Bio*-, *Haus*-, *Rest*-, *Sammel*- und *Sperrmüll*) in einem ansprechenden Design.

## (3) Voraussetzung

### (A) Dateien

- URL der `.ics`-Abfallkalender-Datei des verantwortlichen Entsorgungsdienstes (oder der Stadtverwaltung)

### (B) Kenntnisse

- `HTML`-, `CSS`- und rudimentäre `JS`-Kenntnisse
- Exkurs: [Jinja2-Templates](exkurs_jinja2_templates_de.md)

### (C) Integrationen

- HACS
- Waste Collection Schedule
- Studio Code Server (*optional*, ***empfehlenswert***)

### (D) Frontend

- Custom HTML Template Card
- Lovelace Card Mod (*optional*, ***empfehlenswert***)
- Custom Button Card (*optional*)
- Lovelace Layout Card (*optional*, ***empfehlenswert***)
- Browser Mod 2 (*optional*)

## (4) Installation

Zur Einrichtung des Abfallkalenders gibt es zwei Arten - **GUI** und **YAML** -, und hierbei wiederum jeweils mehrere Möglichkeiten.

### (A) Installationsroutine

Um *Waste Collection Schedule* zu installieren und anschließend zu konfigurieren, ist Folgendes zu tun :

1. HA → HACS → in die Suchmaske `waste collection schedule` eintragen, und aus der Trefferliste den Eintrag `Waste Collection Schedule` auswählen → herunterladen anklicken → die aktuelle Version auswählen → Installationsverzeichnis: `/config/custom_components/waste_collection_schedule` → herunterladen
2. HA → Werkzeuge → gegebenenfalls die Registerkarte `YAML` öffnen → Konfiguration prüfen → OK ! → neu starten
3. HA → Studio Code Server → die Datei `configuration.yaml` öffnen → nachfolgende Codezeile an das Ende einfügen :
  
   ```yaml
   waste_collection_schedule: !include waste-collection-schedules.yaml
   ```

4. Im `config/`-Verzeichnis eine neue Datei namens `waste-collection-schedules.yaml` anlegen (und öffnen), und den nachfolgenden Code eintragen, um den Kalender zu erstellen, wobei die Eingaben beziehungsweise Werte jeweils dem eigenen Szenario entsprechend angepasst werden müssen.

    Benötigt wird hierzu der genaue Link zur `.ics`-Datei des Abfallkalenders des jeweiligen Dienstanbieters (oder der Stadtverwaltung).

    Im Link jeweils alle Vorkommen der (konstanten) Jahreszahl (hier: `2026`) durch die Variable `{%Y}` ersetzen. Hier ist dies...

    - `Speyer2026` ersetzen durch `Speyer{%Y}`
    - `Jahr=2026` ersetzen durch `Jahr={%Y}`

    ...wodurch bei jedem Download die aktuelle Jahreszahl generiert wird, so dass ein manuelles Downloaden oder das erneute Anpassen der URL zukünftig entfällt - im Besonderen nach einem Jahreswechsel:

    ```yaml
    sources: # enthält Infos über beziehungsweise für den Kalender
      - name: ics # "ics", falls der Dienstanbieter von wcs nicht unterstützt wird
        args:
          url: https://www.stadtwerke-speyer.de/speyerGips/Gips?SessionMandant=Speyer&Anwendung=Abfuhrkalender&Methode=TermineAnzeigenICS&Mandant=Speyer&Abfuhrkalender=Speyer{%Y}&Bezirk_ID=17&Jahr={%Y}
        calendar_title: "EBS Speyer" # der Name des Kalenders
        day_offset: 0 # 0; day_offset in Tagen, der zum Abholdatum addiert werden soll (darf *negativ* sein)
    fetch_time: "01:16" # zu welcher Zeit soll der tägliche (Update-)Download stattfinden
    random_fetch_time_offset: 15 # zufällige Startzeit innerhalb ..._offset Minuten (+/-) von fetch-time
    day_switch_time: "23:59" # Zeitpunkt (HH:MM), ab welchem der aktuelle Eintrag verworfen und zum nächsten Eintrag übergegangen wird
    separator: "," # trennt bei Textausgaben die Einträge mittels Separator voneinander
    ```

5. Die Datei speichern → HA → Werkzeuge → gegebenenfalls die Registerkarte `YAML` öffnen → Konfiguration prüfen → OK ! → neu starten
6. In Studio Code Server im `/config`-Verzeichnis die Ordner `sensoren` und `templates` anlegen.
7. In Studio Code Server in der Datei `configuration.yaml` zuerst die nachfolgenden Einträge an das Ende hinzufügen :
  
    ```yaml
    sensor: !include_dir_merge_list sensoren/ # den Ordner 'sensoren' der Domäne 'sensor:' zuweisen
    template: !include_dir_merge_list templates/ # den Ordner 'templates' der Domäne 'template:' zuweisen
    ```

8. Den nachfolgenden Codeblock an den Anfang - unterhalb der Domäne `logger:` - der `configuration.yaml` platzieren und anschließend speichern :
  
    ```yaml
    homeassistant:
      allowlist_external_dirs:
        - "/config/sensoren" # den Ordner 'sensoren' in HA einbinden
        - "/config/templates" # den Ordner 'templates' in HA einbinden
    ```

### (B) Fehlerbehebung

#### (I) Duplicate Key

Sollte es jetzt zu einer Fehleranzeige im Code durch *Studio Code Server* kommen, derart, dass einer oder gar beide Domäneneinträge (`sensor:` und/oder `template:`) als `duplikate Key` (doppelter Schlüssel) markiert werden, dann liegt dies daran, dass diese(r) Domänennamen bereits in der Datei `configuration.yaml` benutzt werden beziehungsweise benutzt wird.
![duplikate Key in der configuration.yaml](pictures/configuration-yaml_duplicate-key.png)
*Abbildung: duplikate Key in der configuration.yaml*

**Lösung:**  
Angenommen, der Inhalt der Domäne `sensor:` in der Datei `configuration.yaml` bestünde aktuell aus den nachfolgenden Einträgen...
  
```yaml
sensor:
- platform: name_der_platform # beispielsweise Feedparser
  name: name_1 # beispielsweise CHIEFS_NEWS
  ...
   
- platform: name_der_platform # beispielsweise Feedparser
  name: name_2 # beispielsweise FORTUNA_NEWS
  ...
   
- platform: template
  sensors:
    name_1_attributes_0: # beispielsweise FORTUNA_NEWS_attributes_0
    ...
   
- platform: template
  sensors:
    name_1_attributes_1: # beispielsweise FORTUNA_NEWS_attributes_1
    ...

- platform: template
  sensors:
    name_2_attributes_0: # beispielsweise CHIEFS_NEWS_attributes_0
    ...
```

...dann würden zwei unterschiedliche Werte (`name_1` und `name_2`) des Parameters `name` der `platform` `name_der_platform` zugeordnet werden.

Für jeden dieser Einträge muss somit jeweils im Verzeichnis `/config/sensoren/` eine eigene `.yaml`-Datei angelegt werden:

- `name_der_platform-sensor--name_1.yaml`, beispielsweise *feedparser-sensor--fortuna.yaml* und
- `name_der_platform-sensor--name_2.yaml`, beispielsweise *feedparser-sensor--chiefs.yaml*.

Die Inhalte der Dateien wären demnach beispielsweise:
  
*feedparser-sensor--chiefs.yaml*:
  
```yaml
- platform: feedparser
  name: CHIEFS News
  ...    
- platform: template
  sensors:
    chiefs_news_attributes_0:
    ...    
- platform: template
  sensors:
    chiefs_news_attributes_1:
    ...
```
  
feedparser-sensor--fortuna.yaml :
  
```yaml
- platform: feedparser
  name: FORTUNA News
  ...
- platform: template
  sensors:
    fortuna_news_attributes_0:
    ...
```
  
Letztendlich wird in der Datei `configuration.yaml` alles **innerhalb** der Domäne `sensor:` dem Inhalt nach (sortiert) in entsprechende externe Dateien ausgelagert (cut & paste) und der Eintrag `sensor:` durch den Eintrag `sensor: !include_dir_merge_list sensoren/` ersetzt.

Analog dazu gegebenenfalls die Domäne `template:` in externe Dateien auslagern und dementsprechend anpassen (`template: !include_dir_merge_list templates/`).
  
#### (II) patternWarning

*Studio Code Server* zeigt hierbei (`sensor: !include_dir_merge_list sensoren/`) den Fehler ***patternWarning*** an.

Der Code ist allerdings richtig und funktioniert.

Abschließend:
HA → Werkzeuge → Konfiguration prüfen → OK ! → neu starten

### (C) Überprüfung

Es wird überprüft, ob die Daten aus der `.ics`-Datei auch in den erstellten Kalender eingetragen worden sind, und ob die entsprechenden *Entitäten* und *Zustände* existieren und richtig interpretiert werden.

Die Verzeichnisstruktur würde sich momentan wie folgt darstellen:

```yaml
   ˅ CONFIG
     ...
     > custom_components
     ...
     ˅ sensoren   
       feedparser-sensor--chiefs.yaml
       feedparser-sensor--fortuna.yaml
     > templates
     ...
     configuration.yaml
     ...
     waste-collection-schedules.yaml
```

HA → Kalender → den entsprechenden Kalender (hier: `EBS-Kalender`) auswählen:
![Abfuhr-Termine der verschiedenen Abfall-Arten im Kalender des entsprechenden Dienstleisters](pictures/ebs-kalender_ansicht.png)
*Abbildung: Abfuhr-Termine der verschiedenen Abfall-Arten im Kalender des entsprechenden Dienstleisters*

Diese Überprüfung zeigt, dass die Abhol-Termine der jeweiligen Müllart korrekt eingetragen worden sind und auch richtig angezeigt werden.

**Und** / **oder** :  
HA → Werkzeuge → Menüeintrag *Zustände* → Entitäten nach dem Namen des Kalenders (hier: `ebs`) filtern :  
![Liste der Zustände, gefiltert nach dem
Kalendernamen](pictures/ebs-kalender_zustand.png)
*Abbildung: Liste der Zustände, gefiltert nach dem Kalendernamen (hier: ebs)*

Diese Überprüfung verdeutlicht, dass die Attribute der entsprechenden Entität vollständig und richtig sind.

**Und** / **oder** :  
HA → Einstellungen → Geräte & Dienste → auf den Menüeintrag `Entitäten` klicken, und nach *Integrationen → Waste Collection Schedule* filtern. Es sollte nun der Kalender aufgelistet sein :
![Liste der Entitäten, gefiltert nach der Integration Waste Collection Schedule](pictures/ebs-kalender_entität.png)
*Abbildung: Liste der Entitäten, gefiltert nach der Integration Waste Collection Schedule*

Diese Überprüfung zeigt, dass der während der WCS-Installation erstellte Kalender als *Entität* registriert worden ist.

Die `configuration.yaml` würde aktuell beispielsweise wie folgt aussehen :
  
   ```yaml
   logger:
     default: warning
     logs:
       ...
   
   homeassistant:
     allowlist_external_dirs:
       - "/config/sensoren"
       - "/config/templates"
       - ...
   
   # Loads default set of integrations. Do not remove.
   default_config:
   
   # Load frontend themes from the themes folder
   frontend:
     themes: !include_dir_merge_named themes
     extra_module_url: !include extra-modules.yaml
   
   # Outsourced
   ...
   sensor: !include_dir_merge_list sensoren/
   template: !include_dir_merge_list templates/
   waste_collection_schedule: !include waste-collection-schedules.yaml
   ```

### (D) Angelegte Dateien und Verzeichnisse

Während der Installation wurden die nachfolgenden Dateien und Ordner angelegt:

```yaml  
˅ CONFIG
  > .cache
  ...
  ˅ custom_components
    ...
    > hacs
    ...
    ˅ waste_collection_schedule
      > translations
      > waste_collection_schedule
      __init__.py
      calendar.py
      config_flow.py
      const.py
      icons.json
      init_ui.py
      init_yaml.py
      manifest.json
      sensor.py
      service.py
      services.yaml
      sources.json
      waste_collection_api.py
      wcs_coordinator.py
```

## Konfiguration

### Sensoren

Alle Sensoren werden nach demselben Code-Muster konstruiert, somit muss lediglich der jeweilge Inhalt kopiert, und anschließend die entsprechenden Werte der Parameter `name` und `types` angepasst werden. Deswegen werden hier nur zwei Sensoren als Beispiel herangezogen:

- der Haupt-Sensor (nächste EBS-Abfuhr) und
- die Abfallart-Sensoren (Papiertonne, etc).

**Hinweis**:
Die Namen der `.yaml`-Dateien dürfen sowohl die Umlaute `ä`, `ö` und `ü`, als auch `Leerzeichen` enthalten!
Empfehlenswert sind stattdessen: `a`, `o`, `u` und als Trennung ein oder mehrere `Minus`-Zeichen (`-`, `--` , `---`) anstelle eines Unterstriches (`_`).

1. Studio Code Server öffnen → im Verzeichnis `/config/sensoren` die Datei `wcs-sensor--nachste-ebs-abfuhr.yaml` (des Hauptsensors) anlegen, und die nachfolgenden Codezeilen in die leere Datei eintragen → diese Änderungen anschließend speichern :
  
   ```yaml
   - platform: waste_collection_schedule
     name: "nächste EBS-Abfuhr"
     value_template: >
       {{value.types|join(", ")}}
       {% if value.daysTo == 0 %} heute
       {% elif value.daysTo == 1 %} morgen
       {% else %} in {{value.daysTo}} Tagen
       {% endif %}
   ```

2. Die `.ics`-Kalenderdatei, welche bekanntermaßen vom Entsorgungsbetrieb (oder der Stadtverwaltung) als Download-Link angeboten wird, auch auf den lokalen PC hochladen. Diese Datei wird hier nur für den nachfolgenden Schritt benötigt, und kann danach sofort wieder gelöscht werden.
Ist die `.ics`-Datei auf den PC hochgeladen worden, dann diese mittels eines gewöhnlichen Texteditors (beispielsweise *Notepad*) öffnen, um danach deren Inhalt einsehen zu können. Die Werte, die hier unter dem Parameter-Namen `SUMMARY` gelistet werden, sind diejenigen, welche den Sensoren-Namen bilden - **nicht** den Namen der `.yaml`-Sensor-Datei! - und zwar **identisch**, Zeichen für (Leer-)Zeichen, gegebenenfalls auch mit Umlauten!
3. Den Cursor an den Anfang der ersten Zeile setzen → `STRG + F` öffnet die Suchfunktion innerhalb der Datei → `summary` in die Suchmaske eintragen, um das erste Vorkommen anzuzeigen. Den **Wert** dieses Parameters notieren → nach dem nächsten Vorkommen suchen → dessen **Wert** notieren..., solange, bis alle Werte notiert sind. Hierbei gilt zu beachten, dass keine Duplikate notiert werden sollten.
Letztendlich sind dies hier :

    | Mülltyp      | Aliasname      |Sensor-Dateiname                 |
    |:-------------|:---------------|:--------------------------------|
    |Biotonne      | braune Tonne   | wcs-sensor--braune-tonne.yaml   |
    |Gelber Sack   | gelber Sack    | wcs-sensor--gelber-sack.yaml    |
    |Grünabfall 1  | Grünabfall 1   | wcs-sensor--grunabfall-1.yaml   |
    |Grünabfall 2  | Grünabfall 2   | wcs-sensor--grunabfall-2.yaml   |
    |Grünabfall 3  | Grünabfall 3   | wcs-sensor--grunabfall-3.yaml   |
    |Grünabfall 4  | Grünabfall 4   | wcs-sensor--grunabfall-4.yaml   |
    |Papiertonne   | blaue Tonne    | wcs-sensor--blaue-tonne.yaml    |
    |Papier Gewerbe|blauer Container|wcs-sensor--blauer-container.yaml|
    |Resttonne     |schwarze Tonne  | wcs-sensor--schwarze-tonne.yaml |
    |Sonderabfall A|Sonderabfall 1  |wcs-sensor--sonderabfall-1.yaml  |
    |Sonderabfall B|Sonderabfall 2  |wcs-sensor--sonderabfall-2.yaml  |
    |Tannenbaum    |Tannenbaum      |wcs-sensor--tannenbaum.yaml      |

    Die Namen der `.yaml`-Dateien dürfen sowohl die Umlaute `ä`, `ö` und `ü`, als auch `Leerzeichen` enthalten!
  
    Wer dies nicht mag, sollte auch auf den Unterstrich (`_`) als Trennzeichen verzichten, und stattdessen das Minuszeichen (`-`) als Trennzeichen verwenden.
    Unbedingt Kleinbuchstaben verwenden!
  
    Die Datei `wcs sensor gelber sack.yaml` sollte demnach wie folgt benannt werden :
    `wcs-sensor--gelber-sack.yaml`.

    Momentan hat die Datei `waste-collection-schedules.yaml` den nachfolgenden Inhalt :
  
    ```yaml
    sources: # enthält Infos über beziehungsweise für den Kalender
    - name: ics # "ics", falls der Dienstanbieter von wcs nicht unterstützt wird
      args:
        url: https://www.stadtwerke-speyer.de/speyerGips/Gips?SessionMandant=Speyer&Anwendung=Abfuhrkalender&Methode=TermineAnzeigenICS&Mandant=Speyer&Abfuhrkalender=Speyer{%Y}&Bezirk_ID=17&Jahr={%Y}
      calendar_title: "EBS Speyer" # der Name des Kalenders
      day_offset: 0 # 0; day_offset in Tagen, der zum Abholdatum addiert werden soll (darf *negativ* sein)
    fetch_time: "01:16" # zu welcher Zeit soll der tägliche (Update-)Download stattfinden
    random_fetch_time_offset: 15 # zufällige Startzeit innerhalb ..._offset Minuten (+/-) von fetch-time
    day_switch_time: "23:59" # Zeitpunkt (HH:MM), ab welchem der aktuelle Eintrag verworfen und zum nächsten Eintrag übergegangen wird
    separator: "," # trennt bei Textausgaben die Einträge mittels separator voneinander
    ```
  
    Bevor die Sensor-Dateien angelegt und mit Code gefüllt werden, muss zunächst die Datei `waste-collection-schedules.yaml` angepasst werden.
4. Zuerst wird der Parameter `source:` um das Attribut `customize:` - eine Liste - erweitert, welche mittels nachfolgender Attribute konfiguriert werden kann:
   `type:`, `alias:`, `show:`, `icon:`, `picture:`, `use_dedicated_calendar:` und `dedicated_calendar_title:`.
  
    Dazu zuerst unterhalb - ***unterhalb***, nicht ***Attribut von*** (!) - des Attributs `arg:` das Attribut `customize:` einfügen, und danach dessen Parameter und deren Werte. Die `waste-collection-schedules.yaml` sollte nach dem ersten Abfallart- beziehungsweise Mülltyp-Eintrag nachfolgenden Inhalt aufweisen :
  
    ```yaml
    sources: # enthält Infos über beziehungsweise für den Kalender
    - name: ics # "ics", falls der Dienstanbieter von wcs nicht unterstützt wird
      args:
        url: https://www.stadtwerke-speyer.de/speyerGips/Gips?SessionMandant=Speyer&Anwendung=Abfuhrkalender&Methode=TermineAnzeigenICS&Mandant=Speyer&Abfuhrkalender=Speyer{%Y}&Bezirk_ID=17&Jahr={%Y}
      customize:
        - type: "Biotonne" # Name der Abfallart, so wie er im Kalender aufgeführt ist
          alias: "braune Tonne" # neuer Name
          show: True # diese Abfallart anzeigen (True)
          icon: mdi:trash-can-outline # icon aus der mdi-Sammlung
          #picture: # "Pfad zum Bild, das verwendet werden soll"
          use_dedicated_calendar: False # separaten Kalender, speziell für diese Abfallart, anlegen?
          #dedicated_calendar_title: # "Titel des speziell für diese Abfallart angelegten Kalenders"
      calendar_title: "EBS Speyer"
      day_offset: 0
    fetch_time: "01:16"
    random_fetch_time_offset: 15
    day_switch_time: "15:00"
    separator: ","
    ```
  
    Anschließend kommen sogenannte `Jinja2`-Templates zum Einsatz. Es können 2 Template-Typen verwendet werden:
  
    - zum einen ein Template zum verarbeiten der Kalender-Werte - auch der Datumswerte - (→ Werte- oder Value-Template),
    - zum anderen ein Template zum Verarbeiten der Datumswerte (→ Datum- oder Date-Template).
  
   Wie diese angefertigt und eingesetzt werden, ist nachfolgend beschrieben :  
   ***Value-Template***:
  
   | Ausgabe                             |Code                                                                                                              |
   | ------------------------------------|------------------------------------------------------------------------------------------------------------------|
   | " "                                 |" "                                                                                                               |
   | "in [Zahl] Tagen"                   |"in {{value.daysTo}} Tagen"                                                                                       |
   | "[Müllart] in [Zahl] Tagen"         |"{{value.types \| join(', ')}} in {{value.daysTo}} Tagen"                                                         |
   | "[Zahl]"                            | "{{value.daysTo}}"                                                                                               |
   | "in [Zahl] Tagen oder Morgen/Heute" |"{% if value.daysTo == 0 %}heute{% elif value.daysTo == 1 %}morgen{% else %}in {{value.daysTo}} Tagen{% endif %}" |
   | "[Wochentag], den dd.mm.yyyy"       |"{{value.date.strftime('%a')}}, den {{value.date.strftime('%d.%m.%Y')}}"                                          |
   | "[Wochentag], yyyy-mm-dd"           |"{{value.date.strftime('%a')}}, {{value.date.strftime('%Y-%m-%d')}}"                                              |
   | "nächste BFS-Abfuhr"                |"{{value.types\|join(', ')}}" {# Beispiel: Biotonne in 5 Tagen #}                                                 |
  
   ***Date-Template***:
  
   | Ausgabe         | Code                                    |
   |:----------------|:----------------------------------------|
   | " "             | " "                                     |
   | "20.09.2026"    |"{{value.date.strftime('%d.%m.%Y')}}"    |
   |"Sun, 20.09.2026"|"{{value.date.strftime('%a, %d.%m.%Y')}}"|
   |"09/20/2026"     |"{{value.date.strftime('%m/%d/%Y')}}"    |
   |"Sun, 09/20/2026"|"{{value.date.strftime('%a, %m/%d/%Y')}}"|
   |"2026-09-20"     |"{{value.date.strftime('%Y-%m-%d')}}"    |
   |"Sun, 2026-09-20"|"{{value.date.strftime('%a, %Y-%m-%d')}}"|

5. Falls die `.yaml`-Sensor-Dateien (`wcs-sensor--braune-tonne.yaml`, etc.) der jeweiligen Abfall-Arten noch nicht im Ordner `/config/sensoren` erstellt worden sind, dann ist es an der Zeit, dies jetzt nachzuholen. Zuerst jedoch nur eine der soeben erstellten Dateien mit Inhalt füllen, und zwar diejenige, welche in der Datei `waste-collection-schedules.yaml` innerhalb des neu angelegten Attributs `customize:` soeben aufgelistet beziehungsweise eingetragen worden ist.
   Der nachfolgende Code ist beispielhaft für eine Abfallart-Sensordatei - hier ist es die Datei `wcs-sensor--braune-tonne.yaml` - und kann als Muster für alle weiteren Abfallart- Sensordateien verwendet werden, wobei dann jeweils nur einige Parameter-Werte angepasst werden müssen:
  
    ```yaml
    - platform: waste_collection_schedule
      source_index: 0 # Quelle: ics
      name: "braune Tonne" # alias, wenn der Wert gesetzt worden ist
      details_format: upcoming # gültig sind upcoming, appointment_types, generic, hidden
      count: 1 # die Anzeige der nächsten count-Sammlungen im HA-Pop-up
      leadtime: 7 # die Anzeige von Abholungen, die innerhalb der nächsten leadtime-Tage stattfinden
      value_template: >
        "{{ value.daysTo }}" {# Anzahl der Tage bis zur Abholung dieser Abfallart #}
      #date_template: {{ value.date.strftime('%A, %d.%m.%Y') }}
      add_days_to: 0 # ein Boolean-Wert, der das Attribut daysTo (de)aktiviert (→ (0) oder 1).
      event_index: 0 # nächste Abholung; 1: zweite (übernächste) Abholung; 2: dritte Abholung, ...
   
      types:
        - braune Tonne # sämtliche Abfallarten, die unter diesem Sensor-Namen geführt werden sollen
    ```
  
    ***Hinweis***:
    In *Studio Code Server* lösen sämtliche Einträge jeweils den Fehler ***DisallowedExtraPropWarning*** aus.
    Dies kann unbeachtet bleiben und bedarf keines Einschreitens. Der Code ist richtig und funktioniert!

    ***Erläuterung***:
  
    - `source_index:`
      **Konstante:** `SOURCE_INDEX`
      **Standard**: 0
      **Beschreibung**: wird verwendet, um einen Sensor einer bestimmten Quelle zuzuordnen. Dies ist nur dann erforderlich, wenn mehrere Quellen definiert sind. Die erste definierte Quelle ist `source_index 0`, die zweite `source_index 1` usw. Wenn man einen Sensor haben möchte, der die Daten aus mehreren Quellen kombiniert, dann muss einfach eine Liste der Quellen hinzugefügt werden. Dieser Parameter ist bei Verwendung der **GUI**-Konfiguration nicht verfügbar, da die Sensoren direkt zu den Quellen hinzugefügt werden.
    - `name`:
      *Konstante*: `NAME`
      *Standard*: der von der Quelle zugeordnete Namen
      *Beschreibung*: Name des Sensors
    - `details_format`:
      *Konstante*: `DETAILS_FORMAT`
      *Standard*: upcoming
      *Beschreibung*: gibt das Format an, welches zum Anzeigen von Informationen im HA-Pop-up-Fenster verwendet wird. Gültige Werte sind: `upcoming`, `appointment_types`, `generic` und `hidden`
    - `count`:
      *Konstante*: `COUNT`
      *Standard*: 1
      *Beschreibung*: die Anzeige der nächsten [Zahl]-Sammlungen im HA-Popup
    - `leadtime`:
      *Konstante*: `LEADTIME`
      *Standard*: 1
      *Beschreibung*: die Anzeige von Abholungen, die innerhalb der nächsten `leadtime`-Tage stattfinden
    - `value_template`:
      *Konstante*: `VALUE_TEMPLATE`
      *Beschreibung*: Template, um die Statusinformationen einer Entität zu formatieren.
    - `date_template`:
      *Konstante*: `DATE_TEMPLATE`
      *Beschreibung*: Template, um die Datum-Daten einer Entität im HA-Popup zu formatieren.
    - `add_days_to`:
      *Konstante*: `ADD_DAYS_TO`
      *Standard*: 0
      *Beschreibung*: die `add_day_to`-Anzahl der Tage bis zur nächsten Sammlung
    - `event_index`:
      *Konstante*: `EVENT_INDEX`
      *Standard*: 0
      *Beschreibung*: um einem Sensor einen bestimmten Abholdatums-Index zuzuordnen. Das nächste Abholdatum hat den `event_index`-Wert 0. Nützlich, wenn man dedizierte Sensoren für die nächste Abholung, zweite Abholung, dritte Abholung, usw. haben möchte.
    - `types`:
      *Konstante*: `TYPES`
      *Beschreibung*: Filtern nach Abfallarten. Der Sensor zeigt nur Sammlungen an, die dieser Abfallart entsprechen. Man muss den Aliasnamen einsetzen, wenn man für den betreffenden Sensor unter dem Attribut `customize` (`waste-collection-schedule.yaml`) den Parameter `Alias` verwendet hat.

6. HA → Werkzeuge → Konfiguration prüfen → OK ! → neu starten
7. Zum Überprüfen kann außer den bereits erwähnten Möglichkeiten jetzt auch das Standard-Dashboard *Übersicht* verwendet werden. Dort sollte der soeben angelegte Sensor `braune Tonne` unter dem Bereich `Sensor` aufgelistet sein, samt seines Wertes. Wird jetzt in diesem Dashboard auf diesen Abfallart-Sensor geklickt, dann erscheint das entsprechende HA-Pop-up mit weiteren Informationen über den betreffenden Sensor; unter anderem kann man dort die `Entitäts-ID` des betreffenden Sensors einsehen, kopieren oder aber auch ändern...
8. Die restlichen Sensor-`.yaml`-Dateien im Ordner `/config/sensoren` mit dem entsprechenden Code füllen.
9. Zur zwischenzeitlichen Überprüfung:
   HA → Werkzeuge → Konfiguration prüfen → OK ! → neu starten → HA → Übersicht → unter dem Bereich `Sensor` sollten nun alle neu angelegten Sensoren zu finden sein.
10. Man kann auch mehrere Abfallart-Sensoren zusammenfassen. Beispielsweise könnte man die Abfallarten `Grünabfall 1`, `Grünabfall 2`, `Grünabfall 3`, `Grünabfall 4` und `Tannenbaum` zu einem einzigen Sensor zusammenfassen. Dazu im Ordner `/config/sensoren` eine neue Datei namens `wcs-sensor--grunabfall.yaml` anlegen, und mit nachfolgendem Code-Block füllen :
  
    ```yaml
    - platform: waste_collection_schedule
      source_index: 0
      name: "Grünabfall"
      details_format: upcoming
      count: 1
      leadtime: 7
      value_template: "{{value.daysTo}}"
    
      #date_template: "{{value.date.strftime('%A, %d.%m.%Y')}}"
      add_days_to: 0
      event_index: 0
      types:
       - Grünabfall 1
       - Grünabfall 2
       - Grünabfall 3
       - Grünabfall 4
       - Tannenbaum
    ```

11. Nun wird ein weiterer Sensor angelegt, welcher sowohl die Abfallart, als auch die Anzahl der Tage anzeigt, bis die nächste Müll-Abholung erfolgt. Man kann auch 'nur' die Abfallart und das entsprechende Datum des nächsten Abfuhrtermins anzeigen lassen.
    Dazu jetzt zunächst im Verzeichnis `/config/sensoren` eine neue Datei namens `wcs-sensor--nachste-ebs-abfuhr.yaml` anlegen, und nachfolgenden Code eintragen :
  
    ```yaml
    - platform: waste_collection_schedule
      name: "nächste EBS-Abfuhr"
      value_template: >
        {{value.types|join(", ")}}
        {% if value.daysTo == 0 %} heute
        {% elif value.daysTo == 1 %} morgen
        {% else %} in {{value.daysTo}} Tagen
        {% endif %}
    ```

12. HA → Werkzeuge → Konfiguration prüfen → OK ! → neu starten → HA → Übersicht → unterhalb des Bereichs `Sensor` sollten nun alle neu angelegten Sensoren zu finden sein.

### Templates

Einige Template-Schnipsel wurden bereits jeweils bei den Sensor-`.yaml`-Dateien verwendet. Diese dienten dazu, die Anzeige des jeweiligen Sensors beziehungsweise der jeweiligen Sensorgruppe im Dashboard zu steuern. Dasjenige Template, welches letztendlich die ***Textausgabe*** des Pop-ups (beispielsweise: *Heute müssen folgende Abfälle bereitgestellt werden: ...*) steuert, besteht weitgehend aus `Jinja2`-Code, und kann - mit wenigen Einschränkungen - nach persönlichen Vorlieben erstellt werden.

Wer detaillierte Informationen (mit Code-Beispielen) über das Programmieren mit der `Jinja2`-Engine bekommen möchte, wird vor allem bei [Template Designer Documentation](https://jinja.palletsprojects.com/en/latest/templates/) fündig werden.

Um ein Template zur Steuerung der ***Textausgabe*** zu erstellen - Ziel ist es, dass bereits am **Vortag** des Abfuhr-Termins eine Nachricht erscheint, mit der Information, welche Abfallart zur Abfuhr bereitgestellt werden muss.

Um dies zu erreichen, ist Folgendes zu tun:

1. HA → Studio Code Server → die Datei `wcs-template--erinnerung-ebs-abfuhr.yaml` im Verzeichnis `/config/templates` anlegen, und vorab den nachfolgenden Code-Block einfügen :
  
    ```yaml
    - name: Erinnerung EBS-Abfuhr # Namen anpassen
      unique_id: erinnerung_ebsabfuhr # ID anpassen
      icon: mdi:trash-can-outline
      state: >
        # hier wird später der persönliche Template-Code eingefügt - die Einrückung(en) dabei stets beachten !
    ```

2. HA → Werkzeuge → in der Menüleiste den Eintrag `Template` auswählen → in den dortigen Editor den individuellen Code eingeben. Nachfolgend ein Beispiel-Code, anhand dessen man üben kann, um letztendlich den eigenen Code anlegen zu können.
  
    **Tipp:**
    die exakte `Entitäten-ID` des jeweiligen Sensors kann wie folgt ermittelt werden:
    Im Standard-Dashboard *Überblick* auf den betreffenden Sensor klicken, woraufhin das Pop-up des betreffenden Sensors erscheint. In diesem auf das Zahnrad-Symbol (→ Einstellungen) klicken, woraufhin sich der Konfigurations-Dialog des betreffenden Sensors öffnet. Dort kann die `Entitäts-ID` des Sensors festgelegt und auch kopiert werden (durch Klick auf das Dokumenten-Symbol am Rand rechts-außen der Sektion *Entitäts-ID*).
  
    ```yaml
    {% set StatusSensoren = {
      "braune Tonne": states.sensor.braune_tonne.state,
      "blaue Tonne": states.sensor.blaue_tonne.state,
      "gelber Sack": states.sensor.gelber_sack.state,
      "schwarze Tonne": states.sensor.schwarze_tonne.state,
      "Grünabfall 1": states.sensor.grunabfall_1.state,
      "Grünabfall 2": states.sensor.grunabfall_2.state,
      "Grünabfall 3": states.sensor.grunabfall_3.state,
      "Grünabfall 4": states.sensor.grunabfall_4.state,
      "Sondermüll 1": states.sensor.sonderabfall_1.state,
      "Sondermüll 2": states.sensor.sonderabfall_2.state,
      "blauer Container": states.sensor.blauer_container.state,
      "Tannenbaum": states.sensor.tannenbaum.state,
      }
    %}
    {%- set SensorDeadLine = namespace(key=[]) %}
    ```
  
    Aus diesen beiden Zuweisungen können jetzt die unterschiedlichsten Textausgaben in derselben Datei erzeugt werden :

    Bei der ersten Zuweisung wird der Variablen `StatusSensoren` ein sogenanntes *Dictionary* (→ Wörterbuch) zugewiesen. Es besteht aus (mehreren)`"Schlüssel":Wert`-Paaren, welche mittels Kommata (`,`) voneinander getrennt aufgelistet werden, wobei das letzte `"Schlüssel":Wert`-Paar ebenfalls ein Komma am Ende als Trennung beinhalten darf.
    Die gesamten `"Schlüssel":Wert`-Paare sind umfasst von jeweils einer geschweiften Klammer, die den Anfang `{` beziehungsweise das Ende `}` eines *Dictionaries* (→ Wörterbuch) repräsentieren. Man kann sowohl auf den Schlüssel, als auch auf den Wert des Schlüssels eines `"Schlüssel":Wert`-Paares des *Dictionaries* zugreifen.
    Bei der zweiten Zuweisung wird ein sogenannter *Namensraum* gebildet. Ein *Namensraum* ist eine Sammlung aktuell definierter symbolischer Namen zusammen mit Informationen über dasjenige Objekt, auf welches jeder (symbolische) Name verweist. Man kann sich einen *Namensraum* auch als einen Typ *Dictionary* vorstellen, in dem die "Schlüssel" die (symbolischen) Objektnamen und die Werte die Objekte selbst repräsentieren.
    Jedes `"Schlüssel":Wert`-Paar ordnet demnach seinem entsprechenden Objekt einen Namen zu.
    Im Beispiel-Code wird der Variablen `SensorDeadLine` der *Namensraum* `key` als leere Liste (`[]`) zugewiesen, auf diese mittels `SensorDeadLine.key` zugegriffen werden kann.
    Dies ist eine Möglichkeit, um in Home Assistant (HA) dynamische Listen in Templates erzeugen zu können.
    Dieser *Namensraum* ist **lokal**, das heißt er ist nur ***innerhalb*** **dieses Templates** gültig. Er bleibt solange bestehen, bis das Template beendet wird.

    In den nachfolgenden Beispielen sind einige mögliche Textausgabe-Muster aufgeführt, die zusätzlich in **derselben** Datei aufgeführt werden können.
  
    **Beispiel: Durch das Wörterbuch `StatusSensoren` iterieren**
  
    ```yaml
    {% for item in StatusSensoren -%}
      {{- item -}}: in {{ StatusSensoren[item] }} Tagen
    {% endfor %}
    ```
  
    *Ausgabe:*

    ```yaml
    braune Tonne: in 5 Tagen
    blaue Tonne: in 5 Tagen
    gelber Sack: in 12 Tagen
    schwarze Tonne: in 5 Tagen
    Grünabfall 1: in 14 Tagen
    Grünabfall 2: in 21 Tagen
    Grünabfall 3: in 28 Tagen
    Grünabfall 4: in 35 Tagen
    Sondermüll 1: in 19 Tagen
    Sondermüll 2: in 110 Tagen
    blauer Container: in 6 Tagen
    Tannenbaum: in unknown Tagen
    ```
  
    Es werden hier alle Abfallarten angezeigt. Es sollen jedoch nur diejenigen Abfallarten angezeigt werden, welche an einem bestimmten Tag (heute, morgen, übermorgen oder in X Tagen) abgeholt werden. Hierbei entspricht die Zahl **0** `heute`, die Zahl **1** `morgen`, die Zahl **2** `übermorgen` und jede andere Zahl `in [Zahl] Tagen`.
    **Beispiel: Bedingungen (if...endif)**
  
    ```yaml
    {% for item in StatusSensoren -%}
      {%- if StatusSensoren[item] == '5' %}
        {{- item -}} {{- "\n" -}}
      {%- endif -%}
    {% endfor %}
    ```
  
    *Ausgabe:*
  
    ```yaml
    braune Tonne
    blaue Tonne
    schwarze Tonne
    ```
  
    Das Ergebnis sieht zwar relativ ansprechend aus, richtig arbeiten kann man allerdings noch nicht damit. Ein ansprechendes Formatieren ist hier nahezu unmöglich und die Verwendung der `{{ "\n" }}` Print-Anweisung äußerst unschön.
  
    **Beispiel: Bedingungen (if...else...endif)**
    Im ersten Beispiel wird bei ***Tannenbaum*** `in unknown Tagen` angezeigt - immer noch. Dies ist in diesem Fall leider logisch und richtig, da der Tannenbaum nur einmal im Jahr abgeholt wird - zumeist in der zweiten Januarwoche - und deswegen in diesem Kalenderjahr nicht mehr aufgeführt wird, somit nicht mehr zu finden ist und deswegen richtigerweise als *'unbekannt'* aufgeführt wird.
    Um dieses unschöne *unknown* jedoch loszuwerden, muss eine Bedingung in diesen Code eingefügt werden :
  
    ```yaml
    {% for item in StatusSensoren -%}
      {{- item -}} :
      {%- if (item == 'Tannenbaum' and StatusSensoren[item] == 'unknown') %}
        nächstes Jahr
      {%- else %}
        in {{StatusSensoren[item]}} Tagen
      {%- endif %}
    {% endfor %}
    ```
  
    *Ausgabe :*
  
    ```yaml
    braune Tonne: in 5 Tagen
    blaue Tonne: in 5 Tagen
    gelber Sack: in 12 Tagen
    schwarze Tonne: in 5 Tagen
    Grünabfall 1: in 14 Tagen
    Grünabfall 2: in 21 Tagen
    Grünabfall 3: in 28 Tagen
    Grünabfall 4: in 35 Tagen
    Sondermüll 1: in 19 Tagen
    Sondermüll 2: in 110 Tagen
    blauer Container: in 6 Tagen
    Tannenbaum: nächstes Jahr
    ```
  
    **Beispiel: Listen einsetzen, füllen und verwenden**
    Wie man aussortiert, um die relevanten Daten anzuzeigen, ist jetzt bekannt. Formatieren lassen sich diese Ergebnisse allerdings nur bedingt. Um mit diesen Ergebnissen richtig gut arbeiten zu können, werden diese in eine Liste gepackt.
    Mittels Filtern wie beispielsweise `join()` oder Funktionen wie `loop()` können die Ergebnisse relativ gut formatiert werden:
  
    ```yaml
    {% for item in StatusSensoren %}
      {%- if StatusSensoren[item] == "5" -%}
        {% set SensorDeadLine.key = SensorDeadLine.key + [item] %}
      {%- endif -%}
    {% endfor %}
    {{- SensorDeadLine.key | join(', ') }} bitte heute bereitstellen !
    ```
  
    *Ausgabe :*
  
    ```yaml
    braune Tonne, blaue Tonne, schwarze Tonne bitte heute bereitstellen !
    ```
  
    Das ist bereits fast eine gute Textausgabe, welche man ohne schlechten Gewissens verwenden kann. Es geht aber noch besser:
    der Einsatz der Funktion `loop()` beispielsweise leistet für diese Art Formatierung sehr gute Unterstützung:
  
    ```yaml
    {% for item in StatusSensoren %}
      {%- if StatusSensoren[item] == "5" -%}
        {% set SensorDeadLine.key = SensorDeadLine.key + [item] %}
      {%- endif -%}
    {% endfor %}
   
    {% for item in SensorDeadLine.key %}
      {%- if not loop.first -%}
        {%- if loop.last %} und {% else -%}, {% endif -%}
      {%- endif -%}
      {{ item }}
    {%- endfor %} bitte heute bereitstellen !
    ```
  
    *Ausgabe:*
  
    ```yaml
    braune Tonne, blaue Tonne und schwarze Tonne bitte heute bereitstellen !
    ```

3. Damit sollte die Basis gelegt sein, um (reine) ***Textausgaben*** der Sensorwerte in einer beliebigen Karte einzubinden.  
    Bei dieser großen Anzahl an Kartentypen ist für reichlich Vielfalt gesorgt, um einen Kartentyp zu finden, welcher letztendlich den persönlichen Ansprüchen und Bedürfnissen gerecht werden wird. Zuvor jedoch muss ein sogenanntes Text-Template als Sensor erstellt, und somit bereitgestellt werden, welches beispielsweise in einem Pop-up zum Einsatz kommen kann.
    Um dieses Text-Template als Sensor zu erstellen, ist lediglich der nachfolgende Code-Block an das Ende der Datei `wcs-template--erinnerung-ebs-abfuhr.yaml` einzufügen :
  
    ```yaml
    - name: Text-Erinnerung EBS-Abfuhr
      unique_id: text_erinnerung_ebsabfuhr
      icon: mdi:trash-can-outline
      state: >
        {% set StatusSensoren = {
        'braune Tonne': states.sensor.braune_tonne.state,
        'blaue Tonne': states.sensor.blaue_tonne.state,
        'gelber Sack': states.sensor.gelber_sack.state,
        'blauer Container': states.sensor.blauer_container.state,
        'Grünabfall 1': states.sensor.grunabfall_1.state,
        'Grünabfall 2': states.sensor.grunabfall_2.state,
        'Grünabfall 3': states.sensor.grunabfall_3.state,
        'Grünabfall 4': states.sensor.grunabfall_4.state,
        'schwarze Tonne': states.sensor.schwarze_tonne.state,
        'Sonderabfall 1': states.sensor.sonderabfall_1.state,
        'Sonderabfall 2': states.sensor.sonderabfall_2.state,
        'Tannenbaum': states.sensor.tannenbaum.state }
        %}
        {%- set SensorDeadLine = namespace(key=[]) %}
        {% for item in StatusSensoren %}
        {%- if StatusSensoren[item] == '1' -%}  {# 1: wird morgen abgeholt, also heute die Erinnerung #}
        {% set SensorDeadLine.key = SensorDeadLine.key + [item] %}
        {%- endif -%}
        {% endfor %}
        {% if SensorDeadLine.key -%} {{ states('sensor.erinnerung_ebsabfuhr') }} {% endif %}
    ```
  
    Die Datei `wcs-template--erinnerung-ebsabfuhr.yaml` sollte letztendlich nachfolgenden Inhalt haben :
  
    ```yaml
    ## Erinnerung EBS-Abfuhr
   
    - name: Erinnerung EBS-Abfuhr
      unique_id: erinnerung_ebsabfuhr
      icon: mdi:trash-can-outline
      state: >
        {% set StatusSensoren = {
        'braune Tonne': states.sensor.braune_tonne.state,
        'blaue Tonne': states.sensor.blaue_tonne.state,
        'gelber Sack': states.sensor.gelber_sack.state,
        'blauer Container': states.sensor.blauer_container.state,
        'Grünabfall 1': states.sensor.grunabfall_1.state,
        'Grünabfall 2': states.sensor.grunabfall_2.state,
        'Grünabfall 3': states.sensor.grunabfall_3.state,
        'Grünabfall 4': states.sensor.grunabfall_4.state,
        'schwarze Tonne': states.sensor.schwarze_tonne.state,
        'Sonderabfall 1': states.sensor.sonderabfall_1.state,
        'Sonderabfall 2': states.sensor.sonderabfall_2.state,
        'Tannenbaum': states.sensor.tannenbaum.state }
        %}
        {%- set SensorDeadLine = namespace(key=[]) %}
        {% for item in StatusSensoren %}
        {%- if StatusSensoren[item] == '1'-%}  {# 1: wird morgen abgeholt, also heute die Erinnerung #}
        {% set SensorDeadLine.key = SensorDeadLine.key + [item] %}
        {%- endif -%}
        {% endfor %}
        {% for item in SensorDeadLine.key -%}
        {% if not loop.first %}{% if loop.last %} und {% else %}, {% endif %}{% endif %}{{ item }}
        {%- endfor %}
        {%- if SensorDeadLine.key %} bitte heute bereitstellen !{%- endif %}

    ## JINJA - Text-Template
    - name: Text-Erinnerung EBS-Abfuhr
      unique_id: text_erinnerung_ebsabfuhr
      icon: mdi:trash-can-outline
      state: >
        {% set StatusSensoren = {
        'braune Tonne': states.sensor.braune_tonne.state,
        'blaue Tonne': states.sensor.blaue_tonne.state,
        'gelber Sack': states.sensor.gelber_sack.state,
        'blauer Container': states.sensor.blauer_container.state,
        'Grünabfall 1': states.sensor.grunabfall_1.state,
        'Grünabfall 2': states.sensor.grunabfall_2.state,
        'Grünabfall 3': states.sensor.grunabfall_3.state,
        'Grünabfall 4': states.sensor.grunabfall_4.state,
        'schwarze Tonne': states.sensor.schwarze_tonne.state,
        'Sonderabfall 1': states.sensor.sonderabfall_1.state,
        'Sonderabfall 2': states.sensor.sonderabfall_2.state,
        'Tannenbaum': states.sensor.tannenbaum.state }
        %}
        {%- set SensorDeadLine = namespace(key=[]) %}
        {% for item in StatusSensoren %}
        {%- if StatusSensoren[item] == '1' -%}  {# 1: wird morgen abgeholt, also heute die Erinnerung #}
        {% set SensorDeadLine.key = SensorDeadLine.key + [item] %}
        {%- endif -%}
        {% endfor %}
        {% if SensorDeadLine.key -%} {{ states('sensor.erinnerung_ebsabfuhr') }} {% endif %}
    ```
  
    HA → Werkzeuge → Konfiguration prüfen → OK ! → neu starten
4. Im Standard-Dashboard sollte die Textmeldung erscheinen, falls `if StatusSensoren[item] == "5"` ein Ergebnis liefert.
   Zum Überprüfen der Funktionalität deswegen vorübergehend eine Zahl einsetzen, die auch Ergebnisse liefert. Damit ist `Waste Collection Schedule` installiert und konfiguriert.
5. **Überprüfung** :  
   HA → Werkzeuge→ Zustände → nach `text` filtern  
   ![Zustand des Template-Sensors sensor.text_erinnerung_ebs_abfuhr](pictures/textsensor_erinnerung.png)*Abbildung: Zustand des Template-Sensors sensor.text_erinnerung_ebs_abfuhr*

   Diese Überprüfung zeigt, dass der Zustand des Text-Sensors richtig interpretiert wird.

## Visualisierung

Nachfolgend ein Beispiel(-Code), wie man dies auch grafisch darstellen kann.

Der das Template betreffende Code muss nur noch in ein bestehendes Dashboard eingebunden werden, nachdem die Sensorennamen angepasst, und die entsprechenden Bilddateien in das Verzeichnis `config/www/img/wcs` beziehungsweise `local/img/wcs` (`config/www` = `local`) abgelegt worden sind:

**Hinweis:**
Der Code besteht aus `HTML`, `CSS` und `JINGA2`, weswegen die Visualisierung mittels einer sogenannten ***custom:html-template-card*** realisiert worden ist. Man kann den kompletten Code, so wie er ist, im Raw-Editor eines **neuen** Dashboards einfügen:

```yaml
views:
  - type: sections
    sections:
      - type: grid
        cards:
          - type: heading
            heading: Neuer Abschnitt
          - type: custom:html-template-card
            ignore_line_breaks: true
            content: >
              {%- set aktuell_datum = now().date() -%} {#
                {%- set StatusSensoren = {
                'braune Tonne': states.sensor.braune_tonne.state,
                'blaue Tonne': states.sensor.blaue_tonne.state,
                'gelber Sack': states.sensor.gelber_sack.state,
                'blauer Container': states.sensor.blauer_container.state,
                'Grünabfall 1': states.sensor.grunabfall_1.state,
                'Grünabfall 2': states.sensor.grunabfall_2.state,
                'Grünabfall 3': states.sensor.grunabfall_3.state,
                'Grünabfall 4': states.sensor.grunabfall_4.state,
                'schwarze Tonne': states.sensor.schwarze_tonne.state,
                'Sonderabfall 1': states.sensor.sonderabfall_1.state,
                'Sonderabfall 2': states.sensor.sonderabfall_2.state,
                'Tannenbaum': states.sensor.tannenbaum.state }
                -%}
              #} {%- set StatusSensoren = {
                  'braune Tonne': states.sensor.braune_tonne.state,
                  'blaue Tonne': states.sensor.blaue_tonne.state,
                  'gelber Sack': states.sensor.gelber_sack.state,
                  'schwarze Tonne': states.sensor.schwarze_tonne.state,
                  'Tannenbaum': states.sensor.tannenbaum.state }
                  -%}
              {%- set SensorDeadLine = namespace(key=[]) -%} {%- for item in
              StatusSensoren -%}
                {%- if StatusSensoren[item] == '1'-%}
                  {# 1: wird morgen abgeholt, also heute die Erinnerung #}
                  {%- set SensorDeadLine.key = SensorDeadLine.key + [item] -%}
                {%- endif -%} 
              {%- endfor -%} {# ------ DEBUGGING -------- 
                {{SensorDeadLine.key}}
                ---------------------------- #}
              <table id='ebs_table'>
                <tr>
                  <td colspan='2' class='ebs_titel'>EBS-Speyer</td>
                </tr>
                <tr>
                  <td colspan='2' class='line'></td>
                </tr>
              {%- if SensorDeadLine.key -%}
                <tr>
                  <td colspan='2'>
                    <table id='ebs_inner_table'>
                      <tr>
                        <td class='ebs_heute'>
                          <div class="blink">Bereitstellen</div>
                {%- for item in SensorDeadLine.key -%}
                  {%- if item == 'braune Tonne' -%}
                    {%- set item ='<img src="/local/img/wcs/EBS-braune-tonne.svg">' -%}
                  {%- elif item == 'blaue Tonne' -%}
                    {%- set item ='<img src="/local/img/wcs/EBS-blaue-tonne.svg">' -%}
                  {%- elif item == 'gelber Sack'-%}
                    {%- set item ='<img src="/local/img/wcs/EBS-gelber-sack.svg">' -%}
                  {%- elif item == 'blauer Container' -%}
                    {%- set item ='<img src="/local/img/wcs/EBS-blauer-container.svg">' -%}
                  {%- elif item == 'Grünabfall 1' -%}
                    {%- set item ='<img src="/local/img/wcs/EBS-grunabfall-1.svg">' -%}
                  {%- elif item == 'Grünabfall 2' -%}
                    {%- set item ='<img src="/local/img/wcs/EBS-grunabfall-2.svg">' -%}
                  {%- elif item == 'Grünabfall 3' -%}
                    {%- set item ='<img src="/local/img/wcs/EBS-grunabfall-3.svg">' -%}
                  {%- elif item == 'Grünabfall 4' -%}
                    {%- set item ='<img src="/local/img/wcs/EBS-grunabfall-4.svg">' -%}
                  {%- elif item == 'schwarze Tonne' -%}
                    {%- set item ='<img src="/local/img/wcs/EBS-schwarze-tonne.svg">' -%}
                  {%- elif item == 'Sonderabfall 1' -%}
                    {%- set item ='<img src="/local/img/wcs/EBS-sonderabfall-1.svg">' -%}
                  {%- elif item == 'Sonderabfall 2' -%}
                    {%- set item ='<img src="/local/img/wcs/EBS-sonderabfall-2.svg">' -%}
                  {%- elif item == 'Tannenbaum' -%}
                    {%- set item ='<img src="/local/img/wcs/EBS-tannenbaum.svg">' -%}
                  {%- endif -%}
                  {{- item -}}
                {%- endfor -%}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              {%- else -%}
                <tr>
                  <td class='ebs_art'>braune Tonne</td>
                  <td class='ebs_tage'>
                {%- if states('sensor.braune_tonne') == '2' -%}
                  Morgen
                {%- else -%}
                  Tage <span id="ebs_tage">{{states('sensor.braune_tonne')}}</span>
                {%- endif -%}
                  </td>
                </tr>
                <tr>
                  <td class='ebs_art'>blaue Tonne</td>
                  <td class='ebs_tage'>
                {%- if states('sensor.blaue_tonne') == '2' -%}
                  Morgen
                {%- else -%}
                  Tage <span id="ebs_tage">{{states('sensor.blaue_tonne')}}</span>
                {%- endif -%}
                  </td>
                </tr>
                <tr>
                  <td class='ebs_art'>schwarze Tonne</td>
                  <td class='ebs_tage'>
                {%- if states('sensor.schwarze_tonne') == '2' -%}
                  Morgen
                {%- else -%}
                  Tage <span id="ebs_tage">{{states('sensor.schwarze_tonne')}}</span>
                {%- endif -%}
                  </td>
                </tr>
                <tr>
                  <td class='ebs_art'>gelber Sack</td>
                  <td class='ebs_tage'>
                {%- if states('sensor.gelber_Sack') == '2' -%}
                  Morgen
                {%- else -%}
                  Tage <span id="ebs_tage">{{states('sensor.gelber_Sack')}}</span>
                {%- endif -%}
                  </td>
                </tr>
                <tr>
                  <td class='ebs_art'>Tannenbaum</td>
                {%- if states('sensor.tannenbaum') == 'unknown' -%}
                  <td class='ebs_tage'> <span id='ebs_jahr'>Jahr</span> <span id='ebs_tage'>{{aktuell_datum.year +1}}</span></td>
                {%- else -%}
                  <td class='ebs_tage'>
                  {%- if states('sensor.tannenbaum') == '2' -%}
                    Morgen
                  {%- else -%}
                    Tage <span id='ebs_tage'>{{- states('sensor.tannenbaum') -}}</span>
                  {%- endif -%}
                  </td>
                {%- endif -%}
                </tr>
              {%- endif -%} </table>

```

So könnte beispielsweise eine Übersicht der wichtigen Abfallarten aussehen:
![Übersicht der nächsten Entsorgung-Termine der unterschiedlichen Abfallarten](pictures/Dashboard---WCS--Termin_Abholung.png)
*Abbildung: Übersicht der nächsten Entsorgung-Termine der unterschiedlichen Abfallarten*

Und so könnte beispielsweise eine Erinnerung für das Herausstellen der Abfallbehälter aussehen:
![Erinnerung zur Abholung der entsprechenden Müllbehälter](pictures/Dashboard---WCS--Erinnerung_Abholung.png)
*Abbildung: Erinnerung zur Abholung der entsprechenden Müllbehälter*

Herzlichen Glückwunsch !
