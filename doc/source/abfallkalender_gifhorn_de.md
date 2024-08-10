# Landkreis Gifhorn

Support for schedules provided by [Landkreis Gifhorn](https://www.abfallkalender-gifhorn.de), serving Landkreis Gifhorn, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: abfallkalender_gifhorn_de
      args:
        territory: TERRITORY (Gebietseinheit)
        street: STREET (Ort / Straße)
        
```

### Configuration Variables

**territory**  
*(String) (required)*

**street**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: abfallkalender_gifhorn_de
      args:
        territory: Wittingen
        street: Glüsingen
        
```

## How to get the source argument

Goto [https://www.abfallkalender-gifhorn.de](https://www.abfallkalender-gifhorn.de) and search for your region/address. The `territory` is the `Gebietseinheit` value and the `street` is the `Ort / Straße` value, make sure to write it exactly as shown in the drop down menu.
