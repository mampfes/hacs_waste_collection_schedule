# Repentigny (QC)

Support for waste collection schedule for [Ville de Repentigny](https://repentigny.ca/services/citoyens/collectes) using the city's official calendar JSON.

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

Visit the [Repentigny collection calendar page](https://repentigny.ca/services/citoyens/collectes) and click the link to view the calendar PDF for the current year. Your sector (A through F) is indicated on the calendar legend. If you are unsure, contact the city with your address.

## Collection Types

This source returns all upcoming collection dates with actual dates from the city's calendar:

| Type | Description |
|------|-------------|
| Déchets | General waste (garbage) |
| Recyclables | Recycling (paper, cardboard, glass, metal, plastic) |
| Recyclables + surplus accepté | Recycling with extra accepted materials |
| Matières organiques | Organic waste (kitchen scraps) |
| Organiques + résidus verts | Organic waste including yard trimmings |
| Encombrants | Bulky waste (large items) |
| Branches | Branch/yard waste collection |
| Sapins | Christmas tree collection |

## Contact Information

For issues with collection service:
- Website: https://repentigny.ca/services/citoyens/collectes
- Email: info-environnement@repentigny.ca
- Phone: 450-470-3830
