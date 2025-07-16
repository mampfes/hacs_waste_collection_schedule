# BurgerPortaal

Support for schedules provided by [BurgerPortaal](https://21burgerportaal.mendixcloud.com/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: burgerportaal_nl
      args:
        organization: ORGANIZATION
        post_code: POST_CODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**organization**  
*(string) (required)*

Use one of the following codes as organization code:

- assen
- rmn

**post_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

**addition**  
*(string) (optional)*

For example if you house is `2A` you will put `A` here.

## Supported Operators

- `assen`: <https://21burgerportaal.mendixcloud.com/p/assen/landing/>
- `rmn`: <https://21burgerportaal.mendixcloud.com/p/rmn/landing/>

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: burgerportaal_nl
      args:
        organization: rmn
        post_code: 3437GN
        house_number: "3"
```

Eg. with addition:

```yaml
waste_collection_schedule:
  sources:
    - name: burgerportaal_nl
      args:
        organization: rmn
        post_code: 3437GS
        house_number: "2"
        addition: A
```
