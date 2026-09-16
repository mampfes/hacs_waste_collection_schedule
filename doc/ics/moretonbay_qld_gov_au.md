# Moreton Bay

Moreton Bay is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.moretonbay.qld.gov.au/Services/Waste-Recycling/Collections/Bin-Days> and select your location.
- Click on `Subscribe to a personalised calendar` to get a webcal link.
- Use this link as the `url` parameter.

The link is one of ten per-run calendars on the council's CDN, named
`waste-calendar-<day>-week<N>.ics`, where `<day>` is your collection weekday
(`monday`-`friday`) and `<N>` is your recycling fortnight (`1` or `2`). Both
are property-specific, so use the link generated for your own address rather
than copying the example below.

Older `webcal://www.moretonbay.qld.gov.au/bincal?externalId=...` links are no
longer issued by the council, and that host rejects the integration's HTTP
client with `HTTP Error 403`. Replace any such link with the one the Bin Days
page gives you now.

## Examples

### 18 Mainsail Drive, CABOOLTURE SOUTH Queensland 4510

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://cdn.services-v2.moretonbay.qld.gov.au/bin-days/icals/waste-calendar-thursday-week1.ics
```
