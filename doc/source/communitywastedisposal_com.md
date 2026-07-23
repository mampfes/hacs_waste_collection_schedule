# Community Waste Disposal (CWD)

Support for schedules provided by [Community Waste Disposal (CWD)](https://www.communitywastedisposal.com), serving 39 cities in North Texas, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: communitywastedisposal_com
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
_(String) (required)_

Street address including city and ZIP code.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: communitywastedisposal_com
      args:
        address: "123 Main St, Allen, TX 75002"
```

## How to get the source argument

Visit the [CWD View My Schedule](https://www.communitywastedisposal.com/view-my-schedule/) page and enter your address to verify your service area and collection days.

Supported cities include: Addison, Allen, Anna, Balch Springs, Blue Ridge, Celina, Crandall, Fairview, Farmersville, Fate, Forney, Frisco, Garland, Heath, Josephine, Kaufman, Keller, Lavon, Lucas, McKinney, McLendon-Chisholm, Melissa, Murphy, Nevada, Parker, Plano, Princeton, Prosper, Richardson, Rockwall, Rowlett, Royse City, Sachse, Seagoville, Southlake, St. Paul, Talty, Terrell, and Wylie.

## Limitations

Some waste streams are "call to schedule" rather than an automatic recurring pickup (e.g. Household Hazardous Waste in most zones) — these are not returned, since there is no fixed recurring date to report. Likewise, some Monthly/BiMonthly streams don't specify which week of the month they fall on in CWD's public route data; those are also omitted rather than guessed.
