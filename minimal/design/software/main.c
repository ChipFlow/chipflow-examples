#include <stdint.h>
#include "generated/soc.h"

char uart_getch_block(volatile uart_regs_t *uart) {
    while (!(uart->rx.status & 0x1))
        ;
    return uart->rx.data;
}

void main() {
    uart_init(UART_0, 25000000/115200);

    puts("🐱: nyaa~!\r\n");

    puts("SoC type: ");
    puthex(SOC_ID->type);
    // This would make the golden reference output change every commit
    // puts(" ");
    // puthex(SOC_ID->version);
    puts("\r\n");

    // SPI Flash config
    puts("Flash ID: ");
    puthex(spiflash_read_id(SPIFLASH));
    puts("\n");
    spiflash_set_qspi_flag(SPIFLASH);
    spiflash_set_quad_mode(SPIFLASH);
    puts("Quad mode\n");

    while (1) {
    };
}
