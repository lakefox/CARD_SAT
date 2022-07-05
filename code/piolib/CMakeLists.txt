# Set minimum required version of CMake
cmake_minimum_required(VERSION 3.12)
project(uart)

add_executable(pio_uart_tx)
add_executable(pio_uart_rx)
add_executable(uart)

pico_generate_pio_header(pio_uart_tx ${CMAKE_CURRENT_LIST_DIR}/uart_tx.pio)
pico_generate_pio_header(pio_uart_rx ${CMAKE_CURRENT_LIST_DIR}/uart_rx.pio)

target_sources(pio_uart_tx PRIVATE uart_tx.c)
target_sources(pio_uart_rx PRIVATE uart_rx.c)
target_sources(uart PRIVATE uart.c)

target_link_libraries(pio_uart_tx PRIVATE pico_stdlib hardware_pio)
target_link_libraries(pio_uart_rx PRIVATE
    pico_stdlib
    pico_multicore
    hardware_pio
)

pico_add_extra_outputs(pio_uart_tx)
pico_add_extra_outputs(pio_uart_rx)

# Create C header file with the name <pio program>.pio.h
pico_generate_pio_header(${PROJECT_NAME}
    ${CMAKE_CURRENT_LIST_DIR}/uart_tx.pio
)

# Create C header file with the name <pio program>.pio.h
pico_generate_pio_header(${PROJECT_NAME}
    ${CMAKE_CURRENT_LIST_DIR}/uart_rx.pio
)