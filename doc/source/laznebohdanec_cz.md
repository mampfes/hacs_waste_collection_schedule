# Lázně Bohdaneč

Support for schedules provided by [Lázně Bohdaneč](https://lazne.bohdanec.cz/svozovy%2Dkalendar/ms-2523).

Source of city waste collection calendar (paper/plastic/mixed) of Lázně Bohdaneč.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: laznebohdanec_cz
      args:
        url: URL
        file: FILE
```

### Configuration Variables

**url**  
*(string) (optional)*

**file**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: laznebohdanec_cz
```

## How to get the source arguments

By default no arguments are required. The integration will automatically
retrieve the current XLSX link from the official city page (Lázně Bohdaneč
website, sections "Odpady" -> "Svozový kalendář").
* If you want to pin the exact URL, open that page, click the XLSX download link,
  copy the direct XLSX URL, and use it as `url`.
* As a fallback you can download the file and use a local `file` path. Beware you need to manually upload file to HA.
* If you enable dedicated calendars per waste type, set colors per calendar in the HA calendar UI.
