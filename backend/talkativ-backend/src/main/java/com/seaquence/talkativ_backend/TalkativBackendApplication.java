package com.seaquence.talkativ_backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import com.seaquence.talkativ_backend.security.JwtProperties;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@EnableConfigurationProperties(JwtProperties.class)
@ConfigurationPropertiesScan
public class TalkativBackendApplication {
    public static void main(String[] args) {
        SpringApplication.run(TalkativBackendApplication.class, args);
    }
}

