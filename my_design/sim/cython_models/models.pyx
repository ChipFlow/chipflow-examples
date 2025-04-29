# cython: language_level=3

import cython
from cpython.buffer cimport PyObject_GetBuffer, PyBuffer_Release, PyBUF_ANY_CONTIGUOUS, PyBUF_SIMPLE
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy, memset
from libc.stdio cimport fprintf, stderr
import json
import os
import numpy as np
cimport numpy as np

# C type definitions
cdef extern from "stdint.h":
    ctypedef unsigned char uint8_t
    ctypedef unsigned int uint32_t
    ctypedef bint bool

# External C++ declarations for cxxrtl wrapper classes
cdef extern from "cxxrtl_wrap.h" namespace "cxxrtl":
    # Define the wrapper classes in a Cython-compatible way
    cdef cppclass value1_wrap:
        value1_wrap() except +
        bint bit(int n) except +
        uint32_t get_uint32() except +
        void set_uint32(uint32_t i) except +

    cdef cppclass value4_wrap:
        value4_wrap() except +
        bint bit(int n) except +
        uint32_t get_uint32() except +
        void set_uint32(uint32_t i) except +
        
    cdef cppclass value8_wrap:
        value8_wrap() except +
        bint bit(int n) except +
        uint32_t get_uint32() except +
        void set_uint32(uint32_t i) except +

cdef class PyValue1:
    cdef value1_wrap* c_value
    
    def __cinit__(self):
        self.c_value = NULL
    
    def __getitem__(self, int index):
        if self.c_value is NULL:
            raise ValueError("PyValue1 not initialized with a C++ value")
        return self.c_value.bit(index)
    
    def get(self):
        if self.c_value is NULL:
            raise ValueError("PyValue1 not initialized with a C++ value")
        return self.c_value.get_uint32()
        
    def set(self, uint32_t value):
        if self.c_value is NULL:
            raise ValueError("PyValue1 not initialized with a C++ value")
        self.c_value.set_uint32(value)

cdef class PyValue4:
    cdef value4_wrap* c_value
    
    def __cinit__(self):
        self.c_value = NULL
    
    def __getitem__(self, int index):
        if self.c_value is NULL:
            raise ValueError("PyValue4 not initialized with a C++ value")
        return self.c_value.bit(index)
    
    def get(self):
        if self.c_value is NULL:
            raise ValueError("PyValue4 not initialized with a C++ value")
        return self.c_value.get_uint32()
        
    def set(self, uint32_t value):
        if self.c_value is NULL:
            raise ValueError("PyValue4 not initialized with a C++ value")
        self.c_value.set_uint32(value)

cdef class PyValue8:
    cdef value8_wrap* c_value
    
    def __cinit__(self):
        self.c_value = NULL
    
    def __getitem__(self, int index):
        if self.c_value is NULL:
            raise ValueError("PyValue8 not initialized with a C++ value")
        return self.c_value.bit(index)
    
    def get(self):
        if self.c_value is NULL:
            raise ValueError("PyValue8 not initialized with a C++ value")
        return self.c_value.get_uint32()
        
    def set(self, uint32_t value):
        if self.c_value is NULL:
            raise ValueError("PyValue8 not initialized with a C++ value")
        self.c_value.set_uint32(value)


# Import cxxrtl_design namespace
cdef extern from "cxxrtl_wrap.h" namespace "cxxrtl_design":
    pass  # just for namespace access

# Global state
cdef object _event_log = None
cdef object _input_cmds = None
cdef size_t _input_ptr = 0
cdef dict _queued_actions = {}

# Event log functions
def open_event_log(filename):
    global _event_log
    try:
        _event_log = open(filename, "w")
        _event_log.write("{\n")
        _event_log.write("\"events\": [\n")
        fetch_actions_into_queue()
    except Exception as e:
        raise RuntimeError(f"Failed to open event log for writing: {e}")

def open_input_commands(filename):
    global _input_cmds, _input_ptr
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            _input_cmds = data["commands"]
            _input_ptr = 0
    except Exception as e:
        raise RuntimeError(f"Failed to open input commands: {e}")

def fetch_actions_into_queue():
    global _input_cmds, _input_ptr, _queued_actions
    if _input_cmds is None:
        return
    
    while _input_ptr < len(_input_cmds):
        cmd = _input_cmds[_input_ptr]
        if cmd["type"] == "wait":
            break
        if cmd["type"] != "action":
            raise ValueError("Invalid 'type' value for command")
            
        peripheral = cmd["peripheral"]
        if peripheral not in _queued_actions:
            _queued_actions[peripheral] = []
            
        _queued_actions[peripheral].append({
            "event": cmd["event"],
            "payload": cmd["payload"]
        })
        _input_ptr += 1

def log_event(unsigned timestamp, str peripheral, str event_type, payload):
    global _event_log, _input_cmds, _input_ptr
    
    if _event_log is None:
        return
        
    # Convert to JSON if not already
    if not isinstance(payload, str):
        payload_str = json.dumps(payload)
    else:
        payload_str = payload
        
    # Write to event log
    static_had_event = [False]  # Use a list as a static mutable variable
    if static_had_event[0]:
        _event_log.write(",\n")
        
    _event_log.write(f"{{ \"timestamp\": {timestamp}, \"peripheral\": \"{peripheral}\", "
                    f"\"event\": \"{event_type}\", \"payload\": {payload_str} }}")
    static_had_event[0] = True
    
    # Check if we have actions waiting on this
    if _input_cmds is not None and _input_ptr < len(_input_cmds):
        cmd = _input_cmds[_input_ptr]
        if (cmd["type"] == "wait" and cmd["peripheral"] == peripheral and 
                cmd["event"] == event_type and cmd["payload"] == payload):
            _input_ptr += 1
            fetch_actions_into_queue()

def get_pending_actions(str peripheral):
    global _queued_actions
    
    if peripheral in _queued_actions:
        actions = _queued_actions[peripheral]
        _queued_actions[peripheral] = []
        return actions
    return []

def close_event_log():
    global _event_log, _input_cmds, _input_ptr
    
    if _event_log is None:
        return
        
    _event_log.write("\n]\n")
    _event_log.write("}\n")
    _event_log.close()
    
    if _input_cmds is not None and _input_ptr != len(_input_cmds):
        fprintf(stderr, "WARNING: not all input actions were executed (%d/%d remain)!\n",
                <int>(len(_input_cmds) - _input_ptr), <int>(len(_input_cmds)))

# SPI Flash model
cdef class spiflash_model:
    cdef str name
    cdef PyValue1 clk
    cdef PyValue1 csn
    cdef PyValue4 d_o
    cdef PyValue4 d_oe
    cdef PyValue4 d_i
    cdef np.ndarray _data_np
    cdef uint8_t* _data_ptr
    cdef bint _last_clk
    cdef bint _last_csn
    cdef int _bit_count
    cdef int _byte_count
    cdef unsigned _data_width
    cdef uint32_t _addr
    cdef uint8_t _curr_byte
    cdef uint8_t _command
    cdef uint8_t _out_buffer
    
    def __cinit__(self, str name, PyValue1 clk, PyValue1 csn, PyValue4 d_o, PyValue4 d_oe, PyValue4 d_i):
        self.name = name
        self.clk = clk
        self.csn = csn
        self.d_o = d_o
        self.d_oe = d_oe
        self.d_i = d_i
        
        # Initialize memory (16MB)
        self._data_np = np.ones(16*1024*1024, dtype=np.uint8) * 0xFF
        self._data_ptr = <uint8_t*>self._data_np.data
        
        # Initialize state
        self._last_clk = False
        self._last_csn = False
        self._bit_count = 0
        self._byte_count = 0
        self._data_width = 1
        self._addr = 0
        self._curr_byte = 0
        self._command = 0
        self._out_buffer = 0
    
    def load_data(self, str filename, unsigned offset):
        if offset >= self._data_np.size:
            raise IndexError("flash: offset beyond end")
            
        try:
            with open(filename, "rb") as f:
                data = np.fromfile(f, dtype=np.uint8)
                max_copy = min(len(data), self._data_np.size - offset)
                self._data_np[offset:offset+max_copy] = data[:max_copy]
        except Exception as e:
            raise RuntimeError(f"flash: failed to read input file: {filename}, {e}")
    
    cpdef step(self, unsigned timestamp):
        cdef bint csn_val = <bint>self.csn[0].get()
        cdef bint clk_val = <bint>self.clk[0].get()
        
        # Process data if chip select changes from high to low
        if csn_val and not self._last_csn:
            self._bit_count = 0
            self._byte_count = 0
            self._data_width = 1
        # Process data on clock rising edge when chip select is low
        elif clk_val and not self._last_clk and not csn_val:
            if self._data_width == 4:
                self._curr_byte = (self._curr_byte << 4) | (self.d_o[0].get() & 0xF)
            else:
                self._curr_byte = (self._curr_byte << 1) | (<uint8_t>self.d_o[0].bit(0))
            
            self._out_buffer = self._out_buffer << self._data_width
            self._bit_count += self._data_width
            
            if self._bit_count == 8:
                self._process_byte()
                self._byte_count += 1
                self._bit_count = 0
        # Output data on clock falling edge when chip select is low
        elif not clk_val and self._last_clk and not csn_val:
            if self._data_width == 4:
                self.d_i[0].set((self._out_buffer >> 4) & 0xF)
            else:
                self.d_i[0].set(((self._out_buffer >> 7) & 0x1) << 1)
        
        self._last_clk = clk_val
        self._last_csn = csn_val
    
    cdef void _process_byte(self):
        self._out_buffer = 0
        if self._byte_count == 0:
            self._addr = 0
            self._data_width = 1
            self._command = self._curr_byte
            
            # Handle different commands
            if self._command == 0xab:
                pass  # Power up
            elif (self._command == 0x03 or self._command == 0x9f or self._command == 0xff or
                  self._command == 0x35 or self._command == 0x31 or self._command == 0x50 or
                  self._command == 0x05 or self._command == 0x01 or self._command == 0x06):
                pass  # Nothing special to do
            elif self._command == 0xeb:
                self._data_width = 4
            else:
                raise RuntimeError(f"flash: unknown command {self._command:02x}")
        else:
            if self._command == 0x03:  # Single read
                if self._byte_count <= 3:
                    self._addr |= ((<uint32_t>self._curr_byte) << ((3 - self._byte_count) * 8))
                if self._byte_count >= 3:
                    self._out_buffer = self._data_ptr[self._addr]
                    self._addr = (self._addr + 1) & 0x00FFFFFF
            elif self._command == 0xeb:  # Quad read
                if self._byte_count <= 3:
                    self._addr |= ((<uint32_t>self._curr_byte) << ((3 - self._byte_count) * 8))
                if self._byte_count >= 6:  # After mode byte and dummy clocks
                    self._out_buffer = self._data_ptr[self._addr]
                    self._addr = (self._addr + 1) & 0x00FFFFFF
        
        # Handle read ID command
        if self._command == 0x9f:
            flash_id = [0xCA, 0x7C, 0xA7, 0xFF]
            self._out_buffer = flash_id[self._byte_count % 4]

# UART model
cdef class uart_model:
    cdef str name
    cdef PyValue1 tx
    cdef PyValue1 rx
    cdef unsigned baud_div
    cdef bint _tx_last
    cdef int _rx_counter
    cdef uint8_t _rx_sr
    cdef bint _tx_active
    cdef int _tx_counter
    cdef uint8_t _tx_data
    
    def __cinit__(self, str name, PyValue1 tx, PyValue1 rx, unsigned baud_div=25000000//115200):
        self.name = name
        self.tx = tx
        self.rx = rx
        self.baud_div = baud_div
        
        # Initialize state
        self._tx_last = False
        self._rx_counter = 0
        self._rx_sr = 0
        self._tx_active = False
        self._tx_counter = 0
        self._tx_data = 0
    
    cpdef step(self, unsigned timestamp):
        cdef bint tx_val = <bint>self.tx[0].get()
        
        # Process actions
        for action in get_pending_actions(self.name):
            if action["event"] == "tx":
                self._tx_active = True
                self._tx_data = int(action["payload"])
        
        # Receive processing
        if self._rx_counter == 0:
            if self._tx_last and not tx_val:  # Start bit
                self._rx_counter = 1
        else:
            self._rx_counter += 1
            if self._rx_counter > (self.baud_div // 2) and ((self._rx_counter - (self.baud_div // 2)) % self.baud_div) == 0:
                bit = ((self._rx_counter - (self.baud_div // 2)) // self.baud_div)
                
                if bit >= 1 and bit <= 8:
                    # Update shift register
                    self._rx_sr = (0x80 if tx_val else 0x00) | (self._rx_sr >> 1)
                
                if bit == 8:
                    # Log received byte
                    log_event(timestamp, self.name, "tx", self._rx_sr)
                    if self.name == "uart_0":
                        fprintf(stderr, "%c", <char>self._rx_sr)
                
                if bit == 9:  # End
                    self._rx_counter = 0
        
        self._tx_last = tx_val
        
        # Transmit processing
        if self._tx_active:
            self._tx_counter += 1
            bit = (self._tx_counter // self.baud_div)
            
            if bit == 0:
                self.rx[0].set(0)  # Start bit
            elif bit >= 1 and bit <= 8:
                self.rx[0].set((self._tx_data >> (bit - 1)) & 0x1)
            elif bit == 9:  # Stop bit
                self.rx[0].set(1)
            else:
                self._tx_active = False
        else:
            self._tx_counter = 0
            self.rx[0].set(1)  # Idle

# GPIO model
cdef class gpio_model:
    cdef str name
    cdef PyValue8 o
    cdef PyValue8 oe
    cdef PyValue8 i
    cdef uint32_t _input_data
    cdef uint32_t _o_last
    cdef uint32_t _oe_last
    
    def __cinit__(self, str name, PyValue8 o, PyValue8 oe, PyValue8 i):
        self.name = name
        self.o = o
        self.oe = oe
        self.i = i
        
        # Initialize state
        self._input_data = 0
        self._o_last = 0
        self._oe_last = 0
    
    cpdef step(self, unsigned timestamp):
        cdef uint32_t o_value = self.o[0].get()
        cdef uint32_t oe_value = self.oe[0].get()
        
        # Process actions
        for action in get_pending_actions(self.name):
            if action["event"] == "set":
                bin_str = str(action["payload"])
                self._input_data = 0
                for i in range(8):  # Hardcoded width=8
                    if bin_str[7-i] == '1':  # MSB first
                        self._input_data |= (1 << i)
        
        # Log changes
        if o_value != self._o_last or oe_value != self._oe_last:
            formatted_value = ""
            for i in range(7, -1, -1):  # MSB first, width=8
                if oe_value & (1 << i):
                    formatted_value += '1' if (o_value & (1 << i)) else '0'
                else:
                    formatted_value += 'Z'
            log_event(timestamp, self.name, "change", formatted_value)
        
        # Update inputs
        self.i[0].set((self._input_data & ~oe_value) | (o_value & oe_value))
        self._o_last = o_value
        self._oe_last = oe_value

# SPI model
cdef class spi_model:
    cdef str name
    cdef PyValue1 clk
    cdef PyValue1 csn
    cdef PyValue1 copi
    cdef PyValue1 cipo
    cdef bint _last_clk
    cdef bint _last_csn
    cdef int _bit_count
    cdef uint32_t _send_data
    cdef uint32_t _width
    cdef uint32_t _in_buffer
    cdef uint32_t _out_buffer
    
    def __cinit__(self, str name, PyValue1 clk, PyValue1 csn, PyValue1 copi, PyValue1 cipo):
        self.name = name
        self.clk = clk
        self.csn = csn
        self.copi = copi
        self.cipo = cipo
        
        # Initialize state
        self._last_clk = False
        self._last_csn = False
        self._bit_count = 0
        self._send_data = 0
        self._width = 8
        self._in_buffer = 0
        self._out_buffer = 0
    
    cpdef step(self, unsigned timestamp):
        cdef bint csn_val = <bint>self.csn[0].get()
        cdef bint clk_val = <bint>self.clk[0].get()
        
        # Process actions
        for action in get_pending_actions(self.name):
            if action["event"] == "set_data":
                self._out_buffer = self._send_data = int(action["payload"])
            if action["event"] == "set_width":
                self._width = int(action["payload"])
        
        # Process SPI protocol
        if csn_val and not self._last_csn:
            self._bit_count = 0
            self._in_buffer = 0
            self._out_buffer = self._send_data
            log_event(timestamp, self.name, "deselect", "")
        elif not csn_val and self._last_csn:
            log_event(timestamp, self.name, "select", "")
        elif clk_val and not self._last_clk and not csn_val:
            self._in_buffer = (self._in_buffer << 1) | (<uint32_t>self.copi[0].bit(0))
            self._out_buffer = self._out_buffer << 1
            self._bit_count += 1
            
            if self._bit_count == self._width:
                log_event(timestamp, self.name, "data", self._in_buffer)
                self._bit_count = 0
        elif not clk_val and self._last_clk and not csn_val:
            self.cipo[0].set(((self._out_buffer >> (self._width - 1)) & 0x1))
        
        self._last_clk = clk_val
        self._last_csn = csn_val

# I2C model
cdef class i2c_model:
    cdef str name
    cdef PyValue1 sda_oe
    cdef PyValue1 sda_i
    cdef PyValue1 scl_oe
    cdef PyValue1 scl_i
    cdef int _byte_count
    cdef int _bit_count
    cdef bint _do_ack
    cdef bint _is_read
    cdef uint8_t _read_data
    cdef uint8_t _sr
    cdef bint _drive_sda
    cdef bint _last_sda
    cdef bint _last_scl
    
    def __cinit__(self, str name, PyValue1 sda_oe, PyValue1 sda_i, PyValue1 scl_oe, PyValue1 scl_i):
        self.name = name
        self.sda_oe = sda_oe
        self.sda_i = sda_i
        self.scl_oe = scl_oe
        self.scl_i = scl_i
        
        # Initialize state
        self._byte_count = 0
        self._bit_count = 0
        self._do_ack = False
        self._is_read = False
        self._read_data = 0
        self._sr = 0
        self._drive_sda = True
        self._last_sda = False
        self._last_scl = False
    
    cpdef step(self, unsigned timestamp):
        cdef bint sda = not <bint>self.sda_oe[0].get()
        cdef bint scl = not <bint>self.scl_oe[0].get()
        
        # Process actions
        for action in get_pending_actions(self.name):
            if action["event"] == "ack":
                self._do_ack = True
            elif action["event"] == "nack":
                self._do_ack = False
            elif action["event"] == "set_data":
                self._read_data = int(action["payload"])
        
        # Process I2C protocol
        if self._last_scl and self._last_sda and not sda:
            # START condition
            log_event(timestamp, self.name, "start", "")
            self._sr = 0xFF
            self._byte_count = 0
            self._bit_count = 0
            self._is_read = False
            self._drive_sda = True
        elif scl and not self._last_scl:
            # SCL rising edge
            if self._byte_count == 0 or not self._is_read:
                self._sr = (self._sr << 1) | (sda & 0x1)
            
            self._bit_count += 1
            if self._bit_count == 8:
                if self._byte_count == 0:
                    # Address byte
                    self._is_read = (self._sr & 0x1)
                    log_event(timestamp, self.name, "address", self._sr)
                elif not self._is_read:
                    # Write data
                    log_event(timestamp, self.name, "write", self._sr)
                
                self._byte_count += 1
            elif self._bit_count == 9:
                self._bit_count = 0
        elif not scl and self._last_scl:
            # SCL falling edge
            self._drive_sda = True  # Idle high
            
            if self._bit_count == 8:
                self._drive_sda = not self._do_ack
            elif self._byte_count > 0 and self._is_read:
                if self._bit_count == 0:
                    self._sr = self._read_data
                else:
                    self._sr = self._sr << 1
                
                self._drive_sda = (self._sr >> 7) & 0x1
        elif self._last_scl and not self._last_sda and sda:
            # STOP condition
            log_event(timestamp, self.name, "stop", "")
            self._drive_sda = True
        
        # Update state and pins
        self._last_sda = sda
        self._last_scl = scl
        self.sda_i[0].set(sda and self._drive_sda)
        self.scl_i[0].set(scl)
