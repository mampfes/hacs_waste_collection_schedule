# Straatbeeld Online

Support for schedules provided by [Straatbeeld Online](https://afvalkalender.straatbeeld.online), a waste calendar platform used by several Dutch municipalities, including Gemeente Drimmelen and Gemeente Geertruidenberg.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: straatbeeld_online
      args:
        municipality: MUNICIPALITY
        postal_code: POSTAL CODE
        house_number: HOUSE NUMBER
        house_letter: HOUSE LETTER (optional)
```

### Configuration Variables

**municipality**
*(String) (required)*

Subdomain of the municipality's waste calendar, e.g. `drimmelen` for `https://drimmelen.afvalkalender.straatbeeld.online`.

**postal_code**
*(String) (required)*

Dutch postal code, e.g. `4926CW`. Spaces are ignored.

**house_number**
*(String | Integer) (required)*

House number.

**house_letter**
*(String) (optional, default: `None`)*

House letter or addition. Only required when multiple addresses share the same postal code and house number.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: straatbeeld_online
      args:
        municipality: drimmelen
        postal_code: 4926CW
        house_number: "28"
```

## How to get the source arguments

Open your municipality's Straatbeeld Online waste calendar (e.g. <https://drimmelen.afvalkalender.straatbeeld.online>). The `municipality` argument is the first part of that URL (e.g. `drimmelen`). Use the same postal code and house number you would enter on that page.
