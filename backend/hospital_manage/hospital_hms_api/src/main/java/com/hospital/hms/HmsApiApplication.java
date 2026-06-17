package com.hospital.hms;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.hospital.hms.dao")
public class HmsApiApplication {
    public static void main(String[] args) {
        SpringApplication.run(HmsApiApplication.class, args);
    }
}