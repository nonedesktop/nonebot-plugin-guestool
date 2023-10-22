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

### Hello

- name: `/hello`
- desc: The first data pack to be sent when connected.
- content: Nothing.
