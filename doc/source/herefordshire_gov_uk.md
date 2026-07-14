# Herefordshire County Council

Support for schedules provided by [Herefordshire County
Council](https://www.herefordshire.gov.uk/environmental-protection/waste-management/refuse-household-bin-collection),
serving Herefordshire (UK).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: herefordshire_gov_uk
      args:
        post_code: POST_CODE
        number: NUMBER

```

### Configuration Variables

**POST_CODE**  
*(string) (required)*

Postcode of the property, e.g. `HR4 9JS`.

**NUMBER**  
*(string) (required)*

House number, house name, or UPRN (Unique Property Reference Number) of the
property. If your property only has a name and no number, enter the name
first. If it still cannot be found, the resulting error message will list
the full addresses found for your postcode, so you can copy the UPRN or the
exact house-name wording from there.

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: herefordshire_gov_uk
      args:
        post_code: "hr49js"
        number: "52"
```

```yaml
waste_collection_schedule:
    sources:
    - name: herefordshire_gov_uk
      args:
        post_code: "hr49js"
        number: "200002607460"
```
