# MZV Rotenburg

Support for schedules provided by [MZV Rotenburg](https://www.mzv-rotenburg-bebra.de), serving Bebra, Ronshausen, Rotenburg an der Fulda, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: mzv_rotenburg_bebra_de
      args:
        city: CITY (Stadt/Ort)
        yellow_route: "YELLOW ROUTE (Rutennummer für Gelbe Tonne)"
        paper_route: PAPER ROUTE (Rute für Blaue Tonne)
        
```

### Configuration Variables

**city**  
*(String) (required)*  
Short form of you city. It should match the URL parameter of the ics link of your city here: <https://www.mzv-rotenburg-bebra.de//webapp.html>

**yellow_route**  
*(String) (optional)*  
Used if there are multiple routes for the yellow bin collection. E.g 'Rotenburg - Kernstadt' has yellow bin collection routes `1`,`2`,`3` and `4`.

**paper_route**  
*(String) (optional)*  
Used if there are multiple routes for the paper collection. E.g 'Rotenburg - Kernstadt' has paper collection routes `West` and `Ost`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: mzv_rotenburg_bebra_de
      args:
        city: Rotenburg an der Fulda
        yellow_route: "2"
        paper_route: Ost
```
