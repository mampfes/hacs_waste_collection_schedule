# Static Source

Support for schedules with static dates or recurrences.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: static
      args:
        type: TYPE
        dates: DATES
        frequency: FREQUENCY
        interval: INTERVAL
        start: START
        until: UNTIL
        excludes: EXCLUDES
```

### Configuration Variables

**TYPE**  
*(string) (required)*

The type of this source.

**DATES**  
*(list) (optional)*

A list of dates in format "YYYY-MM-DD" which should be added to the source.
Dates defined in this list will be added in addition to calculated dates from the recurrence and will not be affected by the exclude-list.

**FREQUENCY**  
*(string) (optional)*

Defines the frequency of the recurrence. Must be one of "DAILY", "WEEKLY", "MONTHLY" or "YEARLY".

**INTERVAL**  
*(int) (optional, default: ```1```)*

Defines the interval of the recurrence.

**START**  
*(string) (optional)*

Defines the start of the recurrence in the format "YYYY-MM-DD".
Required if *FREQUENCY* is set.

**UNTIL**  
*(string) (optional)*

Defines the end of the recurrence in the format "YYYY-MM-DD".
Required if *FREQUENCY* is set.

**EXCLUDES**  
*(list) (optional)*

A list of dates in format "YYYY-MM-DD" which should be excluded from the recurrence.

## Example

This example defines a schedule, every 4 weeks starting on Friday, January 14, 2022 until the end of the year.
Two days are removed from the schedule and two days are added instead, which are outside of the recurrence.

```yaml
waste_collection_schedule:
  sources:
    - name: static
      calendar_title: Altpapier
      args:
        type: Altpapier
        frequency: WEEKLY
        interval: 4
        start: '2022-01-14'
        until: '2022-12-31'
        excludes: # Add exception for the recurrence
          - '2022-07-29'
          - '2022-09-23'
        dates: # Manually define dates that are not part of the recurrence
          - '2022-07-28'
          - '2022-09-22'
```
