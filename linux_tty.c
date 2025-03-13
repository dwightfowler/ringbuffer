/* linux_tty.c - Linux Serial Communication Implementation */
#include "linux_tty.h"
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <stdio.h>
#include <string.h>

int linux_tty_open(const char *device, SerialConfig *config) {
    int fd = open(device, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd == -1) {
        perror("Error opening serial port");
        return -1;
    }

    struct termios tty;
    if (tcgetattr(fd, &tty) != 0) {
        perror("tcgetattr");
        close(fd);
        return -1;
    }

    // Set baud rate
    cfsetospeed(&tty, config->baud_rate);
    cfsetispeed(&tty, config->baud_rate);

    // Configure data bits, stop bits, and parity
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= (config->data_bits == 7) ? CS7 : CS8;
    tty.c_cflag &= ~(PARENB | PARODD);
    if (config->parity) tty.c_cflag |= PARENB;
    tty.c_cflag &= ~CSTOPB;
    if (config->stop_bits == 2) tty.c_cflag |= CSTOPB;

    // Flow control
    tty.c_cflag &= ~CRTSCTS;
    if (config->flow_control) tty.c_cflag |= CRTSCTS;

    tty.c_cflag |= CREAD | CLOCAL; // Enable receiver
    tty.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG); // Raw mode
    tty.c_oflag &= ~OPOST; // No output processing
    tty.c_iflag &= ~(IXON | IXOFF | IXANY); // No software flow control

    if (tcsetattr(fd, TCSANOW, &tty) != 0) {
        perror("tcsetattr");
        close(fd);
        return -1;
    }

    return fd;
}

ssize_t linux_tty_read(int fd, void *buffer, size_t length) {
    return read(fd, buffer, length);
}

ssize_t linux_tty_write(int fd, const void *buffer, size_t length) {
    return write(fd, buffer, length);
}

void linux_tty_close(int fd) {
    close(fd);
}
