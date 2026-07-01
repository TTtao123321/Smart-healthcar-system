package com.hospital.hms.config;

import com.hospital.hms.event.HmsDomainEventPublisher;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMqConfig {
    @Bean
    public TopicExchange hmsDomainEventsExchange() {
        return new TopicExchange(HmsDomainEventPublisher.EXCHANGE, true, false);
    }
}
