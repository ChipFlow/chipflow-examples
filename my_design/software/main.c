#include <stdint.h>
#include "generated/soc.h"

typedef unsigned guint;
typedef uint8_t guint8;

#include "umu.h"
#include "nya_a.h"

char uart_getch_block(volatile uart_regs_t *uart) {
    while (!(uart->rx.status & 0x1))
        ;
    return uart->rx.data;
}

static void oled_cmd_mode() {
    GPIO_1->setclr = GPIO_PIN0_CLEAR;
}

static void oled_data_mode() {
    GPIO_1->setclr = GPIO_PIN0_SET;
}

static void oled_pwr_on() {
    oled_cmd_mode();
    spi_xfer(USER_SPI_0, 0xA072, 16, true); // set remap, RGB
    spi_xfer(USER_SPI_0, 0xA100, 16, true); // start line
    spi_xfer(USER_SPI_0, 0xA200, 16, true); // display offset
    spi_xfer(USER_SPI_0, 0xA83F, 16, true); // 1/64 duty
    spi_xfer(USER_SPI_0, 0x8EAD, 16, true); // master
    spi_xfer(USER_SPI_0, 0xB00B, 16, true); // power mode
    spi_xfer(USER_SPI_0, 0xB13B, 16, true); // precharge
    spi_xfer(USER_SPI_0, 0xB3F0, 16, true); // clock divide
    spi_xfer(USER_SPI_0, 0x8A64, 16, true); // precharge a
    spi_xfer(USER_SPI_0, 0x8B78, 16, true); // precharge b
    spi_xfer(USER_SPI_0, 0x8C64, 16, true); // precharge c
    spi_xfer(USER_SPI_0, 0xBB3A, 16, true); // precharge level
    spi_xfer(USER_SPI_0, 0xBE3E, 16, true); // vcomh
    spi_xfer(USER_SPI_0, 0x8706, 16, true); // master current

    spi_xfer(USER_SPI_0, 0xAF, 8, true); // power on


}

static void oled_set_contrast(uint8_t contrast) {
    oled_cmd_mode();
    spi_xfer(USER_SPI_0, (0x81U << 8U) | contrast, 16, true);
}

static void oled_set_column_addr(uint8_t low, uint8_t high) {
    oled_cmd_mode();
    spi_xfer(USER_SPI_0, (0x15U << 16U) | (low << 8U) | high, 24, true);
}

static void oled_set_row_addr(uint8_t low, uint8_t high) {
    oled_cmd_mode();
    spi_xfer(USER_SPI_0, (0x75U << 16U) | (low << 8U) | high, 24, true);
}

static void oled_put_image(const uint8_t *data) {
    oled_set_column_addr(0, 95);
    oled_set_row_addr(0, 63);
    oled_data_mode();
    for (unsigned y = 0; y < 64; y++) {
        for (unsigned x = 0; x < 96; x++) {
            unsigned word = ((63-y)*96 + x) * 2;
            spi_xfer(USER_SPI_0, data[word] | data[word + 1] << 8U, 16, (y != 63) || (x != 95));
        }
    }
}

void main() {

    GPIO_0->mode = GPIO_PIN0_PUSH_PULL | GPIO_PIN1_PUSH_PULL \
                 | GPIO_PIN2_PUSH_PULL | GPIO_PIN3_PUSH_PULL \
                 | GPIO_PIN4_PUSH_PULL | GPIO_PIN5_PUSH_PULL \
                 | GPIO_PIN6_PUSH_PULL | GPIO_PIN7_PUSH_PULL;

    GPIO_0->output = 0x55;

    uart_init(UART_0, 25000000/115200);
    uart_init(UART_1, 25000000/115200);

    puts("🐱: nyaa~!\r\n");

    GPIO_0->output = 0xAA;

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

    GPIO_1->mode = GPIO_PIN0_PUSH_PULL | GPIO_PIN1_PUSH_PULL;
    GPIO_1->output = 0x2; // display out of reset

    spi_init(USER_SPI_0, 1);

    oled_pwr_on();

    while(1) {
        oled_put_image(nya_umu.pixel_data);
        //for (int i = 0; i < 2000000; i++) asm("nop");
        oled_put_image(nya_a.pixel_data);
        //for (int i = 0; i < 2000000; i++) asm("nop");
    }

}
