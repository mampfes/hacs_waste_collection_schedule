# Straatbeeld Online

Support for schedules provided by [Straatbeeld Online](https://afvalkalender.straatbeeld.online).

Source for Straatbeeld Online (afvalkalender.straatbeeld.online), a waste calendar platform used by several Dutch municipalities (e.g. Gemeente Drimmelen, Gemeente Geertruidenberg).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: straatbeeld_online
      args:
        municipality: MUNICIPALITY
        postal_code: POSTAL_CODE
        house_number: HOUSE_NUMBER
        house_letter: HOUSE_LETTER
```

### Configuration Variables

**municipality**  
*(string) (required)*

**postal_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

**house_letter**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: straatbeeld_online
      args:
        municipality: drimmelen
        postal_code: 4926CW
        house_number: '28'
```

## How to get the source arguments

Open your municipality's Straatbeeld Online waste calendar (e.g. https://drimmelen.afvalkalender.straatbeeld.online), the 'municipality' argument is the first part of that URL (e.g. 'drimmelen'). Use the same postal code and house number you would enter on that page. Add a house letter or addition only when several addresses share the same postal code and house number.
