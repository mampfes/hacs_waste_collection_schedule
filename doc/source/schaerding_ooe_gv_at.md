# Schärding

Support for schedules provided by [Schärding](https://www.schaerding.ooe.gv.at).

Source for Schärding, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: schaerding_ooe_gv_at
      args:
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: schaerding_ooe_gv_at
      args:
        strasse: "Adalbert-Stifter-Stra\xDFe"
        hausnummer: '1'
```
