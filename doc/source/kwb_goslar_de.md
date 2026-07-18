# Kreiswirtschaftsbetriebe Goslar

Support for schedules provided by [Kreiswirtschaftsbetriebe Goslar](https://www.kwb-goslar.de).

Source for kwb-goslar.de waste collection.

## Configuration via configuration.yaml

### Using strasse

```yaml
waste_collection_schedule:
  sources:
    - name: kwb_goslar_de
      args:
        ort: ORT
        strasse: STRASSE
```

### Using pois

```yaml
waste_collection_schedule:
  sources:
    - name: kwb_goslar_de
      args:
        ort: ORT
        pois: POIS
```

### Configuration Variables

**strasse**  
*(string) (alternative)*

**pois**  
*(string) (alternative)*

**ort**  
*(string) (optional)*

Provide one of: `strasse` or `pois`.

## Example

### Using strasse

```yaml
waste_collection_schedule:
  sources:
    - name: kwb_goslar_de
      args:
        ort: Seesen
        strasse: "Marktstra\xDFe"
```

## How to get the source arguments

Enter your street (optionally with the place to disambiguate), or a direct POIS id if you already have one.
