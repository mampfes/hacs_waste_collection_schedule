# Lázně Bohdaneč - Czech Republic

Support for schedules provided by the city of Lázně Bohdaneč (CZ).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: laznebohdanec_cz
      args:
        # url: "https://lazne.bohdanec.cz/assets/File.ashx?id_org=617&id_dokumenty=5683"
        # official_page_url: "https://lazne.bohdanec.cz/svozovy%2Dkalendar/ms-2523/p1=2523"
        # file: "/config/laznebohdanec.xlsx"
```

### Configuration Variables

**official_page_url**  
*(string)* Official city page containing the XLSX download link (auto-used by default). Hardcoded, it is listed here as reference.

**url**  
*(string)* Direct URL to the XLSX calendar file.

**file**  
*(string)* Path to a local XLSX calendar file (fallback if `url` is not set).  
Place the file inside your Home Assistant config directory and reference it with the full path, e.g. `/config/laznebohdanec.xlsx`.

## Example
```yaml
waste_collection_schedule:
  sources:
    - name: laznebohdanec_cz
      args: {}

sensor:
  - platform: waste_collection_schedule
    name: "Svoz papíru"
    types:
      - "Papír"
    add_days_to: true
  - platform: waste_collection_schedule
    name: "Svoz plastů"
    types:
      - "Plast"
    add_days_to: true
  - platform: waste_collection_schedule
    name: "Svoz komunálního odpadu"
    types:
      - "Komunální odpad"
    add_days_to: true
```

## How to get the configuration arguments

1. Open the city page with the waste calendar:
   https://lazne.bohdanec.cz/svozovy%2Dkalendar/ms-2523/p1=2523
2. By default no arguments are required. The integration will automatically retrieve the current XLSX link from the official city page.
3. If you want to pin the exact URL, click the download link for the XLSX file.
4. Copy the direct XLSX URL and use it as the `url` parameter.

The direct document link can change (e.g. on yearly update), autodetection should handle that. When you use a direct link, you need to update the URL and reconfigure/reload the service.
You can also download the XLSX and use a local `file` path.


## Czech notes
### Barvy kalendáře (dedikované kalendáře)

Pokud zapnete dedikované kalendáře pro každý typ odpadu (Papír, Plast, Komunální odpad), nastavte barvy zvlášť pro každý kalendář v UI Home Assistantu. Integrace barvy nenastavuje.

### Jak získat konfigurační hodnoty

1. Otevřete stránku města se svozovým kalendářem:
   https://lazne.bohdanec.cz/svozovy%2Dkalendar/ms-2523/p1=2523
2. Ve výchozím stavu nejsou potřeba žádné argumenty. Integrace si automaticky najde aktuální odkaz na XLSX na oficiální městské stránce.
3. Pokud chcete URL zafixovat, klikněte na odkaz pro stažení XLSX souboru (kalendáře).
4. Zkopírujte přímý odkaz na XLSX a použijte ho jako `url` v konfiguraci.

Pokud město dokument aktualizuje, přímý odkaz na dokument se může změnit. Pokud používáte manuální odkaz a nikoliv autodetekci, tak je potřeba URL upravit a službu znovu nakonfigurovat/načíst.
Pokud chcete, stáhněte XLSX a použijte lokální cestu přes `file`, ale je potřeba nahrát soubor také do HA.
