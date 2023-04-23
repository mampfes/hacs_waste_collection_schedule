# Movar Norway

Support for schedules provided by [movar.no](https://movar.no/kalender.html) serving Våler, Råde, Moss and Vestby in Norway.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: movar_no
      args:
        address: Vålerveien 1148, Våler
```

### Configuration Variables

**address**  
*(string) (required)*

## How to get the source arguments

Visit [[movar.no](https://movar.no/kalender.html) and search your address. Make sure the address in your configuration is written exactly as it is in the search bar.