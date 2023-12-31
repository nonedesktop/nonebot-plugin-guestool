# GuesTool Protocol for Information Transportation

This document includes informations for transporting information between host-side management service and GuesTool.

## Basic communication protocol

GuesTool currently only uses WebSocket for communication.

### Generic message data

```json
{
    "opid": "{uuid4}",
    "opnm": "{operation_name}",
    "opct": {(any data that belongs to the operation)}
}
```

Every message has its unique ID for identifying.

All of the message data should be in this JSON format and should be send as text (string) instead of bytes.

All messages should be expired 1 minute after the messages are sent. For all expired messages, no responses with the expired `opid`s should be received, and rejection messages should be sent back when received.

## Operation list

### Greet

- name: `/greet/{greet_type}`
- desc: The first/last data pack to be sent when connecting/disconnecting.
- content: `{}`

#### Greet types

- `hello`
  - desc: The first data pack to be sent when connected.
- `bye`
  - desc: The first data pack to be sent before disconnecting.

### Info

- name: `/info/{info_name}`
- desc: Get specific informations.
- content:

  ```json
  {
      (some extra parameters...)
  }
  ```

#### Info names

- `python_version`
  - desc: get Python version of the guest
- `cpu`
  - desc: get CPU usage info of the guest
  - params:
    - `smptime (float, default=0.1)`: sample time for CPU usage
- `memory`
  - desc: get memory info of the guest
- `all_partitions`
  - desc: get all partitions on the guest
  - params:
    - `physical_only (bool, default=True)`: whether to report physical devices only
- `all_disk_io`
  - desc: get all disk IO on the guest
  - params:
    - `smptime (float, default=1.0)`: sample time for disk IO
- `all_network_io`
  - desc: get all network IO on the guest
  - params:
    - `smptime (float, default=1.0)`: sample time for network IO
- `processes`
  - desc: get all processes on the guest
  - params:
    - `smptime (float, default=1.0)`: sample time for processes
- `system_platform`
  - desc: get platform name of the guest
- `time`
  - desc: get start time of the guest
- `bots`
  - desc: get all names of connected bots
- `bots_connect_time`
  - desc: get connection time of connected bots
- `recv_events`
  - desc: get received events of connected bots
- `apicall`
  - desc: get apicalls of connected bots

### Event

#### Report

- name: `/event/report/{report_type}`
- desc: Report data from info/action requests.
- content:

  ```json
  {
      (data returned from requests...)
  }
  ```

##### Report types

- `info`: for info report.
- `action`: for action report.

### Action

#### Manage matcher

- name: `/action/matcher/{operation}`
- desc: List, add, hack or remove matchers.
- content:

  ```json
  {
      (some extra parameters...)
  }
  ```

##### Operations

- `list`
  - desc: list all found matcher IDs
<!--
- `add`
  - desc: add a new matcher
  - params:
    - `type ("", "metaevent", "message", "notice", "request")`: type of events
    - `rule (RuleDict)`: rule information for new matcher
    - `priority (int)`: matcher response priority
    - `block (bool)`: whether to block event propagation
-->
- `info`
  - desc: get matcher info by ID
  - params:
    - `id (str)`: matcher index UUID
- `hack`
  - desc: hack an existing matcher
  - params:
    - `id (str)`: matcher index UUID
    - `type ("", "metaevent", "message", "notice", "request")`: type of events
    - `rule (RuleDict)`: rule information for matcher
    - `priority (int)`: matcher response priority
    - `block (bool)`: whether to block event propagation
    - `temp (bool)`: whether to be removed after running
    - `expire_time (float | none)`: when to be removed
- `remove`
  - desc: remove a matcher
  - params:
    - `id (str)`: matcher index UUID
