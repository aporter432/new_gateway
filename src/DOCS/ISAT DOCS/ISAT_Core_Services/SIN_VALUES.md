# Service Identification Numbers (SIN)

## SIN Range Definitions

SIN (dec) | Description
----------|-------------
16 – 63   | Core services
64 – 127  | Terminal Apps
128 – 255 | User services

## Core Services

SIN | Service Name | Description
----|--------------|-------------
16  | System | Provides general management and control of the terminal, such as service identification, metrics, and status query/response.
17  | Power | Provides a unified interface to terminal power management at the Lua level.
18  | Message | This service is responsible for building and delivering both to- and from-mobile messages to the appropriate service.
19  | Report | Basic event or status reports either prescheduled or on demand (polled).
20  | Position | This service provides access to positioning information, either from the internal GPS or external high precision GPS.
21  | Geofence | The geofence service provides the ability to define geographical regions based on circles or polygons, as well as reporting entry and exit from these regions.
22  | Serial | Manages communication through the terminal's various serial ports (that is RS-232 and RS-485), including their configuration and status.
23  | Log | Stores data in nonvolatile storage. The data can be application data that can be retrieved at later date, or diagnostic information for troubleshooting. This service also provides auto upload capabilities.
24  | File System | Provides an interface for the file system that is in the application firmware.
25  | External Input/Output | Configures and reports the status of the terminal's general purpose I/O. In addition, it is used to monitor the internal temperature. Alarms can be configured if thresholds are exceeded.
26  | Shell | Provides access to a command-line interface (CLI) over the serial port. It also provides the ability to execute the same commands over-the-air and allows you to change the access level of the shell.
27  | IDP | Provides access to some of the functionality offered by the IDP modem.
28  | Reserved | -
29  | Cell | Provides support for JSON encoding of messages, allows configuration and monitoring of the module; and also provides a plugin to the message service allowing it to send/receive messages over cellular (satellite-cellular terminals).
30  | Reserved | -
31  | Reserved | -
32  | Campaign | A mandatory service that must be running to support software over-the-air updates.
33  | Internet Protocol (ip) | Allows terminals to take advantage of protocols and their associated features for the development of IP enabled Lua applications.
34  | Accelerometer | Defines the global configuration of the accelerometer.

## Implementation Notes
1. Core Services (16-63):
   - Fundamental terminal functionality
   - Many services mandatory
   - Base system capabilities
   - Dependencies:
     * SIN 16 (System) required for service identification
     * SIN 18 (Message) required for all message handling
     * SIN 32 (Campaign) mandatory for updates
     * SIN 33 (IP) mandatory for cellular services

2. Terminal Apps (64-127):
   - Reserved for terminal applications
   - Implementation specific
   - Integration Requirements:
     * Must respect core service boundaries
     * Cannot override core service functionality
     * Must handle core service updates

3. User Services (128-255):
   - Available for custom implementations
   - User-defined functionality
   - Development Guidelines:
     * Use Message service (SIN 18) for all message handling
     * Implement proper error handling
     * Consider cellular vs satellite capabilities
     * Handle service updates appropriately

4. Service Dependencies:
   - IP Service (SIN 33) requires:
     * Cell Service (SIN 29) for cellular operations
     * Message Service (SIN 18) for message handling
     * System Service (SIN 16) for terminal management
   - Cellular Operations require:
     * Campaign Service (SIN 32) for updates
     * Cell Service (SIN 29) enabled
     * IP Service (SIN 33) configured

5. Development Considerations:
   - Service Initialization:
     * Check required services are available
     * Verify service versions
     * Handle missing dependencies gracefully
   - Message Handling:
     * Use appropriate service for message type
     * Consider size limitations
     * Implement proper routing
   - Error Management:
     * Monitor service status
     * Handle service failures
     * Implement recovery procedures

6. Best Practices:
   - Service Implementation:
     * Document service dependencies
     * Maintain service boundaries
     * Handle version compatibility
   - Resource Management:
     * Monitor service resource usage
     * Implement proper cleanup
     * Handle resource constraints
   - Testing Requirements:
     * Verify service interactions
     * Test failure scenarios
     * Validate update procedures

## Common Implementation Patterns

### 1. Service Initialization
```lua
-- Check if required services are available
local function checkRequiredServices()
    local required = {
        system = 16,    -- System service
        message = 18,   -- Message service
        cell = 29,      -- Cell service for cellular ops
        ip = 33        -- IP service
    }

    for name, sin in pairs(required) do
        if not services.isRegistered(sin) then
            error(string.format("Required service %s (SIN %d) not available", name, sin))
        end
    end
end

-- Initialize service with proper error handling
local function initializeService()
    local success, err = pcall(function()
        checkRequiredServices()
        -- Additional initialization code
    end)

    if not success then
        log.error("Service initialization failed: " .. tostring(err))
        return false
    end
    return true
end
```

### 2. Message Handling
```lua
-- Message service wrapper
local MessageHandler = {
    -- Message types
    TYPE_FROM_MOBILE = 1,
    TYPE_TO_MOBILE = 2
}

function MessageHandler:send(data, msgType)
    -- Check message size
    if #data > self:getMaxSize(msgType) then
        return nil, "Message exceeds size limit"
    end

    -- Prepare message
    local msg = {
        type = msgType,
        payload = data,
        timestamp = os.time()
    }

    -- Send via appropriate service
    return services.message.send(msg)
end

function MessageHandler:getMaxSize(msgType)
    if msgType == self.TYPE_FROM_MOBILE then
        return 6400  -- 6.4KB limit for from-mobile
    else
        return 10240 -- 10KB limit for to-mobile
    end
end
```

### 3. Resource Management
```lua
-- Channel management pattern
local function allocateChannel(channelType, params)
    local handle = svc.ip.channelAllocate(channelType, params)
    if not handle then
        return nil, "Channel allocation failed"
    end

    -- Ensure proper cleanup
    local cleanup = function()
        if handle then
            handle:dispose()
            handle = nil
        end
    end

    return handle, cleanup
end

-- Usage example
local function sendData(data)
    local handle, cleanup = allocateChannel(svc.ip.Channel.TCP, {
        address = "example.com",
        port = 8080
    })

    if not handle then
        return false, "Failed to allocate channel"
    end

    -- Ensure cleanup happens
    local success, err = pcall(function()
        handle:send(data)
    end)

    cleanup()  -- Always clean up
    return success, err
end
```

### 4. Error Recovery
```lua
-- Retry pattern with backoff
local function withRetry(operation, maxAttempts, initialDelay)
    local attempts = 0
    local delay = initialDelay or 1

    while attempts < maxAttempts do
        local success, result = pcall(operation)

        if success then
            return true, result
        end

        attempts = attempts + 1
        if attempts < maxAttempts then
            -- Exponential backoff
            os.sleep(delay)
            delay = delay * 2
        end
    end

    return false, "Operation failed after " .. attempts .. " attempts"
end

-- Usage example
local success, result = withRetry(function()
    return services.message.send(data)
end, 3, 2)  -- 3 attempts, starting with 2-second delay
```

### 5. Service Status Monitoring
```lua
-- Service health check
local function checkServiceHealth(sin)
    local status = {
        registered = services.isRegistered(sin),
        timestamp = os.time()
    }

    if status.registered then
        -- Additional health checks based on service type
        if sin == 29 then  -- Cell service
            status.cellular = svc.cell.getStatus()
        elseif sin == 33 then  -- IP service
            status.network = svc.ip.getStatus()
        end
    end

    return status
end

-- Periodic monitoring
local function startMonitoring(interval)
    local timer = services.timer.new(interval, function()
        local health = checkServiceHealth(33)  -- Monitor IP service
        if not health.registered or not health.network.connected then
            log.error("Service health check failed")
            -- Implement recovery logic
        end
    end)
    return timer
end
```

These patterns demonstrate best practices for:
- Service initialization and dependency checking
- Message size validation and handling
- Resource allocation and cleanup
- Error recovery with retry logic
- Service health monitoring

Note: Adjust timeouts, retry counts, and other parameters based on your specific requirements.
