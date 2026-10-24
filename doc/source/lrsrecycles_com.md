# Lakeshore Recycling Systems (LRS)

Support for schedules provided by [Lakeshore Recycling Systems (LRS)](https://www.lrsrecycles.com).

Source for Lakeshore Recycling Systems (Illinois) municipal waste and recycling calendars.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lrsrecycles_com
      args:
        calendar_url: CALENDAR_URL
        service_day: SERVICE_DAY
        recycling_service: RECYCLING_SERVICE
```

### Configuration Variables

**calendar_url**  
*(string) (required)*

**service_day**  
*(string) (required)*

**recycling_service**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lrsrecycles_com
      args:
        calendar_url: https://www.lrsrecycles.com/municipality/_shared/pdfs/d6b92e8267e711a9766eead69edb0a66.pdf
        service_day: Monday
        recycling_service: A
```

## How to get the source arguments

Copy the link of your municipality's 'Waste & Recycling Service' calendar PDF from LRS (lrsrecycles.com or your village's website) into `calendar_url`; LRS publishes a new link every year. The map on the calendar shows your service day and whether your recycling service is A or B.
