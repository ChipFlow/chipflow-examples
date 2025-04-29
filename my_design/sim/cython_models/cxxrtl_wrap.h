#ifndef CXXRTL_WRAP_H
#define CXXRTL_WRAP_H

#include <cxxrtl/cxxrtl.h>
#include "vendor/nlohmann/json.hpp"
#include <string>
#include <vector>
#include <algorithm>
#include <optional>

// This header ensures the CXXRTL templates are accessible to Cython
// It re-exports the types needed by the Cython bindings

// Define helper wrapper classes with non-template methods for Cython to use
namespace cxxrtl {
    // Create specialized wrapper classes for each value width
    class value1_wrap : public value<1> {
    public:
        uint32_t get_uint32() const { return get<uint32_t>(); }
        void set_uint32(uint32_t v) { set<uint32_t>(v); }
    };
    
    class value4_wrap : public value<4> {
    public:
        uint32_t get_uint32() const { return get<uint32_t>(); }
        void set_uint32(uint32_t v) { set<uint32_t>(v); }
    };
    
    class value8_wrap : public value<8> {
    public:
        uint32_t get_uint32() const { return get<uint32_t>(); }
        void set_uint32(uint32_t v) { set<uint32_t>(v); }
    };
}

namespace cxxrtl_design {
    using namespace cxxrtl;
    using json = nlohmann::json;
    
    // Forward declarations for structs used in models
    struct action {
        action(const std::string &event, const json &payload) : event(event), payload(payload) {};
        std::string event;
        json payload;
    };
}

#endif // CXXRTL_WRAP_H