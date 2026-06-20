# Vogel Disposal Service

Support for schedules provided by [Vogel Disposal Service](https://www.vogeldisposal.com/), serving municipalities in western Pennsylvania, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vogeldisposal_com
      args:
        municipality: MUNICIPALITY
        address: STREET_ADDRESS
```

### Configuration Variables

**municipality**  
*(string) (required)*

Your Vogel municipality. Exact spelling is not required — a rough name such as `butler twp` resolves to `BUTLER TWP, BUTLER COUNTY` automatically.

**address**  
*(string) (required)*

Your street address. A partial such as `1002 tudor` resolves to `1002 TUDOR DR` automatically.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vogeldisposal_com
      args:
        municipality: "BUTLER TWP, BUTLER COUNTY"
        address: "1002 TUDOR DR"
```

## How to get the source arguments

Just enter your municipality and street address roughly — the source resolves them to the exact values Vogel uses. If an entry matches more than one municipality or address, the configuration form lists the matching options so you can pick the right one. To see the canonical spellings, you can use the **Print Schedule** lookup on [vogeldisposal.com](https://www.vogeldisposal.com/).

The source returns weekly **Trash** collections and every-other-week **Recycling** collections. Holiday delays are applied automatically: when a holiday shifts your collection, the shifted date is reflected in the schedule.
