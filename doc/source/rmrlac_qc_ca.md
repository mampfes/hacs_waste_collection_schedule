# RMR Lac-Saint-Jean (QC)

Support for schedules provided by [Régie des matières résiduelles du Lac-Saint-Jean](https://calendrier.rmrlac.qc.ca/calendrier-de-collectes).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rmrlac_qc_ca
      args:
        street_number_and_name: "1201 16e Chemin"
        locality: "Métabetchouan-Lac-à-la-Croix"
        province_or_state: "QC"
        language: "fr"
```

### Configuration Variables

**street_number_and_name**  
*(string) (required)*

Your street number and name (e.g. `"1201 16e Chemin"`).

**locality**  
*(string) (required)*

Your municipality name (e.g. `"Métabetchouan-Lac-à-la-Croix"`).

**province_or_state**  
*(string) (optional, default: `"QC"`)*
Province or state code.

**language**  
*(string) (optional, default: `"en"`)*
Language code for collection type names. Supported: `en` (Garbage/Recycling/Organic), `fr` (Déchets/Recyclage/Matières organiques).

## How to find your arguments

1. Visit [Calendrier de collectes](https://calendrier.rmrlac.qc.ca/calendrier-de-collectes).
2. Search for your address (e.g. `"1201 16e Chemin"`).
3. Note your street number and name as well as your municipality name.