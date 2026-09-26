# SISMS.pl / BLISKO

Support for schedules provided by [SISMS.pl / BLISKO](https://sisms.pl).

Source for SISMS.pl / BLISKO.

## Configuration via configuration.yaml

### Using owner

```yaml
waste_collection_schedule:
  sources:
    - name: sims_pl
      args:
        town: TOWN
        owner: OWNER
```

### Using owner_id

```yaml
waste_collection_schedule:
  sources:
    - name: sims_pl
      args:
        town: TOWN
        owner_id: OWNER_ID
```

### Configuration Variables

**owner**  
*(string) (alternative)*

**owner_id**  
*(string) (alternative)*

**town**  
*(string) (required)*

**town_address**  
*(string) (optional)*

**street**  
*(string) (optional)*

**street_address**  
*(string) (optional)*

Provide one of: `owner` or `owner_id`.

## Example

### Using owner

```yaml
waste_collection_schedule:
  sources:
    - name: sims_pl
      args:
        town: Ciemniki
        owner: "Je\u017Cewo"
```

### Using owner_id

```yaml
waste_collection_schedule:
  sources:
    - name: sims_pl
      args:
        town: Bobrza
        owner_id: 188
```

## How to get the source arguments

Owner: your gmina as listed (or its numeric owner id, which the search page at https://sisms.pl requests as ownerId). Town: your town (Miejscowość). Then either the house number in the town, or the street (Ulica) and house number (Numer domu).
