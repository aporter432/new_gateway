# Terminal Software Architecture

## Service-Based Architecture

The terminal software is built on a service-oriented architecture where most end-user functionality is implemented through software constructs called services. These services are:
- Self-contained
- Individually addressable modules
- Offer well-defined functionality

### Service Categories

1. **Core Services**
   - Basic building blocks of terminal functionality
   - Network-visible components
   - Provide fundamental capabilities:
     - I/O accessibility
     - External message handling
     - Position reporting
     - Status and configuration queries

2. **Terminal Apps**
   - Configurable device-level applications
   - Implemented by ORBCOMM
   - Feature specific functionality sets
   - Contact ORBCOMM for available apps

3. **User Services**
   - Provide advanced or complex functions
   - Custom implementations possible

## Software Stack

The software architecture consists of three fundamental layers integrated within a Lua framework:

1. **Hardware Layer**
   - Device hardware components
   - Abstracted through service-callable API
   - Hardware resource management

2. **Application Layer**
   - Service implementations in Lua
   - Custom application support
   - Service registration and management

3. **Network Layer**
   - Message formatting and routing
   - Channel-specific handling
   - Terminal-specific plug-in support

## Lua Framework

The system utilizes Lua as the primary scripting language due to its:
- Proven reliability in embedded systems
- Small footprint
- Fast execution
- Easy integration with other languages
- Robust API support

### Integration Model

- Hardware is separated from applications via service-callable API
- Services access hardware/other services through this API
- Complex functions possible through user-programmable Lua applications
- Services are registered and identified through network interface

## Message Flow

### Network Interface Responsibilities
- Accepts messages from services
- Formats messages for specific network channels
- Handles message transmission
- Processes incoming messages:
  - Removes channel-specific formatting
  - Routes to appropriate service

## System Initialization

1. **Power On/Reset Sequence**
   - Basic hardware tests execution
   - Core services initialization
   - Configuration loading

2. **Network Registration**
   - Lua framework service registration
   - Network synchronization
   - Transport queue management

## Example Implementation

Consider a basic application for digital input monitoring:
1. Terminal configured for digital input 1 state change detection
2. EIO service configuration (local/remote) defines:
   - Port 1 as digital input
   - Alarm trigger on low-to-high transition
3. Message handling:
   - Alarm routed to transport layer
   - Message formatting and transmission
   - Delivery status notification to service
