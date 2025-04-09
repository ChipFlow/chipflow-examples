#undef NDEBUG

#include <cxxrtl/cxxrtl.h>
#include <cxxrtl/cxxrtl_server.h>
#include "sim_soc.h"
#include "models.h"

#include <fstream>
#include <filesystem>

using namespace cxxrtl::time_literals;
using namespace cxxrtl_design;

int main(int argc, char **argv) {
    p_sim__top top;

    spiflash_model flash("flash", top.p_flash____clk____o, top.p_flash____csn____o,
        top.p_flash____d____o, top.p_flash____d____oe, top.p_flash____d____i);

    uart_model uart_0("uart_0", top.p_uart__0____tx____o, top.p_uart__0____rx____i);

    gpio_model gpio_0("gpio_0", top.p_gpio__0____gpio____o, top.p_gpio__0____gpio____oe, top.p_gpio__0____gpio____i);

    cxxrtl::agent agent(cxxrtl::spool("spool.bin"), top);
    if (getenv("DEBUG")) // can also be done when a condition is violated, etc
        std::cerr << "Waiting for debugger on " << agent.start_debugging() << std::endl;

    open_event_log("events.json");
    open_input_commands("../../design/tests/input.json");

    unsigned timestamp = 0;
    auto tick = [&]() {
        // agent.print(stringf("timestamp %d\n", timestamp), CXXRTL_LOCATION);

        flash.step(timestamp);
        uart_0.step(timestamp);

        gpio_0.step(timestamp);

        top.p_clk.set(false);
        agent.step();
        agent.advance(1_us);
        ++timestamp;

        top.p_clk.set(true);
        agent.step();
        agent.advance(1_us);
        ++timestamp;

        // if (timestamp == 10)
        //     agent.breakpoint(CXXRTL_LOCATION);
    };

    flash.load_data("../software/software.bin", 0x00100000U);
    agent.step();
    agent.advance(1_us);

    top.p_rst.set(true);
    tick();

    top.p_rst.set(false);
    for (int i = 0; i < 3000000; i++)
        tick();

    close_event_log();
    return 0;
}
