# CAN Bus Approach

## Tools

- socket can
  - included as a module in Linux kernel
- [J1939 Framework](https://github.com/famez/J1939-Framework)
- [Python API](https://github.com/benkfra/j1939)
- [Savvy CAN](https://www.savvycan.com/)

## Resources

- [Wilfred Voss](https://copperhilltech.com/blog/sae-j1939-programming-with-arduino-multipacket-peertopeer-rtscts-session/)
  - [Arduino code](https://copperhilltech.com/ard1939-sae-j1939-protocol-stack-for-arduino-teensy-esp32/)
  - Also see his book
- Simulating Actuator with CANable
  - [Getting Started with SocketCAN on Linux](https://canable.io/getting-started.html#socketcan-linux)
- CSS Electronics
- [Socket CAN Guide](https://blog.mbedded.ninja/programming/operating-systems/linux/how-to-use-socketcan-with-the-command-line-in-linux/)

# Hardware

- [CAN microcontroller](http://store.evtv.me/proddetail.php?prod=ArduinoDueCANBUS&cat=23)

## Bit Manipulation

### Packing

- The default priority for control messages is 3 while the default priority for other messages is 6
- Destination address in destination specific is the last 8 bits of the pgn
  - destination specific uses PDU1 format
  - Can take value 255 which is global address 
    - This value is also owned by PDU2 format (broadcast communication)
- For communicating with the Electrac HD, it seems like the destination address (last 8 bits of the PGN) must be either 13 or 255
  - 255 is global - every ECU must process? Or do they have some other method for determining if the message is relevant
  - 13 is the source address in the Actuator Feedback Messages (AFM's)
  - It uses the proprietary A2 message for AFM's

### Unpacking

- [Linux Kernel SocketCan J1939 Docs](https://www.kernel.org/doc/html/latest/networking/j1939.html)
  - Good docs on bit packing for J1939 PGN
- Based on Voss book, I think byte ordering starts with byte zero on the left and goes to byte 7 on the right. See attached screenshot (this is for multi-frame packets, but shows the byte order)

```code
class RecieveMsg:
   int PGN
   int position
   int current
   int speed
   int voltageError
   int tempError
   bool motion
   bool overload
   bool backdrive
   bool param
   bool saturation
   bool fatal
```

- I'm not sure what the byte order deal is. I am getting a PGN of 126975 which is not correct should be 126720. See attached screenshot - we are getting 1's as the last byte where it should be zeros.

  - The python api just throws away the last 2 bytes of the 18 PGN bits because they form the destination address in peer-to-peer communication
  - See the footnote of page 21 in the [Comprehensible Guide to J1939](https://drive.google.com/file/d/14AIyga4-BM6MF2NTKZfLU9Kp3-7uXoYC/view?usp=sharing)
  - The PGN is internally extended to 24 bits in this case (what does this mean???)
- The SOF, SRR, IDE, and RTR bits must be handled internally by socket can because they are not included in the 29 bit can id seen in the python api
  - The message stripped of these bits is called the PDU, protocol data unit, just the 29-bit id and the 8 bytes of data

## benkfra/j1939

### Receiving CAN packets

- `on_message` is a callback that is part of the Controller Application class
- It is passed to `ca._ecu.subscribe()` when an ecu subscribes to a controller application.
- This function is called by `ca.associate_ecu()` which is a very important member function called in `ecu.add_ca()` it binds the two objects together.
- `notify_subscribers()` is called by `notify()` in the last case of pgn_value == ...
- `notify()` is called by the `MessageListener` class  which is where all the raw data comes in and is stuffed into a message class and then fed to the ecu

#### Decoding a PGN

- `from_msg_id()` contains critical logic
- Also there is an and with a mask in `notify`
- There is a critical line in `notify()` that ands the result of pgn.value with a mask:
  - `pgn_value = pgn.value & 0x1FF00`
  - this actually splits out the destination address

### Sending CAN Packets

- `ecu.add_timer` specifies frequency (first arg in seconds) and how (second arg is a callback) to send out a can packet
  - The callback takes a "cookie" not sure what this is