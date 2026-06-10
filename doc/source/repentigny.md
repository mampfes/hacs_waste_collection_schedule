# Repentigny (QC)

Support for waste collection schedule for [Ville de Repentigny](https://repentigny.ca/services/citoyens/collectes) using the Quebec open data portal.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: repentigny_ca
      args:
        sector: YOUR_SECTOR
```

## Configuration Variables

**sector**  
*(string) (required)*
Your waste collection sector (A, B, C, D, E, or F). You can find your sector on the official Repentigny collection calendar. The sector is typically indicated in the legend or on the calendar for your address.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: repentigny_ca
      args:
        sector: A
```

## How to Find Your Sector

You can find your sector on the official Repentigny collection calendar. The sector is typically indicated in the legend or on the calendar for your address.

All sectors have the same collection types, but collection days may vary:

- **Sectors C and D**: Waste collection on Thursdays
- **Sectors A, B, E, and F**: Waste collection on Fridays

Recycling collection is every two weeks for all sectors.

Organic matter collection:
- **Sectors A and B**: Tuesdays (twice a month)
- **Sectors C, D, E, and F**: Wednesdays (twice a month)

Special collections (encombrants and branches) have specific dates for all sectors.

## Contact Information

For issues with collection service:
- Website: https://repentigny.ca/services/citoyens/collectes
- Email: info-environnement@repentigny.ca
- Phone: 450-470-3830
