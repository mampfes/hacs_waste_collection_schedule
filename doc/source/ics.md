# ICS

Add support for generic ICS file which are downloaded from a fix location. The waste type will be taken from the `summary` attribute.

This source has been successfully tested with the following service providers:

- [Abfall Landkreis Stade](https://abfall.landkreis-stade.de/)
- [AVL Ludwigsburg](https://www.avl-ludwigsburg.de/)
- [AWB Esslingen](https://www.awb-es.de/)
- [AWM München](https://www.awm-muenchen.de)
- [EDG Entsorgung Dortmund](https://www.edg.de/)
- [Stadtreinigung Leipzig](https://www.stadtreinigung-leipzig.de/)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: URL
        file: FILE
        offset: OFFSET
```

### Configuration Variables

**url**<br>
*(string) (optional)*

URL to ICS file. File will be downloaded using a HTTP GET command.

If the original url contains the current year (4 digits including century), this can be replaced by the wildcard `{%Y}` (see example below).

You have to specify either `url` or `file`!

**file**<br>
*(string) (optional)*

Local ICS file name. Can be used instead of `url` for local files.

You have to specify either `url` or `file`!

**offset**<br>
*(int) (optional, default: `0`)*

Offset in days which will be added to every start time. Can be used if the start time of the events in the ICS file are ahead of the actual date.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://www.avl-ludwigsburg.de/fileadmin/Files/Abfallkalender/ICS/Privat/Privat_{%Y}_Ossweil.ics"
        offset: 1
```

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        file: "test.ics"
```

