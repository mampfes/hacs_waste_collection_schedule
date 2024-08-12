# Entsorgungstermine Jena, Germany

Support for schedules provided by [A-Region.ch](https://www.a-region.ch)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: entsorgungstermine_jena_de
      args:
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (required)*
## Examples

Municipality without extra districts:

```yaml
waste_collection_schedule:
  sources:
    - name: entsorgungstermine_jena_de
      args:
        strasse: Altenburger Straße
        hausnummer: 15-19
```

Municipality with extra districts:


## How to get the source argument

Open [Entsorgungstermine.jena](https://entsorgungstermine.jena.de/). Select your street from the dropdown.
afterwards select your house number.
