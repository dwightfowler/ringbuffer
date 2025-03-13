/* linux_tty.h - Linux Serial Communication Implementation */
#ifndef LINUX_TTY_H
#define LINUX_TTY_H

#include "serial.h"

/* Linux-specific implementation of serial functions */
int linux_tty_open(const char *device, SerialConfig *config);
ssize_t linux_tty_read(int fd, void *buffer, size_t length);
ssize_t linux_tty_write(int fd, const void *buffer, size_t length);
void linux_tty_close(int fd);

#endif /* LINUX_TTY_H */
