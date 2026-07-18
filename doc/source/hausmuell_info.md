# hausmüll.info

Support for schedules provided by [hausmüll.info](https://hausmuell.info).

Source for hausmüll.info.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hausmuell_info
      args:
        subdomain: SUBDOMAIN
        ort: ORT
        ortsteil: ORTSTEIL
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**subdomain**  
*(string) (required)*

**ort**  
*(string) (optional)*

**ortsteil**  
*(string) (optional)*

**strasse**  
*(string) (optional)*

**hausnummer**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hausmuell_info
      args:
        ort: Dietzhausen
        strasse: Am Rain
        hausnummer: 10
        subdomain: ebkds
```
