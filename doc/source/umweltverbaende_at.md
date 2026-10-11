# Die NÖ Umweltverbände

Support for schedules provided by [Die NÖ Umweltverbände](https://www.umweltverbaende.at/).

Consolidated waste collection provider for several districts in Lower Austria

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: umweltverbaende_at
      args:
        district: DISTRICT
        municipal: MUNICIPAL
        town: TOWN
        plz: PLZ
        street: STREET
        hnr: HNR
        addition: ADDITION
        calendar: CALENDAR
        calendar_title_separator: CALENDAR_TITLE_SEPARATOR
        calendar_splitter: CALENDAR_SPLITTER
```

### Configuration Variables

**district**  
*(string) (required)*

**municipal**  
*(string) (required)*

**town**  
*(string) (optional)*

**plz**  
*(string) (optional)*

**street**  
*(string) (optional)*

**hnr**  
*(string) (optional)*

**addition**  
*(string) (optional)*

**calendar**  
*(string) (optional)*

**calendar_title_separator**  
*(string) (optional)*

**calendar_splitter**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: umweltverbaende_at
      args:
        district: baden
        municipal: Hernstein
        calendar: ICS Hernstein
```

## How to get the source arguments

Choose your district (the subdomain of its `umweltverbaende.at` site) and municipality. The district sites come in two kinds: an old one (light blue header, green buttons) and a new one (dark blue header). Old site: if your municipality lists several collection calendars (streets or Rayons), set `calendar` to the name as spelt on the Abholtermine page below `Kalenderansicht`; rarely, `calendar_title_separator` (default `:`) separates the calendar title from the waste type and `calendar_splitter` separates several types listed in one line. New site: `town`, `plz`, `street`, `hnr` and `addition` are rarely needed, set them only when you get an error without them; the error lists the valid values. Scheibbs publishes PDF files only and Stadt Krems has its own ICS source.
