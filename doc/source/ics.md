# ICS

Add support for generic ICS file which are downloaded from a fix location. The waste type will be taken from the `summary` attribute.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: URL
```

### Configuration Variables

**url**<br>
*(string) (required)*
If the original url contains the current year (4 digits including century), this can be replaced by the wildcard `{%Y}` (see example below).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://www.avl-ludwigsburg.de/fileadmin/Files/Abfallkalender/ICS/Privat/Privat_{%Y}_Ossweil.ics"
```

