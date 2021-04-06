# Electrak HD CAN
CAN bus interfacing with the Thomson Linear Electrak HD smart actuator.

## Usage Example

Note, this code is strictly for experimental purposes and has not been extensively tested.

Command actuator to move to 100 mm at 50% speed:

```shell
$ . electrak_can.sh
$ move 100 50
```

## Electrak HD CAN Bus Interfacing

This section describes the interface with the Electrak HD and provides sources.

Here is a list of the sources used:

- [Actuator Manual](https://www.thomsonlinear.com/downloads/actuators/Electrak_HD_Installation_Operation_mnen.pdf)
- [A Comprehensible Guide to J1939](https://copperhilltech.com/a-comprehensible-guide-to-j1939/)
  - "the book"
- [Linux Kernel J1939 Documentation, Socketcan](https://www.kernel.org/doc/html/latest/networking/j1939.html)

### Decoding Actuator Feedback Message

- Page 22 of the actuator manual specifies the use of the Proprietary A2 PGN, and on page 24 defines its use for feedback messages.

  - The book provides a comprehensive specification of this PGN on page 67.
  - It is a peer-to-peer message, or PDU1 format

- **Decoding the 29-bit ID**

  - | **Field**              | Priority | PGN     | R    | DP   | PDU Format | PDU Specific | Source Addr. |
    | ---------------------- | -------- | ------- | ---- | ---- | ---------- | ------------ | ------------ |
    | **Right Shift Amount** | 26       | 8       | 25   | 24   | 16         | 8            |              |
    | **Mask**               |          | 0x3FF00 | 1    | 1    | 0xFF       | 0xFF         | 0xFF         |
    | **Value**              | 6        | 126720  | 0    | 1    | 239        | 255          | 19           |

- **Decoding the Data Bytes**

  - The bits we are extracting each of the below values from may be 1 or two bytes, depending on data item length, specified at page 24 of the manual.

  - Each byte must be reversed before usage.

  - Each value's bit-order is reversed before it is scaled and used.

  - | Field                | Pos    | Current | Speed | Volt. Err. | Temp. Err. | Motion | Ovrld | Backdrv | Param | Sat. | Fatal |
    | -------------------- | ------ | ------- | ----- | ---------- | ---------- | ------ | ----- | ------- | ----- | ---- | ----- |
    | **Right Shift Amnt** | 2      | 1       | 4     | 2          | 0          | 7      | 6     | 5       | 4     | 3    | 2     |
    | **Mask**             | 0x3FFF | 0x1FF   | 0x1F  | 0x3        | 0x3        | 1      | 1     | 1       | 1     | 1    | 1     |

    

### Encoding Actuator Control Message

- Page 22 of the manual specifies the use of the Proprietary A PGN, and on page 23 defines its use for control messages.

  - See page 66 of the book

- **Encoding 29-bit ID**

  - We will need to reverse all the values to be least significant first

  - | **Field** | Priority | PGN   | R    | DP   | PDU Format | PDU Specific | Source Addr. |
    | --------- | -------- | ----- | ---- | ---- | ---------- | ------------ | ------------ |
    | **Value** | 6        | 61184 | 0    | 0    | 239        | 19           | Anything?    |

  - The PDU specific is the destination address in peer-to-peer communication.

    - Same as the source address from the AFM
