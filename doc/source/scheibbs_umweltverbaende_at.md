# GVU Scheibbs

Support for schedules provided by [GVU Scheibbs](https://scheibbs.umweltverbaende.at/).

Source for the municipalities of the Gemeindeverband für Umweltschutz im Bezirk Scheibbs, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: scheibbs_umweltverbaende_at
      args:
        region: REGION
        bio_bin: BIO_BIN
        lackenhof: LACKENHOF
        additional_collections: ADDITIONAL_COLLECTIONS
```

### Configuration Variables

**region**  
*(string) (required)*

**bio_bin**  
*(string) (optional)*

**lackenhof**  
*(string) (optional)*

**additional_collections**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: scheibbs_umweltverbaende_at
      args:
        region: Gaming
```

## How to get the source arguments

Enter your municipality as linked on https://scheibbs.umweltverbaende.at/entsorgung-und-termine/abholtermine/ without 'Abfuhrtermine' and 'Stadtgemeinde', with 'St.' spelt out as 'Sankt', e.g. 'Gaming' or 'Sankt Anton an der Jeßnitz'. Choose '20' as bio_bin if your bio bin is emptied 20 times a year (BIO/20) rather than 40, tick lackenhof in Lackenhof (Gaming), and tick additional_collections if you registered for the additional general waste and paper dates (R2, P4). Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
