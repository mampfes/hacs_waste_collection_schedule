# Publish a collection schedule for your municipality

Municipalities and waste providers can make their collection dates available to
Home Assistant without developing a custom integration. Publish an **iCalendar
(`.ics`) feed** and residents can use the [generic ICS source](source/ics.md).

## 1. Create a public collection calendar

Use a calendar tool that exports a public iCalendar subscription, such as
Nextcloud Calendar or a calendar plugin for your existing website. Create a
separate calendar for waste collections and enable its public subscription link.
Residents need the feed URL, not the HTML page used to view the calendar.

For a small schedule, you can also publish a plain UTF-8 text file named
`collections.ics` on your existing website. The following is a complete example
with two **fictional** collection dates. Replace them with your actual dates:

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Municipality//Waste Collections//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
UID:paper-20270104-zone-a@example.org
DTSTAMP:20261013T120000Z
DTSTART;VALUE=DATE:20270104
DTEND;VALUE=DATE:20270105
SUMMARY:Paper
END:VEVENT
BEGIN:VEVENT
UID:general-waste-20270106-zone-a@example.org
DTSTAMP:20261013T120000Z
DTSTART;VALUE=DATE:20270106
DTEND;VALUE=DATE:20270107
SUMMARY:General waste
END:VEVENT
END:VCALENDAR
```

- Each collection is a `VEVENT`. Its `SUMMARY` names the waste type; use consistent
  names across dates. Local-language names are fine.
- For an all-day collection, use `DTSTART;VALUE=DATE:YYYYMMDD`. The `DTEND` date is
  exclusive, so a one-day event ends on the following date.
- Give each event a unique `UID` and retain it when correcting that event. Set
  `DTSTAMP` to the creation or update time in UTC.
- Use the actual collection dates, including holiday changes. A recurring rule
  without exceptions can show the wrong dates around holidays.
- For different collection zones, offer a feed per zone and label it clearly on
  your website. A combined feed must not make residents guess which dates apply
  to them. Do not include residents' personal details in a public calendar.

Calendar software normally handles the iCalendar formatting for you, including
line endings and escaping. When writing a file yourself, follow
[RFC 5545](https://www.rfc-editor.org/rfc/rfc5545), including CRLF line endings.

## 2. Publish a stable subscription URL

For example: `https://example.org/waste/zone-a.ics`.

The URL should return the calendar directly over HTTPS, without requiring an
account, cookies or an interactive login. Serve static files as
`text/calendar; charset=utf-8`. Open the URL in a private browser window to check
that it really downloads a calendar rather than a login page.

Keep this URL unchanged when publishing next year's schedule. Update the calendar
at the same location, include upcoming dates, and publish corrections promptly.
Residents then keep receiving updates without configuring a new link each year.

## 3. Let residents subscribe in Home Assistant

In Waste Collection Schedule, choose **Generic → ICS** and enter the public URL
in the source configuration. A YAML configuration can use the same feed:

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: "https://example.org/waste/zone-a.ics"
```

Before announcing the feed, check the resulting calendar against your official
schedule: collection dates, waste types, zone and holiday changes should match.
The [ICS source documentation](source/ics.md) explains further configuration
options. A static file and a calendar subscription both work; residents should
configure the URL so that changes are fetched automatically.

## 4. Add your municipality to the provider list

Once the feed works, you or a contributor can submit a small YAML provider
definition following [the ICS contribution guide](contributing_ics.md). Include
a working example zone and its feed URL. No new Python source module is needed.

If publishing a feed is not possible yet, residents can use the
[static source](source/static.md) for a manually maintained schedule. That is a
local workaround: corrections will not reach them automatically.
