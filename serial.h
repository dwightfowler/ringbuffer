/* serial.h - Cross-Platform Serial Communication Interface */
#ifndef SERIAL_H
#define SERIAL_H

#include <stddef.h>
#include <stdbool.h>

/* Serial Configuration Structure */
typedef struct {
    int baud_rate;     // Baud rate (e.g., 115200)
    int data_bits;     // Data bits (typically 8)
    int stop_bits;     // Stop bits (1 or 2)
    bool parity;       // Parity (true = enabled, false = none)
    bool flow_control; // Flow control (true = enabled, false = none)
} SerialConfig;

/* Abstract Serial Interface */
int serial_open(const char *device, SerialConfig *config);
ssize_t serial_read(int fd, void *buffer, size_t length);
ssize_t serial_write(int fd, const void *buffer, size_t length);
void serial_close(int fd);

#endif /* SERIAL_H */
