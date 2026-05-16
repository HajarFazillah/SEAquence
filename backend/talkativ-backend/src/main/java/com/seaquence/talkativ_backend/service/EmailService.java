package com.seaquence.talkativ_backend.service;

import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

@Service
public class EmailService {

    private final JavaMailSender mailSender;

    public EmailService(JavaMailSender mailSender) {
        this.mailSender = mailSender;
    }

    public void sendPasswordResetCode(String toEmail, String code) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setTo(toEmail);
        message.setSubject("[Talkativ] 비밀번호 재설정 코드");
        message.setText(
            "안녕하세요, Talkativ입니다.\n\n" +
            "비밀번호 재설정 코드: " + code + "\n\n" +
            "이 코드는 15분간 유효합니다.\n" +
            "본인이 요청하지 않았다면 이 이메일을 무시하세요.\n\n" +
            "- Talkativ 팀"
        );
        mailSender.send(message);
    }
}
