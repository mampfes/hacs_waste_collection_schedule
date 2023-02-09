# zaw-online

Support for schedules provided by [zaw-online.de](https://ead.darmstadt.de/) for Darmstadt Dieburg located in Hesse, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zaw_online_de
      args:
        city: MQ
        street: Nzc0MQ
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## How to get the source arguments

Visit [Abfallkalender](https://www.zaw-online.de/service/abfallkalender`) and select your city and street. Press F12 or rightclick -> inspect to view the source code of the Page. Search for the `<select>` tag for the city and street. The `street` and `city` arguments should be the value parameter of the corresponding `<select>` tag.
