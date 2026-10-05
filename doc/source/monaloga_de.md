# AWISTA LOGISTIK Stadt Remscheid

Support for schedules provided by [AWISTA LOGISTIK Stadt Remscheid](https://www.monaloga.de/).

Source for AWISTA LOGISTIK Stadt Remscheid.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: monaloga_de
      args:
        street: STREET
        plz: PLZ
```

### Configuration Variables

**street**  
*(string) (required)*

**plz**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: monaloga_de
      args:
        street: "Adolf-Clarenbach-Stra\xDFe"
        plz: 42899
```

## How to get the source arguments

Enter your street as listed at https://www.monaloga.de/mportal/awista-logistik/stadt-remscheid/index.php. Add the postcode (PLZ) if the street name occurs in several postcodes.
