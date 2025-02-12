# System Table Documentation

## 3.2 System Table Overview
The system table (`sys`) is a Lua table that contains all functions and values exported by the application firmware.

## 3.2.1 Bitmask Operations

### 3.2.1.1 Bitmask Handle Methods

#### clear()
- Description: Clears the specified bit. Shortcut to `<handle>:setval(bitnum, false)`
- Syntax: `<handle>:clear(bitnum)`
- Parameters: `bitnum` - The bit number (throws error if exceeds array size)
- Returns: None

#### clearall()
- Description: Clears all bits in the array
- Syntax: `<handle>:clearall()`
- Parameters: None
- Returns: None

#### get()
- Description: Get the specified bit value
- Syntax: `<handle>:get(bitnum)`
- Parameters: `bitnum` - The bit number (throws error if exceeds array size)
- Returns: boolean - Whether bit is set (true) or cleared (false)

#### getall()
- Description: Retrieves entire bitmask as string. Bit 7 of first byte is first bit, bit 6 is second, etc.
- Syntax: `<handle>:getall()`
- Parameters: None
- Returns: string - The entire bitmask

#### invert()
- Description: Invert the specified bit
- Syntax: `<handle>:invert(bitnum)`
- Parameters: `bitnum` - The bit number (throws error if exceeds array size)
- Returns: None

#### invertall()
- Description: Invert all bits in the array
- Syntax: `<handle>:invertall()`
- Parameters: None
- Returns: None

#### set()
- Description: Set the specified bit. Shortcut to `<handle>:setval(bitnum, true)`
- Syntax: `<handle>:set(bitnum)`
- Parameters: `bitnum` - The bit number (throws error if exceeds array size)
- Returns: None

#### setall()
- Description: Sets all bits in the array
- Syntax: `<handle>:setall()`
- Parameters: None
- Returns: None

#### setval()
- Description: Set the specified bit to the given value
- Syntax: `<handle>:setval(bitnum, val)`
- Parameters:
  * `bitnum` - The bit number (throws error if exceeds array size)
  * `val` - Value to set (0 clears, other numbers/true sets, false clears)
- Returns: None

### 3.2.1.2 Bitmask Creation
#### create()
- Description: Create a bitmask that holds an array of bit values (true/false)
- Syntax: `sys.bitmask.create(sizeOrContent)`
- Parameters: `sizeOrContent` - Either:
  * Number: indicates number of bits to store (initialized to false)
  * String: each byte represents 8 bits, MSB used first
- Returns: handle - A handle to access bitmask functions
- Examples:
  ```lua
  -- Create bitmask with space for 10 bits
  local bitmask = sys.bitmask.create(10)

  -- Create bitmask with 16 bits, bits 0 and 9 true, others false
  local bitmask = sys.bitmask.create(string.char(0x80, 0x40))
  ```

## 3.2.2 Buffer Operations

### 3.2.2.1 Buffer Handle Methods

#### addBits()
- Description: Adds given number of bits to the buffer
- Syntax: `<handle>:addBits(val, bits)`
- Parameters:
  * `val` - Integer containing bits to add (up to 32 bits)
  * `bits` - Number of bits to add (up to 32)
- Returns: boolean - true if enough space for bits, false otherwise
- Examples:
  ```lua
  -- Add 2 bits (binary 11) to buffer
  local buffer = sys.buffer.create(100)
  local result = buffer:addBits(3, 2)

  -- Add 32 bits (binary 11110000000000000000000000000000)
  local buffer = sys.buffer.create(100)
  local result = buffer:addBits(0xF0000000, 32)
  ```

#### addFloat()
- Description: Adds a single-precision floating point value to the byte stream in IEEE 754 format
- Syntax: `<handle>:addFloat(value, lowWordFirst, littleEndian)`
- Parameters:
  * `value` - The floating point value to add to the byte stream
  * `lowWordFirst` - Whether to add the low word first (optional, default is false)
  * `littleEndian` - Whether to add in little-endian or big-endian format (optional, default is false)
- Returns: boolean - true if enough space for data, false otherwise
- Note: Implements IEEE 754 floating-point standard for data conversion

#### addInt16()
- Description: Adds a 16-bit integer value to the byte stream
- Syntax: `<handle>:addInt16(value, isSigned, littleEndian)`
- Parameters:
  * `value` - The 16-bit value (-32768 to 32767 for signed, 0 to 65535 for unsigned)
  * `isSigned` - Whether the value is signed or not
  * `littleEndian` - Whether to add in little-endian or big-endian format (optional, default is false)
- Returns: boolean - true if enough space for data, false otherwise
