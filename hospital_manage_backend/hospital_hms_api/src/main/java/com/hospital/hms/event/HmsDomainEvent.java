package com.hospital.hms.event;

import java.time.Instant;

public record HmsDomainEvent<T>(
        String eventId,
        String eventType,
        Instant occurredAt,
        String traceId,
        String operatorType,
        Integer operatorId,
        T payload
) {
}
