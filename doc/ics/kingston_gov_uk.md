# London Borough of Kingston

London Borough of Kingston is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.

## How to get the configuration arguments

- Go to <https://waste-services.kingston.gov.uk/waste> and enter your post code, and on the following page select your address.
- In the _Download your collection schedule_ panel, click `Add to your calendar`.
- Click the `Copy` button in _Step 1: copy the link to the calendar_.
- Use the copied link as the `url` parameter.

## Examples

### Address with Garden Waste subscription

- Click Add Hub on your Home Assistant Waste Collection Schedule integration
- On Select Country select Generic
- On Select Source select ICS(ics)
- Configure Source 
-   - Add a Url (e.g. https://waste-services.kingston.gov.uk/waste/2644206/calendar.ics)
-   - Click Submit
- On Select Configuration Details (can both be left empty for default) 
- - Show Collection Event Customize Configurations (Select if you want to limit the collection types)
- - Show Sensor Configurations ()
- Click Submit
