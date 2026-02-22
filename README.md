# OPC DA ↔ OPC UA Bridge 

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Domain](https://img.shields.io/badge/Industrial-Automation-orange)
![Protocol](https://img.shields.io/badge/Protocols-OPC%20DA%20%7C%20OPC%20UA-blueviolet)
![License](https://img.shields.io/badge/License-GPLv3-blue)

> Industrial protocol bridge enabling interoperability between OPC DA systems and modern OPC UA infrastructure.

---

## Project Summary

This project implements a bidirectional communication bridge between:

- **OPC DA** (via OpenOPC / DCOM)
- **OPC UA** (via FreeOPCUA server)

It dynamically maps OPC DA tags into an OPC UA namespace while maintaining real-time synchronization in both directions.

### Use Cases

- Bridging OPC DA to OPC UA
- Exposing legacy systems utilising OPC DA to OPC UA clients
- Creating an integration layer during protocol migration
- Industrial automation lab environments

### Key Features

- Environment-driven configuration
- Dynamic tag discovery
- Data-type mapping (DA → UA)
- Timestamp preservation
- Write conflict prevention
- Logging-based monitoring
- Configuration-based deployment
---

## Industrial Architecture



### <p align="center"> OPC-DA Server  → OpenOPC Client  → FreeOPCUA Server  → OPC UA Clients</p>



An example of an OPC UA Client would be a SCADA system (Ignition, AVEVA, etc.)

---

## Configuration

All deployment-specific values are defined in:

```python
# config.py

CONFIG = {
    # OPC DA
    "da_server": "Kepware.KEPServerEX.V6",
    "group_name": "Channel2.Device1",

    # OPC UA
    "endpoint": "opc.tcp://0.0.0.0:4840/freeopcua/server/",
    "namespace_url": "https://example.com/opcua",
    "ua_object_name": "Micrologix 1400 Series B",
}
```
#### What You Can Customize:

- OPC DA server name
- Tag group name
- OPC UA endpoint
- Namespace URI
- Exposed device object name

---

## Current Limitations

While suitable for integration-layer and lab environments, this bridge has the following limitations:

- **No Automatic Reconnection Logic:** If the OPC DA server or OPC UA server connection is lost, the application must be restarted manually.
- **No High Availability / Redundancy:** This is a single-instance bridge and does not implement failover or clustering.
- **No Security Policy Configuration:** The OPC UA server currently runs without configurable security policies, certificates, or authentication.
- **Basic Error Handling:** Error handling is minimal and does not implement retry backoff strategies or detailed exception classification.
- **No Performance Optimization for Large Tag Sets:** Not stress-tested for thousands of tags or high-frequency updates. Designed for moderate tag counts.
- **Windows-Only (Due to OpenOPC / DCOM):** Because OPC DA relies on COM/DCOM, this bridge requires Windows.

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.

---

## Author

### Salma Alfaramawy

**LinkedIn:** https://www.linkedin.com/in/salma-alf/ 

**Contact:** salmakh.1627@gmail.com

---

