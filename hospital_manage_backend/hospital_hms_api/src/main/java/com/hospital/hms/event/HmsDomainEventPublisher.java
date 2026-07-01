package com.hospital.hms.event;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

@Component
public class HmsDomainEventPublisher {
    public static final String EXCHANGE = "hms.domain.events";

    private final RabbitTemplate rabbitTemplate;

    public HmsDomainEventPublisher(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
    }

    public void publishAfterCommit(HmsDomainEvent<?> event) {
        if (!TransactionSynchronizationManager.isSynchronizationActive()) {
            rabbitTemplate.convertAndSend(EXCHANGE, event.eventType(), event);
            return;
        }
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                rabbitTemplate.convertAndSend(EXCHANGE, event.eventType(), event);
            }
        });
    }
}
