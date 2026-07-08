# eThekwini Municipality

Support for schedules provided by [eThekwini Municipality refuse collection schedules](https://www.durban.gov.za/page/refuse-collection-schedules).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: durban_gov_za
      args:
        region: REGION
        area: AREA
        recycling_in_even_week: RECYCLING_IN_EVEN_WEEK
```

### Configuration Variables

**region**  
*(string) (required)* Regional office area. One of: `outer_west`, `north`, `north_central`, `south`, `south_central`, `inner_west`.

**area**  
*(string) (required)* Suburb or collection area slug from your region's schedule DOCX (see below).

**recycling_in_even_week**  
*(bool) (optional, default: `True`)* Set to `True` if orange-bag recycling is collected on even ISO week numbers, `False` if collected on odd ISO week numbers. Check your last recycling collection date at [whatweekisit.org](https://whatweekisit.org/) to determine this.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: durban_gov_za
      args:
        region: outer_west
        area: hillcrest
        recycling_in_even_week: true
```

## How to get the source arguments

1. Visit the [refuse collection schedules](https://www.durban.gov.za/page/refuse-collection-schedules) page.
2. Download the DOCX for your region (e.g. **Outer West - Collection Schedule**).
3. Find your suburb or area in the table under the weekday column where it is listed.
4. Use the matching `region` slug for your DOCX file and the `area` slug for your suburb.

### Region slugs

| Region DOCX | `region` value |
|---|---|
| Outer West | `outer_west` |
| North Region | `north` |
| North Central | `north_central` |
| South Region | `south` |
| South Central | `south_central` |
| Inner West | `inner_west` |

### Area slugs

Area slugs are lowercase with underscores instead of spaces, for example:

- `Hillcrest` → `hillcrest`
- `Drummond & Montesseel` → `drummond_montesseel`
- `Umdloti` → `umdloti`

If the same suburb name appears on multiple weekdays in your region's schedule, a weekday suffix is added (e.g. `montclair_w3` for Montclair on Thursday). Use the slug that matches your collection day.

## Collection types

- **General Waste** — collected weekly on your mapped weekday (including public holidays).
- **Recycling** (orange bags) — collected fortnightly on the same weekday; not collected on South African public holidays.
