# BurgerPortaal

Support for schedules provided by [BurgerPortaal](https://21burgerportaal.mendixcloud.com/).

Source for BurgerPortaal.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: burgerportaal_nl
      args:
        organization: ORGANIZATION
        post_code: POST_CODE
        house_number: HOUSE_NUMBER
        addition: ADDITION
```

### Configuration Variables

**organization**  
*(string) (required)*

**post_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

**addition**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: burgerportaal_nl
      args:
        organization: assen
        post_code: 9401LN
        house_number: 6
```
