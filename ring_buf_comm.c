/* ring_buf_comm.c - Ring Buffer Communication Module Implementation */
#include "ring_buf_comm.h"
#include <string.h>

void ring_buf_comm_init(RingBufComm *comm) {
    memset(comm, 0, sizeof(RingBufComm));
    strncpy(comm->terminator, DEFAULT_TERMINATOR, sizeof(comm->terminator) - 1);
    comm->rx_callback_threshold = RING_BUF_SIZE; // Default: trigger on full buffer
}

static size_t ring_buf_available(const RingBuffer *rb) {
    return (rb->head >= rb->tail) ? (rb->head - rb->tail) : (RING_BUF_SIZE - (rb->tail - rb->head));
}

bool ring_buf_comm_read(RingBufComm *comm, char *rcvr, size_t rcvr_len,
                        const char *terminator, size_t *read_len, bool *overflow, bool peek) {
    if (!comm || !rcvr || !read_len || !terminator || !overflow) return false;
    
    RingBuffer *rb = &comm->rx_buffer;
    *overflow = rb->overflow;
    *read_len = 0;
    
    size_t term_len = strlen(terminator);
    size_t available = ring_buf_available(rb);
    
    if (available == 0) return false;
    
    bool found_terminator = false;
    size_t i = 0;
    size_t temp_tail = rb->tail;
    
    while (i < rcvr_len && available > 0) {
        rcvr[i] = rb->buffer[temp_tail];
        i++;
        available--;
        temp_tail = (temp_tail + 1) % RING_BUF_SIZE;
        
        if (i >= term_len) {
            bool match = true;
            for (size_t j = 0; j < term_len; j++) {
                if (rcvr[i - term_len + j] != terminator[j]) {
                    match = false;
                    break;
                }
            }
            if (match) {
                found_terminator = true;
                break;
            }
        }
    }
    
    *read_len = i;
    
    if (!peek) {
        rb->tail = temp_tail;
        if (found_terminator) rb->overflow = false;
    }
    
    return found_terminator;
}

bool ring_buf_comm_write(RingBufComm *comm, const char *data, size_t data_len, size_t *written_len) {
    if (!comm || !data || !written_len) return false;
    
    RingBuffer *rb = &comm->tx_buffer;
    *written_len = 0;
    
    for (size_t i = 0; i < data_len; i++) {
        size_t next_head = (rb->head + 1) % RING_BUF_SIZE;
        if (next_head == rb->tail) return false; // Buffer full
        rb->buffer[rb->head] = data[i];
        rb->head = next_head;
        (*written_len)++;
    }
    return true;
}

void ring_buf_comm_set_callback(RingBufComm *comm, void (*callback)(void)) {
    if (comm) comm->rx_callback = callback;
}
