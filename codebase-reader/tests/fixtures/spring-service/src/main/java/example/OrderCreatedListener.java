package example;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionalEventListener;

@Component
public class OrderCreatedListener {
    @TransactionalEventListener
    public void afterCommit(OrderCreated event) {
        System.out.println(event.orderId());
    }

    @KafkaListener(topics = "order-retries")
    public void retry(String orderId) {
        System.out.println(orderId);
    }
}
