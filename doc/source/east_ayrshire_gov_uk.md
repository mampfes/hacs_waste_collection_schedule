# East Ayrshire Council

Support for schedules provided by [East Ayrshire Council](https://www.east-ayrshire.gov.uk/Housing/RubbishAndRecycling/Collection-days/ViewYourRecyclingCalendar.aspx).

**Deprecation notice**: East Ayrshire Council has retired the UPRN-based recycling calendar this source reads: the page now redirects to [Bin collection days](https://www.east-ayrshire.gov.uk/Housing/RubbishAndRecycling/Collection-days/bin-collection-days.aspx), which has no collection dates, so this source returns no collections. The council now publishes bin days via ReCollect (area `EastAyrshireUK`). This source is deprecated and will be removed in the next major release. Please switch to the shared [ReCollect source](recollect_net.md) (`recollect_net`):

```yaml
waste_collection_schedule:
  sources:
    - name: recollect_net
      args:
        place_id: YOUR_RECOLLECT_PLACE_ID
        service_id: waste
        locale: en-GB
```

To find your `place_id`, look up your address in the bin collection widget on the council page above, click "Get a calendar" and copy the ID that follows `/places/` in the calendar link (e.g. `https://recollect.a.ssl.fastly.net/api/places/<place_id>/services/50014/events.en-GB.ics`). `service_id` may be `waste` or the number in that link.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: east_ayrshire_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: east_ayrshire_gov_uk
      args:
        uprn: "127072649"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.