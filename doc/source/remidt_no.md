# zaw-online

Support for schedules provided by [remidt.no](https://www.remidt.no/#!/main) serving Norway Orkland muni.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: remidt_no
      args:
        address: Follovegen 1 A
```

### Configuration Variables

**address**  
*(string) (required)*

## How to get the source arguments

Visit [remidt.no](https://www.remidt.no/#!/main) and make sure, address is written exactly like in the search bar.
