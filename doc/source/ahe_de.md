# AHE Ennepe-Ruhr-Kreis

Support for schedules provided by [AHE Ennepe-Ruhr-Kreis](https://ahe.de), serving Ennepe-Ruhr-Kreis, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ahe_de
      args:
        plz: POSTLEITZAHL
        strasse: STRAßE
        hnr: HAUSNUMMER
        
```

### Configuration Variables

**plz**  
*(String | Integer) (required)*

**strasse**  
*(String) (required)*

**hnr**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: ahe_de
      args:
        plz: 58300
        strasse: Ahornstraße
        hnr: 1
        
```

## How to get the source argument

Find the parameter of your address using [https://ahe.atino.net/pickup-dates](https://ahe.atino.net/pickup-dates) and write them exactly like on the web page.
