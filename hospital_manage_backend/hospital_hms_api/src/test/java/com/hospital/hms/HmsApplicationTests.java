package com.hospital.hms;

import com.hospital.hms.dao.MedicalRegistrationDao;
import com.hospital.hms.event.HmsDomainEvent;
import com.hospital.hms.event.RegistrationEventPayload;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.core.Message;
import org.springframework.amqp.core.MessageProperties;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.time.Instant;

@SpringBootTest
class HmsApplicationTests {

    @Autowired
    private RabbitTemplate rabbitTemplate;

    @Autowired
    private MedicalRegistrationDao medicalRegistrationDao;

    @Test
    void contextLoads() {
    }

    @Test
    void rabbitTemplateShouldUseJsonMessageConverter() {
        Assertions.assertTrue(
                rabbitTemplate.getMessageConverter() instanceof Jackson2JsonMessageConverter
        );
    }

    @Test
    void selectScheduleForUpdateShouldReturnActiveWorkPlanStatus() {
        Assertions.assertEquals(
                "ACTIVE",
                medicalRegistrationDao.selectScheduleForUpdate(1020).get("workPlanStatus")
        );
    }

    @Test
    void rabbitTemplateMessageConverterShouldSerializeDomainEventWithInstant() {
        HmsDomainEvent<RegistrationEventPayload> event = new HmsDomainEvent<>(
                "event-1",
                "registration.created",
                Instant.parse("2026-07-01T09:00:00Z"),
                "trace-1",
                "system",
                null,
                new RegistrationEventPayload(1, 9, 240, 1020, 3, 9, "2026-07-01", 1)
        );

        Message message = rabbitTemplate.getMessageConverter().toMessage(event, new MessageProperties());

        Assertions.assertEquals("application/json", message.getMessageProperties().getContentType());
        Assertions.assertTrue(new String(message.getBody(), StandardCharsets.UTF_8).contains("registration.created"));
    }

    @Test
    @Transactional
    void updateRegistrationStatusShouldBindNamedParameters() {
        Assertions.assertEquals(1, medicalRegistrationDao.updateRegistrationStatus(45, -1));
        Assertions.assertEquals(-1, medicalRegistrationDao.selectRegistrationById(45).get("status"));
    }

}
