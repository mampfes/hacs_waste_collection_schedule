# City of Subiaco (WA)

Support for City of Subiaco (Western Australia) waste collection services. This source uses a calculation based on your Area and Weekday.

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: subiaco_wa_gov_au
      args:
        area: 1
        day_of_week: Monday
        
 ## Configuration Variables
 
 Variable         |  Type   |  Requirement  |  Description
 ---------------------------------------------------------------------
area                |  int       |  Required        |  Either 1 or 2 based on your location.
day_of_week  |  string  |  Required        |  "The day your bins are usually collected (e.g., Monday)."

## How to find your details
Check the City of Subiaco Waste Area Guide. https://www.subiaco.wa.gov.au/residents/in-your-home/bins,-recycling-and-waste/waste-area-guide
Area 1: North of Hamersley Road.
Area 2: South of Hamersley Road.
Your Day of Week is your standard scheduled collection day.
