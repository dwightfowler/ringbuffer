/* ring_buf_comm.h - Ring Buffer Communication Module */
#ifndef RING_BUF_COMM_H
#define RING_BUF_COMM_H

#include <stddef.h>
#include <stdbool.h>

#define RING_BUF_SIZE 1024   // Default ring buffer size
#define DEFAULT_TERMINATOR "\n"

/* Ring buffer structure */
typedef struct {
    char buffer[RING_BUF_SIZE];
    size_t head;    // Write index
    size_t tail;    // Read index
    bool overflow;  // Overflow flag
} RingBuffer;

/* Communication module structure */
typedef struct {
    RingBuffer rx_buffer;
    RingBuffer tx_buffer;
    char terminator[8]; // Allows multi-character terminators
    size_t rx_callback_threshold; // RX buffer fill threshold for callback
    void (*rx_callback)(void); // Function pointer for callback
} RingBufComm;

/* Initialization function */
void ring_buf_comm_init(RingBufComm *comm);

/* Read function */
bool ring_buf_comm_read(RingBufComm *comm, char *rcvr, size_t rcvr_len,
                        const char *terminator, size_t *read_len, bool *overflow);

/* Write function */
bool ring_buf_comm_write(RingBufComm *comm, const char *data, size_t data_len, size_t *written_len);

/* Set callback function */
void ring_buf_comm_set_callback(RingBufComm *comm, void (*callback)(void));

#endif /* RING_BUF_COMM_H */
