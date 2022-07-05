/* uart.c */
#include "uart.h"
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "uart_tx.pio.h"
#include <stdio.h>
#include "pico/multicore.h"
#include "hardware/uart.h"
#include "uart_rx.pio.h"

// We're going to use PIO to print "Hello, world!" on the same GPIO which we
// normally attach UART0 to.
uint PIN_TX;
uint PIN_RX;
// This is the same as the default UART baud rate on Pico
uint SERIAL_BAUD;

PIO pio; // pio0 || 1
uint sm;

int init(uint pinTx, uint pinRx, uint serialBaud, PIO pIO, uint sM)
{
    PIN_TX = pinTx;
    PIN_RX = pinRx;
    SERIAL_BAUD = serialBaud;
    pio = pIO;
    sm = sM;
}

int uartTX(char msg)
{
    uint offset = pio_add_program(pio, &uart_tx_program);
    uart_tx_program_init(pio, sm, offset, PIN_TX, SERIAL_BAUD);
    uart_tx_program_puts(pio, sm, msg);
    return 0;
}

int uartRX()
{
    // Set up the state machine we're going to use to receive them.
    PIO pio = pio0;
    uint sm = 0;
    uint offset = pio_add_program(pio, &uart_rx_program);
    uart_rx_program_init(pio, sm, offset, PIN_RX, SERIAL_BAUD);

    // Echo characters received from PIO to the console
    while (true)
    {
        char c = uart_rx_program_getc(pio, sm);
        putchar(c);
    }
}