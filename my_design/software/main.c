#include <stdint.h>

#include "generated/soc.h"

void main() {
	puts("🐱: nyaa~!\r\n");

	puts("Flash ID: ");
	puthex(spiflash_read_id(SPIFLASH));
	puts("\r\n");

	puts("Entering QSPI mode\r\n");
	spiflash_set_qspi_flag(SPIFLASH);
	spiflash_set_quad_mode(SPIFLASH);

	puts("Initialised!\r\n");

	puts("SoC type: ");
	puthex(SOC_ID->type);
	// This would make the golden reference output change every commit
	// puts(" ");
	// puthex(SOC_ID->version);
	puts("\r\n");

	GPIO_1->oe = 0xF0;
	GPIO_1->out = 0x50;
	GPIO_1->out = 0xA0;
	GPIO_1->oe = 0x00;

	uart_puts(UART_1, "ABCD");

	while (1) {
		// // Listen for button presses
		// next_buttons = BTN_GPIO->in;
		// if ((next_buttons & 1U) && !(last_buttons & 1U))
		// 	puts("button 1 pressed!\n");
		// if ((next_buttons & 2U) && !(last_buttons & 2U))
		// 	puts("button 2 pressed!\n");
		// last_buttons = next_buttons;
	};
}
