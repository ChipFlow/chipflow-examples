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
    ctypedef unsigned long long uint64_t
    ctypedef signed long long int64_t
    ctypedef size_t size_t
    ctypedef int bool

# Define CXXRTL CAPI structures and functions
cdef extern from "cxxrtl/capi/cxxrtl_capi.h":
    # Opaque reference types
    ctypedef struct _cxxrtl_toplevel:
        pass
    ctypedef _cxxrtl_toplevel* cxxrtl_toplevel
    
    ctypedef struct _cxxrtl_handle:
        pass
    ctypedef _cxxrtl_handle* cxxrtl_handle
    
    ctypedef struct _cxxrtl_outline:
        pass
    ctypedef _cxxrtl_outline* cxxrtl_outline
    
    ctypedef struct _cxxrtl_attr_set:
        pass
    ctypedef _cxxrtl_attr_set* cxxrtl_attr_set
    
    # Type enums
    ctypedef enum cxxrtl_type:
        CXXRTL_VALUE,
        CXXRTL_WIRE,
        CXXRTL_MEMORY,
        CXXRTL_ALIAS,
        CXXRTL_OUTLINE
    
    # Flag enums
    ctypedef enum cxxrtl_flag:
        CXXRTL_INPUT = 1 << 0,
        CXXRTL_OUTPUT = 1 << 1,
        CXXRTL_INOUT = (CXXRTL_INPUT|CXXRTL_OUTPUT),
        CXXRTL_DRIVEN_SYNC = 1 << 2,
        CXXRTL_DRIVEN_COMB = 1 << 3,
        CXXRTL_UNDRIVEN = 1 << 4
    
    # Attribute type enum
    ctypedef enum cxxrtl_attr_type:
        CXXRTL_ATTR_NONE = 0,
        CXXRTL_ATTR_UNSIGNED_INT = 1,
        CXXRTL_ATTR_SIGNED_INT = 2,
        CXXRTL_ATTR_STRING = 3,
        CXXRTL_ATTR_DOUBLE = 4
    
    # Object description structure
    struct cxxrtl_object:
        uint32_t type
        uint32_t flags
        size_t width
        size_t lsb_at
        size_t depth
        size_t zero_at
        uint32_t *curr
        uint32_t *next
        _cxxrtl_outline *outline
        _cxxrtl_attr_set *attrs
    
    # Core functions
    cxxrtl_handle cxxrtl_create(cxxrtl_toplevel design)
    cxxrtl_handle cxxrtl_create_at(cxxrtl_toplevel design, const char *top_path)
    void cxxrtl_destroy(cxxrtl_handle handle)
    void cxxrtl_reset(cxxrtl_handle handle)
    int cxxrtl_eval(cxxrtl_handle handle)
    int cxxrtl_commit(cxxrtl_handle handle)
    size_t cxxrtl_step(cxxrtl_handle handle)
    
    # Object access functions
    cxxrtl_object* cxxrtl_get_parts(cxxrtl_handle handle, const char *name, size_t *parts)
    
    # This is a C inline function, so we need to reimplement it in Cython
    # static inline struct cxxrtl_object *cxxrtl_get(cxxrtl_handle handle, const char *name) {...}
    
    # Enumeration callback function type
    ctypedef void (*enum_callback_t)(void *data, const char *name, cxxrtl_object *object, size_t parts)
    
    # Enumeration function
    void cxxrtl_enum(cxxrtl_handle handle, void *data, enum_callback_t callback)
    
    # Outline functions
    void cxxrtl_outline_eval(cxxrtl_outline outline)
    
    # Attribute functions
    int cxxrtl_attr_type(cxxrtl_attr_set attrs, const char *name)
    uint64_t cxxrtl_attr_get_unsigned_int(cxxrtl_attr_set attrs, const char *name)
    int64_t cxxrtl_attr_get_signed_int(cxxrtl_attr_set attrs, const char *name)
    const char* cxxrtl_attr_get_string(cxxrtl_attr_set attrs, const char *name)
    double cxxrtl_attr_get_double(cxxrtl_attr_set attrs, const char *name)

# VCD writer support
cdef extern from "cxxrtl/capi/cxxrtl_capi_vcd.h":
    # Opaque reference type
    ctypedef struct _cxxrtl_vcd:
        pass
    ctypedef _cxxrtl_vcd* cxxrtl_vcd
    
    # VCD functions
    cxxrtl_vcd cxxrtl_vcd_create()
    void cxxrtl_vcd_destroy(cxxrtl_vcd vcd)
    void cxxrtl_vcd_timescale(cxxrtl_vcd vcd, int number, const char *unit)
    void cxxrtl_vcd_add(cxxrtl_vcd vcd, const char *name, cxxrtl_object *object)
    void cxxrtl_vcd_add_from(cxxrtl_vcd vcd, cxxrtl_handle handle)
    
    # VCD filter callback function type
    ctypedef int (*vcd_filter_t)(void *data, const char *name, const cxxrtl_object *object)
    
    # Filtered VCD functions
    void cxxrtl_vcd_add_from_if(cxxrtl_vcd vcd, cxxrtl_handle handle, void *data, vcd_filter_t filter)
    void cxxrtl_vcd_add_from_without_memories(cxxrtl_vcd vcd, cxxrtl_handle handle)
    void cxxrtl_vcd_sample(cxxrtl_vcd vcd, uint64_t time)
    void cxxrtl_vcd_read(cxxrtl_vcd vcd, const char **data, size_t *size)

# Reimplement the cxxrtl_get inline function from the C API
cdef cxxrtl_object* cxxrtl_get(cxxrtl_handle handle, const char *name):
    cdef size_t parts = 0
    cdef cxxrtl_object *object = cxxrtl_get_parts(handle, name, &parts)
    if object == NULL or parts == 1:
        return object
    return NULL

# Python wrapper for cxxrtl_object
cdef class Object:
    cdef cxxrtl_object* _obj
    cdef bint _owns_memory
    cdef str _name
    
    def __cinit__(self):
        self._obj = NULL
        self._owns_memory = False
        self._name = ""
    
    @staticmethod
    cdef Object from_ptr(cxxrtl_object* obj_ptr, str name=""):
        cdef Object obj = Object()
        obj._obj = obj_ptr
        obj._owns_memory = False
        obj._name = name
        return obj
        
    def __dealloc__(self):
        if self._owns_memory and self._obj != NULL:
            free(self._obj)
            self._obj = NULL
    
    @property
    def type(self):
        if self._obj == NULL:
            return None
            
        if self._obj.type == CXXRTL_VALUE:
            return "value"
        elif self._obj.type == CXXRTL_WIRE:
            return "wire"
        elif self._obj.type == CXXRTL_MEMORY:
            return "memory"
        elif self._obj.type == CXXRTL_ALIAS:
            return "alias"
        elif self._obj.type == CXXRTL_OUTLINE:
            return "outline"
        else:
            return f"unknown({self._obj.type})"
    
    @property
    def name(self):
        return self._name
    
    @property
    def flags(self):
        if self._obj == NULL:
            return set()
            
        result = set()
        if self._obj.flags & CXXRTL_INPUT:
            result.add("input")
        if self._obj.flags & CXXRTL_OUTPUT:
            result.add("output")
        if self._obj.flags & CXXRTL_DRIVEN_SYNC:
            result.add("driven_sync")
        if self._obj.flags & CXXRTL_DRIVEN_COMB:
            result.add("driven_comb")
        if self._obj.flags & CXXRTL_UNDRIVEN:
            result.add("undriven")
        return result
    
    @property
    def width(self):
        if self._obj == NULL:
            return 0
        return self._obj.width
    
    @property
    def depth(self):
        if self._obj == NULL:
            return 0
        return self._obj.depth
    
    @property
    def chunks(self):
        if self._obj == NULL:
            return 0
        return (self._obj.width + 31) // 32
    
    def get_value(self):
        cdef size_t num_chunks
        cdef uint64_t result
        cdef np.ndarray[np.uint32_t, ndim=1] arr
        
        if self._obj == NULL:
            return None
            
        # For zero-width objects
        if self._obj.width == 0:
            return 0
            
        # Calculate the number of 32-bit chunks needed
        num_chunks = (self._obj.width + 31) // 32
        
        # For values that fit in a single 64-bit integer
        if num_chunks <= 2 and self._obj.width <= 64:
            result = 0
            for i in range(num_chunks):
                result |= (<uint64_t>self._obj.curr[i]) << (i * 32)
            return result
            
        # For larger values, use a NumPy array
        arr = np.zeros(num_chunks, dtype=np.uint32)
        for i in range(num_chunks):
            arr[i] = self._obj.curr[i]
        return arr
    
    def set_value(self, value):
        cdef size_t num_chunks
        
        if self._obj == NULL or self._obj.next == NULL:
            return False
            
        # For zero-width objects
        if self._obj.width == 0:
            return True
            
        # Calculate the number of 32-bit chunks needed
        num_chunks = (self._obj.width + 31) // 32
        
        # Handle integer values
        if isinstance(value, int) and num_chunks <= 2:
            for i in range(num_chunks):
                self._obj.next[i] = (value >> (i * 32)) & 0xFFFFFFFF
            return True
            
        # Handle NumPy arrays or lists
        if isinstance(value, (np.ndarray, list)):
            for i in range(min(len(value), num_chunks)):
                self._obj.next[i] = int(value[i]) & 0xFFFFFFFF
            return True
            
        return False
    
    def get_bit(self, unsigned int index):
        cdef unsigned int chunk
        cdef unsigned int bit
        cdef bint result
        
        if self._obj == NULL or index >= self._obj.width:
            return None
            
        chunk = index // 32
        bit = index % 32
        result = (self._obj.curr[chunk] & (1 << bit)) != 0
        return result
    
    def set_bit(self, unsigned int index, bint value):
        if self._obj == NULL or self._obj.next == NULL or index >= self._obj.width:
            return False
            
        cdef unsigned int chunk = index // 32
        cdef unsigned int bit = index % 32
        
        if value:
            self._obj.next[chunk] |= (1 << bit)
        else:
            self._obj.next[chunk] &= ~(1 << bit)
            
        return True
    
    def get_attributes(self):
        if self._obj == NULL or self._obj.attrs == NULL:
            return {}
            
        result = {}
        # Implement attribute extraction
        return result

# Python wrapper for CXXRTL handle
cdef class Design:
    cdef cxxrtl_handle _handle
    cdef bint _owns_handle
    cdef str _top_path
    cdef dict _objects
    
    def __cinit__(self):
        self._handle = NULL
        self._owns_handle = False
        self._top_path = ""
        self._objects = {}
    
    @staticmethod
    cdef Design from_toplevel(cxxrtl_toplevel toplevel, str top_path=None):
        cdef Design design = Design()
        
        if top_path is not None:
            design._handle = cxxrtl_create_at(toplevel, top_path.encode('utf-8'))
            design._top_path = top_path
        else:
            design._handle = cxxrtl_create(toplevel)
            design._top_path = ""
            
        design._owns_handle = True
        design._objects = {}
        return design
    
    @staticmethod
    cdef Design from_handle(cxxrtl_handle handle, bint owns=True):
        cdef Design design = Design()
        design._handle = handle
        design._owns_handle = owns
        design._top_path = ""
        design._objects = {}
        return design
    
    def __dealloc__(self):
        if self._owns_handle and self._handle != NULL:
            cxxrtl_destroy(self._handle)
            self._handle = NULL
    
    def reset(self):
        if self._handle != NULL:
            cxxrtl_reset(self._handle)
            return True
        return False
    
    def eval(self):
        cdef int result
        if self._handle != NULL:
            result = cxxrtl_eval(self._handle)
            return result != 0
        return False
    
    def commit(self):
        cdef int result
        if self._handle != NULL:
            result = cxxrtl_commit(self._handle)
            return result != 0
        return False
    
    def step(self):
        if self._handle != NULL:
            return cxxrtl_step(self._handle)
        return 0
    
    def get_object(self, str name):
        if self._handle == NULL:
            return None
            
        # Check cache first
        if name in self._objects:
            return self._objects[name]
            
        cdef cxxrtl_object* obj_ptr = cxxrtl_get(self._handle, name.encode('utf-8'))
        if obj_ptr == NULL:
            return None
            
        obj = Object.from_ptr(obj_ptr, name)
        self._objects[name] = obj
        return obj
    
    def get_parts(self, str name):
        if self._handle == NULL:
            return []
            
        cdef size_t parts_count = 0
        cdef cxxrtl_object* parts_ptr = cxxrtl_get_parts(self._handle, name.encode('utf-8'), &parts_count)
        
        if parts_ptr == NULL:
            return []
            
        result = []
        for i in range(parts_count):
            obj = Object.from_ptr(&parts_ptr[i], f"{name}[{i}]")
            result.append(obj)
            
        return result
    
    def get_all_objects(self):
        if self._handle == NULL:
            return []
            
        objects = []
        self._objects = {}
        
        cdef void* objects_ptr = <void*>objects
        cxxrtl_enum(self._handle, objects_ptr, _enum_callback)
        
        return objects
        
# Callback function for cxxrtl_enum
cdef void _enum_callback(void *data, const char *name, cxxrtl_object *object, size_t parts) noexcept with gil:
    cdef list objects_list
    cdef str py_name
    cdef Object obj
    cdef Object part_obj
    cdef size_t i
    
    try:
        objects_list = <list>data
        py_name = name.decode('utf-8')
        
        if parts == 1:
            obj = Object.from_ptr(object, py_name)
            objects_list.append(obj)
        else:
            for i in range(parts):
                part_obj = Object.from_ptr(&object[i], f"{py_name}[{i}]")
                objects_list.append(part_obj)
    except:
        # Noexcept function can't propagate exceptions
        pass

# Python wrapper for VCD writer
cdef class VcdWriter:
    cdef cxxrtl_vcd _vcd
    cdef bint _owns_vcd
    cdef object _buffer
    
    def __cinit__(self):
        self._vcd = NULL
        self._owns_vcd = False
        self._buffer = None
    
    def __init__(self):
        self._vcd = cxxrtl_vcd_create()
        self._owns_vcd = True
        self._buffer = None
    
    def __dealloc__(self):
        if self._owns_vcd and self._vcd != NULL:
            cxxrtl_vcd_destroy(self._vcd)
            self._vcd = NULL
    
    def set_timescale(self, int number, str unit):
        if self._vcd == NULL:
            return False
            
        if number not in [1, 10, 100]:
            raise ValueError("Timescale number must be 1, 10, or 100")
            
        if unit not in ["s", "ms", "us", "ns", "ps", "fs"]:
            raise ValueError("Timescale unit must be one of: s, ms, us, ns, ps, fs")
            
        cxxrtl_vcd_timescale(self._vcd, number, unit.encode('utf-8'))
        return True
    
    def add_object(self, str name, Object obj):
        if self._vcd == NULL or obj._obj == NULL:
            return False
            
        cxxrtl_vcd_add(self._vcd, name.encode('utf-8'), obj._obj)
        return True
    
    def add_all_from_design(self, Design design):
        if self._vcd == NULL or design._handle == NULL:
            return False
            
        cxxrtl_vcd_add_from(self._vcd, design._handle)
        return True
    
    def add_from_design_without_memories(self, Design design):
        if self._vcd == NULL or design._handle == NULL:
            return False
            
        cxxrtl_vcd_add_from_without_memories(self._vcd, design._handle)
        return True
    
    def sample(self, uint64_t time):
        if self._vcd == NULL:
            return False
            
        cxxrtl_vcd_sample(self._vcd, time)
        return True
    
    def read(self):
        if self._vcd == NULL:
            return b""
            
        cdef const char* data
        cdef size_t size
        cxxrtl_vcd_read(self._vcd, &data, &size)
        
        if size == 0:
            return b""
            
        return data[:size]
    
    def read_all(self):
        if self._vcd == NULL:
            return b""
            
        chunks = []
        while True:
            chunk = self.read()
            if not chunk:
                break
            chunks.append(chunk)
            
        return b"".join(chunks)
    
    def write_to_file(self, str filename):
        if self._vcd == NULL:
            return False
            
        with open(filename, "wb") as f:
            while True:
                chunk = self.read()
                if not chunk:
                    break
                f.write(chunk)
                
        return True