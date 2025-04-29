#undef NDEBUG

#include <cxxrtl/cxxrtl.h>
#include <cxxrtl/cxxrtl_server.h>
#include "sim_soc.h"
#include "cython_models/cxxrtl_wrap.h"

#include <fstream>
#include <filesystem>

// Python initialization
#include <Python.h>

using namespace cxxrtl::time_literals;
using namespace cxxrtl_design;

int main(int argc, char **argv) {
    // Initialize Python
    Py_Initialize();
    
    // Set up the Python path to include current directory
    PyObject* sys_path = PySys_GetObject("path");
    PyObject* pwd = PyUnicode_FromString(".");
    PyList_Append(sys_path, pwd);
    Py_DECREF(pwd);
    
    // Import our Cython module
    PyObject* module_name = PyUnicode_FromString("models");
    PyObject* module = PyImport_Import(module_name);
    Py_DECREF(module_name);
    
    if (!module) {
        PyErr_Print();
        std::cerr << "Failed to import Cython models module" << std::endl;
        return 1;
    }
    
    // Create the top-level design
    p_sim__top top;

    // Create a Python dictionary to hold our model instances
    PyObject* py_dict = PyDict_New();
    
    // Import the necessary Python functions from our module
    PyObject* py_open_event_log = PyObject_GetAttrString(module, "open_event_log");
    PyObject* py_open_input_commands = PyObject_GetAttrString(module, "open_input_commands");
    PyObject* py_close_event_log = PyObject_GetAttrString(module, "close_event_log");
    
    // Import model classes
    PyObject* py_spiflash_model_class = PyObject_GetAttrString(module, "spiflash_model");
    PyObject* py_uart_model_class = PyObject_GetAttrString(module, "uart_model");
    PyObject* py_gpio_model_class = PyObject_GetAttrString(module, "gpio_model");
    PyObject* py_spi_model_class = PyObject_GetAttrString(module, "spi_model");
    PyObject* py_i2c_model_class = PyObject_GetAttrString(module, "i2c_model");
    
    // Import PyValue classes
    PyObject* py_value1_class = PyObject_GetAttrString(module, "PyValue1");
    PyObject* py_value4_class = PyObject_GetAttrString(module, "PyValue4");
    PyObject* py_value8_class = PyObject_GetAttrString(module, "PyValue8");
    
    // Create model instances
    PyObject* py_args = PyTuple_New(6); // Maximum number of arguments needed
    
    // Create PyValue objects
    PyObject* py_flash_clk = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_flash_csn = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_flash_d_o = PyObject_CallObject(py_value4_class, NULL);
    PyObject* py_flash_d_oe = PyObject_CallObject(py_value4_class, NULL);
    PyObject* py_flash_d_i = PyObject_CallObject(py_value4_class, NULL);
    
    // Create wrapper objects - we need to use static_cast to convert to the wrapper types
    auto* flash_clk_wrap = static_cast<cxxrtl::value1_wrap*>(&top.p_flash____clk____o);
    auto* flash_csn_wrap = static_cast<cxxrtl::value1_wrap*>(&top.p_flash____csn____o);
    auto* flash_d_o_wrap = static_cast<cxxrtl::value4_wrap*>(&top.p_flash____d____o);
    auto* flash_d_oe_wrap = static_cast<cxxrtl::value4_wrap*>(&top.p_flash____d____oe);
    auto* flash_d_i_wrap = static_cast<cxxrtl::value4_wrap*>(&top.p_flash____d____i);
    
    // Set the C++ value pointers inside the PyValue objects
    PyObject_SetAttrString(py_flash_clk, "c_value", PyCapsule_New(flash_clk_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_flash_csn, "c_value", PyCapsule_New(flash_csn_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_flash_d_o, "c_value", PyCapsule_New(flash_d_o_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_flash_d_oe, "c_value", PyCapsule_New(flash_d_oe_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_flash_d_i, "c_value", PyCapsule_New(flash_d_i_wrap, "cxxrtl_value_wrap", NULL));
    
    // SPI Flash
    PyTuple_SetItem(py_args, 0, PyUnicode_FromString("flash"));
    PyTuple_SetItem(py_args, 1, py_flash_clk);
    PyTuple_SetItem(py_args, 2, py_flash_csn);
    PyTuple_SetItem(py_args, 3, py_flash_d_o);
    PyTuple_SetItem(py_args, 4, py_flash_d_oe);
    PyTuple_SetItem(py_args, 5, py_flash_d_i);
    PyObject* py_flash = PyObject_CallObject(py_spiflash_model_class, py_args);
    PyDict_SetItemString(py_dict, "flash", py_flash);
    
    // UART models
    Py_DECREF(py_args);
    py_args = PyTuple_New(3);
    
    // Create PyValue objects for UART0
    PyObject* py_uart0_tx = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_uart0_rx = PyObject_CallObject(py_value1_class, NULL);
    
    // Create wrapper objects
    auto* uart0_tx_wrap = static_cast<cxxrtl::value1_wrap*>(&top.p_uart__0____tx____o);
    auto* uart0_rx_wrap = static_cast<cxxrtl::value1_wrap*>(&top.p_uart__0____rx____i);
    
    // Set the C++ value pointers
    PyObject_SetAttrString(py_uart0_tx, "c_value", PyCapsule_New(uart0_tx_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_uart0_rx, "c_value", PyCapsule_New(uart0_rx_wrap, "cxxrtl_value_wrap", NULL));
    
    PyTuple_SetItem(py_args, 0, PyUnicode_FromString("uart_0"));
    PyTuple_SetItem(py_args, 1, py_uart0_tx);
    PyTuple_SetItem(py_args, 2, py_uart0_rx);
    PyObject* py_uart_0 = PyObject_CallObject(py_uart_model_class, py_args);
    PyDict_SetItemString(py_dict, "uart_0", py_uart_0);
    
    Py_DECREF(py_args);
    py_args = PyTuple_New(3);
    
    // Create PyValue objects for UART1
    PyObject* py_uart1_tx = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_uart1_rx = PyObject_CallObject(py_value1_class, NULL);
    
    // Create wrapper objects
    auto* uart1_tx_wrap = static_cast<cxxrtl::value1_wrap*>(&top.p_uart__1____tx____o);
    auto* uart1_rx_wrap = static_cast<cxxrtl::value1_wrap*>(&top.p_uart__1____rx____i);
    
    // Set the C++ value pointers
    PyObject_SetAttrString(py_uart1_tx, "c_value", PyCapsule_New(uart1_tx_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_uart1_rx, "c_value", PyCapsule_New(uart1_rx_wrap, "cxxrtl_value_wrap", NULL));
    
    PyTuple_SetItem(py_args, 0, PyUnicode_FromString("uart_1"));
    PyTuple_SetItem(py_args, 1, py_uart1_tx);
    PyTuple_SetItem(py_args, 2, py_uart1_rx);
    PyObject* py_uart_1 = PyObject_CallObject(py_uart_model_class, py_args);
    PyDict_SetItemString(py_dict, "uart_1", py_uart_1);
    
    // GPIO models
    Py_DECREF(py_args);
    py_args = PyTuple_New(4);
    
    // Create PyValue objects for GPIO0
    PyObject* py_gpio0_o = PyObject_CallObject(py_value8_class, NULL);
    PyObject* py_gpio0_oe = PyObject_CallObject(py_value8_class, NULL);
    PyObject* py_gpio0_i = PyObject_CallObject(py_value8_class, NULL);
    
    // Create wrapper objects
    auto* gpio0_o_wrap = static_cast<cxxrtl::value8_wrap*>(&top.p_gpio__0____gpio____o);
    auto* gpio0_oe_wrap = static_cast<cxxrtl::value8_wrap*>(&top.p_gpio__0____gpio____oe);
    auto* gpio0_i_wrap = static_cast<cxxrtl::value8_wrap*>(&top.p_gpio__0____gpio____i);
    
    // Set the C++ value pointers
    PyObject_SetAttrString(py_gpio0_o, "c_value", PyCapsule_New(gpio0_o_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_gpio0_oe, "c_value", PyCapsule_New(gpio0_oe_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_gpio0_i, "c_value", PyCapsule_New(gpio0_i_wrap, "cxxrtl_value_wrap", NULL));
    
    PyTuple_SetItem(py_args, 0, PyUnicode_FromString("gpio_0"));
    PyTuple_SetItem(py_args, 1, py_gpio0_o);
    PyTuple_SetItem(py_args, 2, py_gpio0_oe);
    PyTuple_SetItem(py_args, 3, py_gpio0_i);
    PyObject* py_gpio_0 = PyObject_CallObject(py_gpio_model_class, py_args);
    PyDict_SetItemString(py_dict, "gpio_0", py_gpio_0);
    
    Py_DECREF(py_args);
    py_args = PyTuple_New(4);
    
    // Create PyValue objects for GPIO1
    PyObject* py_gpio1_o = PyObject_CallObject(py_value8_class, NULL);
    PyObject* py_gpio1_oe = PyObject_CallObject(py_value8_class, NULL);
    PyObject* py_gpio1_i = PyObject_CallObject(py_value8_class, NULL);
    
    // Create wrapper objects
    auto* gpio1_o_wrap = static_cast<cxxrtl::value8_wrap*>(&top.p_gpio__1____gpio____o);
    auto* gpio1_oe_wrap = static_cast<cxxrtl::value8_wrap*>(&top.p_gpio__1____gpio____oe);
    auto* gpio1_i_wrap = static_cast<cxxrtl::value8_wrap*>(&top.p_gpio__1____gpio____i);
    
    // Set the C++ value pointers
    PyObject_SetAttrString(py_gpio1_o, "c_value", PyCapsule_New(gpio1_o_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_gpio1_oe, "c_value", PyCapsule_New(gpio1_oe_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_gpio1_i, "c_value", PyCapsule_New(gpio1_i_wrap, "cxxrtl_value_wrap", NULL));
    
    PyTuple_SetItem(py_args, 0, PyUnicode_FromString("gpio_1"));
    PyTuple_SetItem(py_args, 1, py_gpio1_o);
    PyTuple_SetItem(py_args, 2, py_gpio1_oe);
    PyTuple_SetItem(py_args, 3, py_gpio1_i);
    PyObject* py_gpio_1 = PyObject_CallObject(py_gpio_model_class, py_args);
    PyDict_SetItemString(py_dict, "gpio_1", py_gpio_1);
    
    // SPI models
    Py_DECREF(py_args);
    py_args = PyTuple_New(5);
    
    // Create PyValue objects for SPI0
    PyObject* py_spi0_clk = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_spi0_csn = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_spi0_copi = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_spi0_cipo = PyObject_CallObject(py_value1_class, NULL);
    
    // Create wrapper objects
    auto* spi0_clk_wrap = static_cast<cxxrtl::value1_wrap*>(&top.p_user__spi__0____sck____o);
    auto* spi0_csn_wrap = static_cast<cxxrtl::value1_wrap*>(&top.p_user__spi__0____csn____o);
    auto* spi0_copi_wrap = static_cast<cxxrtl::value1_wrap*>(&top.p_user__spi__0____copi____o);
    auto* spi0_cipo_wrap = static_cast<cxxrtl::value1_wrap*>(&top.p_user__spi__0____cipo____i);
    
    // Set the C++ value pointers
    PyObject_SetAttrString(py_spi0_clk, "c_value", PyCapsule_New(spi0_clk_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_spi0_csn, "c_value", PyCapsule_New(spi0_csn_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_spi0_copi, "c_value", PyCapsule_New(spi0_copi_wrap, "cxxrtl_value_wrap", NULL));
    PyObject_SetAttrString(py_spi0_cipo, "c_value", PyCapsule_New(spi0_cipo_wrap, "cxxrtl_value_wrap", NULL));
    
    PyTuple_SetItem(py_args, 0, PyUnicode_FromString("spi_0"));
    PyTuple_SetItem(py_args, 1, py_spi0_clk);
    PyTuple_SetItem(py_args, 2, py_spi0_csn);
    PyTuple_SetItem(py_args, 3, py_spi0_copi);
    PyTuple_SetItem(py_args, 4, py_spi0_cipo);
    PyObject* py_spi_0 = PyObject_CallObject(py_spi_model_class, py_args);
    PyDict_SetItemString(py_dict, "spi_0", py_spi_0);
    
    Py_DECREF(py_args);
    py_args = PyTuple_New(5);
    
    // Create PyValue objects for SPI1
    PyObject* py_spi1_clk = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_spi1_csn = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_spi1_copi = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_spi1_cipo = PyObject_CallObject(py_value1_class, NULL);
    
    // Set the C++ value pointers
    PyObject_SetAttrString(py_spi1_clk, "c_value", PyCapsule_New(&top.p_user__spi__1____sck____o, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_spi1_csn, "c_value", PyCapsule_New(&top.p_user__spi__1____csn____o, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_spi1_copi, "c_value", PyCapsule_New(&top.p_user__spi__1____copi____o, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_spi1_cipo, "c_value", PyCapsule_New(&top.p_user__spi__1____cipo____i, "cxxrtl_value", NULL));
    
    PyTuple_SetItem(py_args, 0, PyUnicode_FromString("spi_1"));
    PyTuple_SetItem(py_args, 1, py_spi1_clk);
    PyTuple_SetItem(py_args, 2, py_spi1_csn);
    PyTuple_SetItem(py_args, 3, py_spi1_copi);
    PyTuple_SetItem(py_args, 4, py_spi1_cipo);
    PyObject* py_spi_1 = PyObject_CallObject(py_spi_model_class, py_args);
    PyDict_SetItemString(py_dict, "spi_1", py_spi_1);
    
    Py_DECREF(py_args);
    py_args = PyTuple_New(5);
    
    // Create PyValue objects for SPI2
    PyObject* py_spi2_clk = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_spi2_csn = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_spi2_copi = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_spi2_cipo = PyObject_CallObject(py_value1_class, NULL);
    
    // Set the C++ value pointers
    PyObject_SetAttrString(py_spi2_clk, "c_value", PyCapsule_New(&top.p_user__spi__2____sck____o, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_spi2_csn, "c_value", PyCapsule_New(&top.p_user__spi__2____csn____o, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_spi2_copi, "c_value", PyCapsule_New(&top.p_user__spi__2____copi____o, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_spi2_cipo, "c_value", PyCapsule_New(&top.p_user__spi__2____cipo____i, "cxxrtl_value", NULL));
    
    PyTuple_SetItem(py_args, 0, PyUnicode_FromString("spi_2"));
    PyTuple_SetItem(py_args, 1, py_spi2_clk);
    PyTuple_SetItem(py_args, 2, py_spi2_csn);
    PyTuple_SetItem(py_args, 3, py_spi2_copi);
    PyTuple_SetItem(py_args, 4, py_spi2_cipo);
    PyObject* py_spi_2 = PyObject_CallObject(py_spi_model_class, py_args);
    PyDict_SetItemString(py_dict, "spi_2", py_spi_2);
    
    // I2C models
    Py_DECREF(py_args);
    py_args = PyTuple_New(5);
    
    // Create PyValue objects for I2C0
    PyObject* py_i2c0_sda_oe = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_i2c0_sda_i = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_i2c0_scl_oe = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_i2c0_scl_i = PyObject_CallObject(py_value1_class, NULL);
    
    // Set the C++ value pointers
    PyObject_SetAttrString(py_i2c0_sda_oe, "c_value", PyCapsule_New(&top.p_i2c__0____sda____oe, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_i2c0_sda_i, "c_value", PyCapsule_New(&top.p_i2c__0____sda____i, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_i2c0_scl_oe, "c_value", PyCapsule_New(&top.p_i2c__0____scl____oe, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_i2c0_scl_i, "c_value", PyCapsule_New(&top.p_i2c__0____scl____i, "cxxrtl_value", NULL));
    
    PyTuple_SetItem(py_args, 0, PyUnicode_FromString("i2c_0"));
    PyTuple_SetItem(py_args, 1, py_i2c0_sda_oe);
    PyTuple_SetItem(py_args, 2, py_i2c0_sda_i);
    PyTuple_SetItem(py_args, 3, py_i2c0_scl_oe);
    PyTuple_SetItem(py_args, 4, py_i2c0_scl_i);
    PyObject* py_i2c_0 = PyObject_CallObject(py_i2c_model_class, py_args);
    PyDict_SetItemString(py_dict, "i2c_0", py_i2c_0);
    
    Py_DECREF(py_args);
    py_args = PyTuple_New(5);
    
    // Create PyValue objects for I2C1
    PyObject* py_i2c1_sda_oe = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_i2c1_sda_i = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_i2c1_scl_oe = PyObject_CallObject(py_value1_class, NULL);
    PyObject* py_i2c1_scl_i = PyObject_CallObject(py_value1_class, NULL);
    
    // Set the C++ value pointers
    PyObject_SetAttrString(py_i2c1_sda_oe, "c_value", PyCapsule_New(&top.p_i2c__1____sda____oe, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_i2c1_sda_i, "c_value", PyCapsule_New(&top.p_i2c__1____sda____i, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_i2c1_scl_oe, "c_value", PyCapsule_New(&top.p_i2c__1____scl____oe, "cxxrtl_value", NULL));
    PyObject_SetAttrString(py_i2c1_scl_i, "c_value", PyCapsule_New(&top.p_i2c__1____scl____i, "cxxrtl_value", NULL));
    
    PyTuple_SetItem(py_args, 0, PyUnicode_FromString("i2c_1"));
    PyTuple_SetItem(py_args, 1, py_i2c1_sda_oe);
    PyTuple_SetItem(py_args, 2, py_i2c1_sda_i);
    PyTuple_SetItem(py_args, 3, py_i2c1_scl_oe);
    PyTuple_SetItem(py_args, 4, py_i2c1_scl_i);
    PyObject* py_i2c_1 = PyObject_CallObject(py_i2c_model_class, py_args);
    PyDict_SetItemString(py_dict, "i2c_1", py_i2c_1);
    
    Py_DECREF(py_args);
    
    // Also need to decref the PyValue classes
    Py_DECREF(py_value1_class);
    Py_DECREF(py_value4_class);
    Py_DECREF(py_value8_class);
    
    // Create step method for each model
    PyObject* py_step_method = PyUnicode_FromString("step");

    // Set up agent
    cxxrtl::agent agent(cxxrtl::spool("spool.bin"), top);
    if (getenv("DEBUG")) // can also be done when a condition is violated, etc
        std::cerr << "Waiting for debugger on " << agent.start_debugging() << std::endl;

    // Open event log and input commands
    PyObject* py_event_log_args = PyTuple_New(1);
    PyTuple_SetItem(py_event_log_args, 0, PyUnicode_FromString("events.json"));
    PyObject_CallObject(py_open_event_log, py_event_log_args);
    Py_DECREF(py_event_log_args);
    
    PyObject* py_input_cmd_args = PyTuple_New(1);
    PyTuple_SetItem(py_input_cmd_args, 0, PyUnicode_FromString("../../my_design/tests/input.json"));
    PyObject_CallObject(py_open_input_commands, py_input_cmd_args);
    Py_DECREF(py_input_cmd_args);

    // Call load_data on flash
    PyObject* py_load_data_method = PyUnicode_FromString("load_data");
    PyObject* py_load_data_args = PyTuple_New(2);
    PyTuple_SetItem(py_load_data_args, 0, PyUnicode_FromString("../software/software.bin"));
    PyTuple_SetItem(py_load_data_args, 1, PyLong_FromUnsignedLong(0x00100000U));
    PyObject_CallMethodObjArgs(py_flash, py_load_data_method, 
                               PyTuple_GetItem(py_load_data_args, 0),
                               PyTuple_GetItem(py_load_data_args, 1), NULL);
    Py_DECREF(py_load_data_args);
    Py_DECREF(py_load_data_method);

    unsigned timestamp = 0;
    auto tick = [&]() {
        // Call step() on all models with the current timestamp
        PyObject* py_timestamp = PyLong_FromUnsignedLong(timestamp);
        PyObject *key, *value;
        Py_ssize_t pos = 0;

        while (PyDict_Next(py_dict, &pos, &key, &value)) {
            PyObject_CallMethodObjArgs(value, PyUnicode_FromString("step"), py_timestamp, NULL);
        }

        Py_DECREF(py_timestamp);

        top.p_clk.set(false);
        agent.step();
        agent.advance(1_us);
        ++timestamp;

        top.p_clk.set(true);
        agent.step();
        agent.advance(1_us);
        ++timestamp;
    };

    agent.step();
    agent.advance(1_us);

    top.p_rst.set(true);
    tick();

    top.p_rst.set(false);
    for (int i = 0; i < 3000000; i++)
        tick();

    // Close event log
    PyObject_CallObject(py_close_event_log, NULL);
    
    // Clean up Python objects and interpreter
    Py_DECREF(py_step_method);
    Py_DECREF(py_dict);
    Py_Finalize();
    
    return 0;
}
