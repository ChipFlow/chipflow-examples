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

    spiflash_model flash("flash", top.p_io_24_soc__flash__clk_24_o, top.p_io_24_soc__flash__csn_24_o,
        top.p_io_24_soc__flash__d_24_o, top.p_io_24_soc__flash__d_24_oe, top.p_io_24_soc__flash__d_24_i);

    uart_model uart_0("uart_0", top.p_io_24_soc__uart__0__tx_24_o, top.p_io_24_soc__uart__0__rx_24_i);
    uart_model uart_1("uart_1", top.p_io_24_soc__uart__1__tx_24_o, top.p_io_24_soc__uart__1__rx_24_i);

    gpio_model gpio_0("gpio_0", top.p_io_24_soc__gpio__0__gpio_24_o, top.p_io_24_soc__gpio__0__gpio_24_oe, top.p_io_24_soc__gpio__0__gpio_24_i);
    gpio_model gpio_1("gpio_1", top.p_io_24_soc__gpio__1__gpio_24_o, top.p_io_24_soc__gpio__1__gpio_24_oe, top.p_io_24_soc__gpio__1__gpio_24_i);

    spi_model user_spi_0("user_spi_0", top.p_io_24_soc__user__spi__0__sck_24_o, top.p_io_24_soc__user__spi__0__csn_24_o, top.p_io_24_soc__user__spi__0__copi_24_o, top.p_io_24_soc__user__spi__0__cipo_24_i);
    spi_model user_spi_1("user_spi_1", top.p_io_24_soc__user__spi__1__sck_24_o, top.p_io_24_soc__user__spi__1__csn_24_o, top.p_io_24_soc__user__spi__1__copi_24_o, top.p_io_24_soc__user__spi__1__cipo_24_i);
    spi_model user_spi_2("user_spi_2", top.p_io_24_soc__user__spi__2__sck_24_o, top.p_io_24_soc__user__spi__2__csn_24_o, top.p_io_24_soc__user__spi__2__copi_24_o, top.p_io_24_soc__user__spi__2__cipo_24_i);

    i2c_model i2c_0("i2c_0", top.p_io_24_soc__i2c__0__sda_24_oe, top.p_io_24_soc__i2c__0__sda_24_i, top.p_io_24_soc__i2c__0__scl_24_oe, top.p_io_24_soc__i2c__0__scl_24_i);
    i2c_model i2c_1("i2c_1", top.p_io_24_soc__i2c__1__sda_24_oe, top.p_io_24_soc__i2c__1__sda_24_i, top.p_io_24_soc__i2c__1__scl_24_oe, top.p_io_24_soc__i2c__1__scl_24_i);

    cxxrtl::agent agent(cxxrtl::spool("spool.bin"), top);
    if (getenv("DEBUG")) // can also be done when a condition is violated, etc
        std::cerr << "Waiting for debugger on " << agent.start_debugging() << std::endl;

    open_event_log(BUILD_DIR "/sim/events.json");
    open_input_commands(PROJECT_ROOT "/design/tests/input.json");

    unsigned timestamp = 0;
    auto tick = [&]() {
        // agent.print(stringf("timestamp %d\n", timestamp), CXXRTL_LOCATION);

        flash.step(timestamp);
        uart_0.step(timestamp);
        uart_1.step(timestamp);

        gpio_0.step(timestamp);
        gpio_1.step(timestamp);

        user_spi_0.step(timestamp);
        user_spi_1.step(timestamp);
        user_spi_2.step(timestamp);

        i2c_0.step(timestamp);
        i2c_1.step(timestamp);

        top.p_io_24_clk_24_i.set(false);
        agent.step();
        agent.advance(1_us);
        ++timestamp;

        top.p_io_24_clk_24_i.set(true);
        agent.step();
        agent.advance(1_us);
        ++timestamp;

        // if (timestamp == 10)
        //     agent.breakpoint(CXXRTL_LOCATION);
    };

    flash.load_data(BUILD_DIR "/software/software.bin", 0x00100000U);
    agent.step();
    agent.advance(1_us);

    top.p_io_24_rst__n_24_i.set(false);
    tick();

    top.p_io_24_rst__n_24_i.set(true);
    for (int i = 0; i < 3000000; i++)
        tick();

    close_event_log();
    return 0;
}
