# AWISTA LOGISTIK Stadt Remscheid

Support for schedules provided by [AWISTA LOGISTIK Stadt Remscheid](https://www.monaloga.de/), serving Remscheid, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: monaloga_de
      args:
        street: STREET
        plz: "PLZ"
        
```

### Configuration Variables

**street**  
*(String) (required)*

**plz**  
*(String | Integer) (optional)*  
*The postal code of the address only use this if the street on the website shows a PLZ*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: monaloga_de
      args:
        street: Adolf-Clarenbach-Straße
        plz: "42899" 
```

## How to get the source argument

Find the parameter of your address using [https://www.monaloga.de/mportal/awista-logistik/stadt-remscheid/index.php](https://www.monaloga.de/mportal/awista-logistik/stadt-remscheid/index.php) and write them exactly like on the web page.
