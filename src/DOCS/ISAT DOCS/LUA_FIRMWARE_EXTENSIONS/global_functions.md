# Lua Firmware Extensions and Global Functions

## 3.1 Global Functions

### 3.1.1 Base64 Library

The base64 library is a firmware extension that provides base64 encoding/decoding functionality for strings.

#### 3.1.1.1 decode()

**Description**
Decodes a base64 encoded string and returns the decoded results.

**Syntax**
```lua
base64.decode(str)
```

**Parameters**
- `str`: Lua string containing base64 encoded data

**Returns**
- `string`: Decoded string

**Example**
```lua
-- Encodes "This is a test message" and then decodes and prints it
print(base64.decode(base64.encode("This is a test message.")))
-- Output: This is a test message.
```

**See Also**
- base64.encode()

#### 3.1.1.2 encode()

**Description**
Returns the base64 encoding of a specified string.

**Syntax**
```lua
base64.encode(str)
```

**Parameters**
- `str`: Lua string to encode

**Returns**
- `string`: Base64 encoded string

**Example**
```lua
print(base64.encode("Hello world"))
-- Output: SGVsbG8gd29ybGQ=
```

**See Also**
- base64.decode()

### 3.1.2 bit32 Library

The bit32 library provides functions for bitwise manipulation of integers. It is based on the Lua 5.2 alpha version of the library and is included for backwards compatibility. Note that Lua 5.3 has built-in bitwise operators.

#### 3.1.2.1 arshift()

**Description**
Returns the number value shifted `disp` bits to the right. For negative displacements, shifts to the left. This is an arithmetic shift operation where:
- Vacant bits on the left are filled with copies of the higher bit of value
- Vacant bits on the right are filled with zeros
- Displacements with absolute values higher than 31 result in zero or 0XFFFFFFFF

**Syntax**
```lua
bit32.arshift(value, disp)
```

**Parameters**
- `value`: Number to shift
- `disp`: Displacement to shift (negative values shift left)

**Returns**
- `integer`: Shifted result

#### 3.1.2.2 band()

**Description**
Returns the bitwise AND of all operands.

**Syntax**
```lua
bit32.band(...)
```

**Parameters**
- `...`: Numbers to AND together

**Returns**
- `integer`: AND of all operands

#### 3.1.2.3 bnot()

**Description**
Returns the bitwise negation of value.

**Syntax**
```lua
bit32.bnot(value)
```

**Parameters**
- `value`: Number to negate

**Returns**
- `integer`: Bitwise negation of value

#### 3.1.2.4 bor()

**Description**
Returns the bitwise OR of all operands.

**Syntax**
```lua
bit32.bor(...)
```

**Parameters**
- `...`: Numbers to OR together

**Returns**
- `integer`: OR of all operands

#### 3.1.2.5 btest()

**Description**
Returns true if the bitwise AND of all operands is different from zero.

**Syntax**
```lua
bit32.btest(...)
```

**Parameters**
- `...`: Numbers to test

**Returns**
- `boolean`: true if bitwise AND of all operands is different from zero

#### 3.1.2.6 bxor()

**Description**
Returns the bitwise exclusive OR of all operands.

**Syntax**
```lua
bit32.bxor(...)
```

**Parameters**
- `...`: Numbers to exclusive OR together

**Returns**
- `integer`: Exclusive OR of all operands

#### 3.1.2.7 lrotate()

**Description**
Returns the number value rotated disp bits to the left.

**Syntax**
```lua
bit32.lrotate(value, disp)
```

**Parameters**
- `value`: Number to rotate
- `disp`: Displacement to rotate (negative values rotate right)

**Returns**
- `integer`: Rotated result

#### 3.1.2.8 lshift()

**Description**
Returns the number value shifted disp bits to the left. Negative displacements shift to the right. In any direction, vacant bits are filled with zeros. Displacements with absolute values greater than 31 result in zero (all bits are shifted out).

**Syntax**
```lua
bit32.lshift(value, disp)
```

**Parameters**
- `value`: Number to shift
- `disp`: Displacement to shift (negative values shift right)

**Returns**
- `integer`: Shifted result

#### 3.1.2.9 rrotate()

**Description**
Returns the number value rotated disp bits to the right.

**Syntax**
```lua
bit32.rrotate(value, disp)
```

**Parameters**
- `value`: Number to rotate
- `disp`: Displacement to rotate (negative values rotate left)

**Returns**
- `integer`: Rotated result

#### 3.1.2.10 rshift()

**Description**
Returns the number value shifted disp bits to the right. Negative displacements shift to the left. In any direction, vacant bits are filled with zeros. Displacements with absolute values greater than 31 result in zero (all bits are shifted out).

**Syntax**
```lua
bit32.rshift(value, disp)
```

**Parameters**
- `value`: Number to shift
- `disp`: Displacement to shift (negative values shift left)

**Returns**
- `integer`: Shifted result

### 3.1.3 Debugging

#### 3.1.3.1 trace()

**Description**
This command accepts arguments exactly like print(), except that instead of sending the output to the main RS-232 port, the output is sent to the firmware serial tracing facility.

**Syntax**
```lua
trace(...)
```

**Parameters**
- `...`: Zero or more Lua objects to print. If no arguments are specified, just a carriage return/line feed pair is output.

**Returns**
None

**Example**
```lua
-- Sends the output to the serial tracing channel, if it is configured
trace("Current thread is: ", sched.getThread())
```

**See Also**
- print()

#### 3.1.3.2 tracef()

**Description**
This command accepts arguments exactly like printf(), except that instead of sending the output to the main RS-232 port, the output is sent to the firmware serial tracking facility.

**Syntax**
```lua
tracef(format, ...)
```

**Parameters**
- `format`: String optionally containing format specifiers
- `...`: Zero or more arguments matching the format specifiers contained in the format argument

**Returns**
None

### 3.1.4 Pickle Library

The pickle library is used to serialize and deserialize Lua data structures.

#### 3.1.4.1 dump()

**Description**
Serializes a Lua data structure to a string, which is also written out to the given file.

**Syntax**
```lua
pickle.dump(object, filename)
```

**Parameters**
- `object`: The Lua object to serialize
- `filename`: The name of the file to write the serialized object to

**Returns**
- `string`: The serialized object

#### 3.1.4.2 dumps()

**Description**
Serializes a Lua data structure to a string. The string is Lua code, which can actually be loaded with loadstring(), and then subsequently run to produce the original object.

**Syntax**
```lua
pickle.dumps(object)
```

**Parameters**
- `object`: The Lua object to serialize

**Returns**
- `string`: The serialized object

#### 3.1.4.3 load()

**Description**
Deserializes a Lua data structure from a file.

**Syntax**
```lua
pickle.load(filename)
```

**Parameters**
- `filename`: The name of the file where the serialized Lua object is saved

**Returns**
- `object`: The original Lua object, or nil if the content of the file does not represent a valid Lua object

#### 3.1.4.4 loads()

**Description**
Deserializes a Lua data structure from a string.

**Syntax**
```lua
pickle.loads(serialized)
```

**Parameters**
- `serialized`: The string representing the serialized Lua object

**Returns**
- `object`: The original Lua object, or nil if the content of the file does not represent a valid Lua object

### 3.1.5 Serial Output

#### 3.1.5.1 print()

**Description**
Receives any number of arguments and prints their values to the main serial port, if the shell is enabled. The Lua tostring() function is used on each argument to convert the arguments to strings before printing them, followed by a carriage return/line feed pair. This function is similar to the standard Lua print() function except that tab characters are NOT output between each item.

**Syntax**
```lua
print(...)
```

**Parameters**
- `...`: Zero or more Lua objects to print. If no arguments are specified, just a carriage return/line feed pair is output.

**Returns**
None

**Example**
```lua
print("Current thread is: ", sched.getThread())
-- Output: Current thread is: thread: 64050130 [lua nores chunk]
```

**See Also**
- printf()

#### 3.1.5.2 printf()

**Description**
Writes a sequence of data formatted as the format string argument specifies to the main serial port. After the format string argument, the function expects at least as many additional arguments as specified in the format string. Unlike print(), a trailing new-line is NOT output. The format uses the same specifiers as the standard Lua string.format().

**Syntax**
```lua
printf(format, ...)
```

**Parameters**
- `format`: String optionally containing format specifiers
- `...`: Zero or more arguments matching the format specifiers contained in the format argument

**Returns**
None

**Example**
```lua
printf("%10s - 0x%X\n", "abc", 123)
-- Output: abc - 0x7B
```

**See Also**
- print()
